"""
orchestrator.py — El tick loop de 14 pasos.

No dirige. Coordina el orden de ejecución.
La inteligencia no está aquí: está en el campo y en la red de neuronas.
"""

import asyncio
import random
from typing import Optional

from models import Action, NeuronDecision, Signal, Tendency
from neuron import Neuron
from field import CognitiveField
from config import (
    COST_SPAWN_NORMAL, COST_SPAWN_DEEP,
    ENERGY_NORMAL, ENERGY_DEEP,
    max_deep,
)


class Orchestrator:
    """
    Ejecuta el ciclo de 14 pasos definido en la spec.
    Mantiene las referencias a neuronas para inyectarlas al campo.
    """

    def __init__(self, field: CognitiveField):
        self.field = field
        self.active_neurons: list[Neuron] = []
        self.dead_neurons: list[Neuron] = []

        # Inyectar referencias al campo
        self.field._active_neurons = self.active_neurons
        self.field._dead_neurons = self.dead_neurons

        # Señales emitidas en el tick actual (se aplican al campo al final del paso 8)
        self._tick_signals: list[Signal] = []

        # Resultado final
        self.final_result: Optional[str] = None
        self.close_reason: Optional[str] = None

    # ── Spawn de neuronas ─────────────────────────────────────────

    def spawn(
        self,
        tendency: Tendency,
        cluster_id: str,
        cluster_label: str,
        depth_type: str = "normal",
        parent_id: Optional[str] = None,
    ) -> Optional[Neuron]:
        """Crea una neurona si hay energía suficiente."""
        cost = COST_SPAWN_DEEP if depth_type == "profunda" else COST_SPAWN_NORMAL
        if self.field.energy < cost:
            return None

        # Límite de neuronas profundas
        if depth_type == "profunda":
            current_deep = sum(1 for n in self.active_neurons if n.depth_type == "profunda")
            if current_deep >= max_deep(self.field.energy):
                return None

        neuron = Neuron(
            tendency=tendency,
            cluster_id=cluster_id,
            cluster_label=cluster_label,
            depth_type=depth_type,
            parent_id=parent_id,
        )
        self.active_neurons.append(neuron)
        self.field.log(
            f"[BORN] {neuron.id} {tendency.value} "
            f"{'[PROFUNDA]' if depth_type == 'profunda' else ''} "
            f"→ '{cluster_label[:30]}'"
        )
        return neuron

    def _kill(self, neuron: Neuron):
        neuron.die()
        if neuron in self.active_neurons:
            self.active_neurons.remove(neuron)
        self.dead_neurons.append(neuron)
        self.field.log(
            f"[DEAD] {neuron.id} {neuron.tendency.value} "
            f"vida={neuron.lifetime:.1f}s age={neuron.age}"
        )

    # ── Tick loop principal ───────────────────────────────────────

    async def tick(self):
        """
        14 pasos en orden estricto.
        Invariante: ninguna neurona ve el resultado de otras en el mismo tick.
        """
        self.field.cycle += 1
        self._tick_signals = []

        # ── Fase de campo (pasos 1-5) ──────────────────────────────

        # Paso 1: Decaimiento de señales
        self.field.decay_signals()

        # Paso 2: Actualización de clusters
        self.field.update_clusters()

        # Paso 3: Detección de tensiones
        self.field.detect_tensions()

        # Paso 4: Cálculo de resonancia
        self.field.calculate_resonance()

        # Auto-respawn: mantener población mínima de 4 neuronas
        # distribuidas entre los clusters más activos
        if len(self.active_neurons) < 4 and self.field.clusters:
            clusters_sorted = sorted(
                self.field.clusters.values(),
                key=lambda cl: cl.contradiction + cl.novelty,
                reverse=True
            )
            tendencies = [
                Tendency.EXPLORADORA, Tendency.CONTRADECIR if hasattr(Tendency, 'CONTRADECIR') else Tendency.CORRECTIVA,
                Tendency.ASOCIATIVA, Tendency.INHIBIDORA,
            ]
            for i, tendency in enumerate(tendencies[:max(0, 4 - len(self.active_neurons))]):
                cluster = clusters_sorted[i % len(clusters_sorted)]
                self.spawn(tendency, cluster.id, cluster.label)

        # Paso 5: Densificación → spawn de neuronas profundas
        densify_candidates = self.field.check_densification()
        for cluster_id, cluster_label in densify_candidates:
            tendency = random.choice([
                Tendency.SINTETIZADORA,
                Tendency.CORRECTIVA,
                Tendency.ASOCIATIVA,
            ])
            self.spawn(tendency, cluster_id, cluster_label, depth_type="profunda")

        # ── Fase de neuronas (pasos 6-11) ─────────────────────────

        # Paso 6: Cada neurona evalúa su estado local
        # (implícito: la neurona tiene acceso al campo en decide())

        # Paso 7: Decisiones (en paralelo, todas ven el mismo campo)
        if self.active_neurons:
            decisions = await asyncio.gather(*[
                n.decide(self.field) for n in self.active_neurons
            ], return_exceptions=True)
        else:
            decisions = []

        # Paso 8: Ejecución de acciones (todas simultáneas, señales acumuladas)
        tendency_dist = self._tendency_distribution()
        neurons_to_process = list(self.active_neurons)  # snapshot

        spawns_requested: list[tuple[Tendency, str, str, str, bool]] = []

        for neuron, decision in zip(neurons_to_process, decisions):
            if isinstance(decision, Exception):
                continue
            if not isinstance(decision, NeuronDecision):
                continue

            sig = neuron.execute(decision, self.field)
            if sig:
                self._tick_signals.append(sig)

            # Registrar spawns pedidos (se ejecutan después)
            if decision.action == Action.SPAWNEAR and decision.spawn_tendency:
                spawns_requested.append((
                    decision.spawn_tendency,
                    neuron.cluster_id,
                    neuron.cluster_label,
                    neuron.id,
                    decision.spawn_deep,
                ))

        # Aplicar señales al campo simultáneamente
        self.field.receive_signals(self._tick_signals)

        # Ejecutar spawns pedidos por neuronas
        for (tend, cid, clabel, parent_id, is_deep) in spawns_requested:
            depth = "profunda" if is_deep else "normal"
            self.spawn(tend, cid, clabel, depth_type=depth, parent_id=parent_id)

        # Paso 9: Refuerzo de señales
        for sig in self._tick_signals:
            if sig.intensity > 0.6:
                self.field.reinforce_signal(sig.id, boost=0.10)

        # Paso 10: Plasticidad local
        for neuron in self.active_neurons:
            neuron.apply_plasticity(tendency_dist)

        # Paso 11: Verificación de muerte
        to_kill = []
        for neuron in list(self.active_neurons):
            cluster_max_signal = 0.0
            cluster = self.field.clusters.get(neuron.cluster_id)
            if cluster:
                sigs = self.field.top_signals(neuron.cluster_id, k=1)
                cluster_max_signal = sigs[0].intensity if sigs else 0.0

            if neuron.should_die(cluster_max_signal):
                to_kill.append(neuron)

        for neuron in to_kill:
            self._kill(neuron)

        # ── Fase de campo cierre de ciclo (pasos 12-14) ───────────

        # Paso 12: Mantenimiento — neurona envejece y descuenta energía propia
        for neuron in list(self.active_neurons):
            neuron.apply_maintenance()

        # Paso 12b: Costo global del campo
        self.field.apply_global_cost()

        # Paso 13: Verificar cierre
        should_close, reason = self.field.should_close()

        # Paso 14: Log del ciclo
        self.field.update_novelty_history()
        stats = self.field.get_stats()
        self.field.log(
            f"[TICK] e={stats['energy']:.1f} "
            f"sig={stats['signals']} cl={stats['clusters']} "
            f"n_act={stats['active_neurons']} n_dead={stats['dead_neurons']} "
            f"nov={stats['novelty']:.2f}"
        )

        return should_close, reason

    # ── Episodio completo ─────────────────────────────────────────

    async def run_episode(self, on_tick=None) -> str:
        """
        Corre el episodio completo.
        on_tick: callback opcional llamado después de cada tick.
        """
        # Setup de memoria
        await self.field.memory.setup()

        # Spawn de neuronas iniciales desde la perturbación
        root_cluster = list(self.field.clusters.values())[0]
        initial_tendencies = [
            Tendency.EXPLORADORA,
            Tendency.EXPLORADORA,
            Tendency.ASOCIATIVA,
            Tendency.CORRECTIVA,
            Tendency.SINTETIZADORA,
        ]
        for tendency in initial_tendencies:
            self.spawn(
                tendency=tendency,
                cluster_id=root_cluster.id,
                cluster_label=root_cluster.label,
                depth_type="normal",
            )

        # Tick loop
        while True:
            should_close, reason = await self.tick()

            if on_tick:
                await on_tick(self.field, self)

            if should_close:
                self.close_reason = reason
                self.field.log(f"[CLOSE] Motivo: {reason}")
                break

        # Cierre
        self.final_result = await self.field.close()
        return self.final_result

    # ── Utilidades ────────────────────────────────────────────────

    def _tendency_distribution(self) -> dict:
        """Distribución actual de tendencias entre neuronas activas."""
        total = len(self.active_neurons)
        if total == 0:
            return {}
        dist = {}
        for n in self.active_neurons:
            dist[n.tendency] = dist.get(n.tendency, 0) + 1
        return {t: c / total for t, c in dist.items()}

    def get_stats(self) -> dict:
        return {
            **self.field.get_stats(),
            "total_neurons": len(self.active_neurons) + len(self.dead_neurons),
            "close_reason": self.close_reason,
        }