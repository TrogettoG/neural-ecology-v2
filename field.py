"""
field.py — Campo Cognitivo.

No es un broker de mensajes. Es un ecosistema informacional.
Las neuronas no se hablan directamente. Interactúan a través del campo.
"""

import math
import random
from typing import Optional

from models import (
    Action, Cluster, NeuronDecision, Signal, SignalType,
    Tendency, Tension, Trace,
)
from memory import Memory
from config import (
    DECAY_RATE, SIGNAL_DEATH_THRESHOLD,
    CLUSTER_NOVELTY_MIN, CLUSTER_MERGE_SIMILARITY, MAX_CLUSTERS,
    MAX_TENSIONS, TENSION_MAX_CYCLES,
    DENSIFY_PERSIST_MIN,
    R_WEIGHT_SIGNALS, R_WEIGHT_NEURONS,
    CLOSE_ENERGY_THRESHOLD, CLOSE_NOVELTY_THRESHOLD,
    CLOSE_NOVELTY_CYCLES, CLOSE_NO_DENSIFY_CYCLES,
    CLOSE_SOFT_MIN_CONDITIONS, CLOSE_SOFT_MIN_CYCLES,
    MAX_CYCLES, ENERGY_EPISODE,
    max_deep,
)


class CognitiveField:
    """
    El campo contiene todo lo relevante del episodio.
    Las neuronas reaccionan a él, no entre sí directamente.
    """

    def __init__(self, perturbation: str):
        self.perturbation = perturbation

        # Estado central
        self.signals: dict[str, Signal] = {}
        self.clusters: dict[str, Cluster] = {}
        self.tensions: list[Tension] = []
        self.energy = ENERGY_EPISODE
        self.cycle = 0

        # Memoria
        self.memory = Memory()

        # Neuronas (gestionadas por el orquestador pero el campo las ve)
        self._active_neurons: list = []      # referencia inyectada por orquestador
        self._dead_neurons: list = []

        # Historial de novedad global (para cierre)
        self._novelty_history: list[float] = []
        self._last_densify_cycle: int = 0
        self._soft_close_streak: int = 0

        # Log de eventos del episodio
        self.event_log: list[str] = []

        # Cluster inicial desde la perturbación
        self._init_perturbation()

    def _init_perturbation(self):
        """
        Siembra el campo con 3 señales iniciales de distintos ángulos.
        TTL alto para que las neuronas tengan tiempo de elaborar.
        """
        root_cluster = Cluster(
            label=self.perturbation[:50],
            born_at_cycle=0,
        )
        self.clusters[root_cluster.id] = root_cluster

        seed_signals = [
            Signal(
                type=SignalType.EXPLORATORIA,
                intensity=0.90,
                origin_id="field",
                cluster_id=root_cluster.id,
                novelty=0.90,
                contradiction=0.0,
                payload=f"pregunta: {self.perturbation[:80]}",
                ttl=20,
            ),
            Signal(
                type=SignalType.CONFLICTIVA,
                intensity=0.70,
                origin_id="field",
                cluster_id=root_cluster.id,
                novelty=0.60,
                contradiction=0.65,
                payload=f"tensión implícita en: {self.perturbation[:60]}",
                ttl=20,
            ),
            Signal(
                type=SignalType.ASOCIATIVA,
                intensity=0.60,
                origin_id="field",
                cluster_id=root_cluster.id,
                novelty=0.70,
                contradiction=0.20,
                payload=f"analogías posibles con: {self.perturbation[:60]}",
                ttl=20,
            ),
        ]

        for sig in seed_signals:
            self.signals[sig.id] = sig
            root_cluster.signal_ids.append(sig.id)

        self.log(f"[FIELD] Perturbación inicial: {self.perturbation[:60]}")

    # ── PASO 1: Decaimiento de señales ────────────────────────────

    def decay_signals(self):
        """
        Aplica decaimiento exponencial a señales no reforzadas.
        Elimina las que caen bajo el umbral.
        """
        to_remove = []
        for sid, signal in self.signals.items():
            signal.intensity *= math.exp(-DECAY_RATE)
            signal.novelty   *= math.exp(-0.08)   # novedad decae más lento que intensidad
            signal.persistence += 1
            if not signal.is_alive():
                to_remove.append(sid)

        for sid in to_remove:
            sig = self.signals.pop(sid)
            if sig.cluster_id and sig.cluster_id in self.clusters:
                cluster = self.clusters[sig.cluster_id]
                if sid in cluster.signal_ids:
                    cluster.signal_ids.remove(sid)
            self.log(f"[SIGNAL] {sid} murió (intensidad agotada)")

    # ── PASO 2: Actualización de clusters ─────────────────────────

    def update_clusters(self):
        """
        Recalcula métricas de cada cluster basado en sus señales activas.
        """
        for cluster in self.clusters.values():
            active_signals = [
                self.signals[sid] for sid in cluster.signal_ids
                if sid in self.signals
            ]
            if not active_signals:
                continue

            cluster.persistence += 1

            # Actualizar métricas
            prev_c = cluster.contradiction
            prev_i = cluster.total_intensity(self.signals)

            cluster.contradiction = min(1.0, sum(
                s.contradiction for s in active_signals
            ) / len(active_signals))

            cluster.novelty = sum(
                s.novelty for s in active_signals
            ) / len(active_signals)

            new_i = cluster.total_intensity(self.signals)
            delta_i = abs(new_i - prev_i) / max(new_i, 0.01)
            delta_c = abs(cluster.contradiction - prev_c)

            # Variación semántica (proxy: cambio en cantidad de señales)
            variation = abs(len(active_signals) - len(cluster.signal_ids)) / max(len(cluster.signal_ids), 1)

            cluster.history_variation.append(variation)
            cluster.history_novelty.append(cluster.novelty)
            cluster.history_delta_c.append(delta_c)
            cluster.history_delta_i.append(delta_i)
            cluster.intensity_prev = new_i

            # Actualizar ciclos estables
            if cluster.is_stable():
                cluster.stable_cycles += 1
            else:
                cluster.stable_cycles = 0

        # Eliminar clusters vacíos y viejos
        empty = [
            cid for cid, c in self.clusters.items()
            if not any(sid in self.signals for sid in c.signal_ids)
            and c.persistence > 3
        ]
        for cid in empty:
            del self.clusters[cid]

    # ── PASO 2b: Selección competitiva ───────────────────────────────

    def competitive_selection(self):
        """
        El campo aprende a decidir qué regiones merecen sobrevivir.

        Cuatro mecanismos orgánicos (no poda arbitraria):

        A. Absorción: cluster fuerte en tensión persistente con débil
           absorbe señales del débil.
        B. Costo de fragmentación: cuantos más clusters, más caro
           sostener los débiles (energía global).
        C. Decaimiento diferencial: clusters periféricos decaen más
           rápido que clusters centrales.
        D. Ventaja por centralidad: vitalidad favorece a quien tiene
           más tensiones estructurales activas.
        """
        if len(self.clusters) < 3:
            return   # sin competencia con menos de 3 clusters

        # ── Score de vitalidad por cluster ────────────────────────
        # Combina C, R, intensidad activa y centralidad en tensiones
        tension_count = {}  # cluster_id → nº de tensiones estructurales
        for t in self.tensions:
            if t.intensity >= 0.35:
                tension_count[t.cluster_a] = tension_count.get(t.cluster_a, 0) + 1
                tension_count[t.cluster_b] = tension_count.get(t.cluster_b, 0) + 1

        vitality = {}
        for cid, cluster in self.clusters.items():
            intensity = cluster.total_intensity(self.signals)
            centrality = tension_count.get(cid, 0) / max(len(self.tensions), 1)
            vitality[cid] = (
                0.35 * cluster.contradiction +
                0.25 * cluster.resonance +
                0.20 * min(1.0, intensity / 3.0) +
                0.20 * centrality
            )

        if not vitality:
            return

        sorted_clusters = sorted(vitality.items(), key=lambda x: x[1], reverse=True)
        max_vitality    = sorted_clusters[0][1]

        # ── A. Absorción competitiva ──────────────────────────────
        # Para cada tensión estructural persistente: el más vital
        # absorbe 1 señal débil del más débil
        for tension in self.tensions:
            if tension.intensity < 0.35 or tension.cycles_active < 4:
                continue
            va = vitality.get(tension.cluster_a, 0)
            vb = vitality.get(tension.cluster_b, 0)
            if abs(va - vb) < 0.15:
                continue   # demasiado parejos, no absorber
            strong_id = tension.cluster_a if va > vb else tension.cluster_b
            weak_id   = tension.cluster_b if va > vb else tension.cluster_a
            strong    = self.clusters.get(strong_id)
            weak      = self.clusters.get(weak_id)
            if not strong or not weak:
                continue
            # Encontrar señal más débil del cluster débil
            weak_sigs = sorted(
                [self.signals[sid] for sid in weak.signal_ids if sid in self.signals],
                key=lambda s: s.intensity
            )
            if weak_sigs:
                migrant = weak_sigs[0]
                if migrant.intensity < 0.30:   # solo señales débiles migran
                    weak.signal_ids.remove(migrant.id)
                    strong.signal_ids.append(migrant.id)
                    migrant.cluster_id = strong_id
                    self.log(
                        f"[ABSORB] '{weak.label[:20]}' → '{strong.label[:20]}' "
                        f"(Δv={abs(va-vb):.2f})"
                    )

        # ── B. Costo de fragmentación ─────────────────────────────
        # Cada cluster por encima de 6 tiene costo extra de energía
        FRAGMENT_THRESHOLD = 6
        excess = max(0, len(self.clusters) - FRAGMENT_THRESHOLD)
        if excess > 0:
            # Los clusters más débiles pagan el costo extra
            weakest = sorted_clusters[-excess:]
            fragment_cost = excess * 0.10
            self.energy -= fragment_cost

        # ── C. Decaimiento diferencial ────────────────────────────
        # Clusters periféricos (vitalidad < 30% del máximo) decaen
        if max_vitality > 0:
            for cid, v in vitality.items():
                if v < max_vitality * 0.30:
                    cluster = self.clusters[cid]
                    # Reducir intensidad de sus señales más débiles
                    weak_sigs = [
                        self.signals[sid] for sid in cluster.signal_ids
                        if sid in self.signals and self.signals[sid].intensity < 0.25
                    ]
                    for sig in weak_sigs[:2]:
                        sig.intensity *= 0.80
                    if weak_sigs:
                        self.log(
                            f"[DECAY] '{cluster.label[:25]}' periférico "
                            f"(v={v:.2f} < {max_vitality*0.30:.2f})"
                        )

        # ── D. Ventaja por centralidad ────────────────────────────
        # Clusters centrales (vitalidad > 70% del máximo) refuerzan
        # sus señales más intensas
        if max_vitality > 0:
            for cid, v in vitality.items():
                if v > max_vitality * 0.70:
                    cluster = self.clusters[cid]
                    top_sigs = sorted(
                        [self.signals[sid] for sid in cluster.signal_ids
                         if sid in self.signals],
                        key=lambda s: s.intensity,
                        reverse=True
                    )[:2]
                    for sig in top_sigs:
                        sig.intensity = min(1.0, sig.intensity * 1.05)

    # ── PASO 3: Detección de tensiones ────────────────────────────

    def detect_tensions(self):
        """
        Detecta contradicciones entre clusters activos.
        Actualiza tensiones existentes y crea nuevas.
        """
        cluster_list = [
            c for c in self.clusters.values()
            if c.contradiction > 0.20
        ]

        # Actualizar tensiones: envejecen e intensidad decae si no son reforzadas
        active_cluster_ids = set(self.clusters.keys())
        for tension in self.tensions:
            tension.cycles_active += 1
            # Si alguno de los dos clusters ya no existe, decae rápido
            if tension.cluster_a not in active_cluster_ids or tension.cluster_b not in active_cluster_ids:
                tension.intensity *= 0.5
            else:
                # Decaimiento suave por ciclo si no crece
                tension.intensity *= 0.92

        # Detectar nuevas
        for i, ca in enumerate(cluster_list):
            for cb in cluster_list[i+1:]:
                # ¿Ya existe tensión entre estos dos?
                already = any(
                    (t.cluster_a == ca.id and t.cluster_b == cb.id) or
                    (t.cluster_a == cb.id and t.cluster_b == ca.id)
                    for t in self.tensions
                )
                if not already and ca.contradiction + cb.contradiction > 0.45:
                    tension = Tension(
                        cluster_a=ca.id,
                        cluster_b=cb.id,
                        description=f"{ca.label[:25]} vs {cb.label[:25]}",
                        intensity=(ca.contradiction + cb.contradiction) / 2,
                    )
                    self.tensions.append(tension)
                    self.log(f"[TENSION] Nueva: {tension.description}")

        # Separar tensiones estructurales (intensity >= 0.35) de residuales
        # Las residuales expiran más rápido
        self.tensions = [
            t for t in self.tensions
            if t.intensity >= 0.10  # umbral mínimo de existencia
        ]
        structural = [t for t in self.tensions if t.intensity >= 0.35]
        residual   = [t for t in self.tensions if t.intensity < 0.35]
        # Residuales expiran en la mitad de ciclos
        residual = [t for t in residual if t.cycles_active < TENSION_MAX_CYCLES // 2]
        structural = [t for t in structural if t.cycles_active < TENSION_MAX_CYCLES]
        # Cap total
        self.tensions = (structural + residual)[:MAX_TENSIONS]
        self._structural_tensions = len(structural)  # para should_close

    # ── PASO 4: Cálculo de resonancia ─────────────────────────────

    def calculate_resonance(self):
        """
        R para cada cluster: señales que llegaron desde OTROS clusters.

        Fórmula corregida:
          R = cross_signals / total_signals_in_cluster
              + consolidated_boost

        cross_signal = señal cuyo source_cluster_id != este cluster
        (neurona de otro cluster actuó y su señal aterrizó acá)
        """
        for cluster in self.clusters.values():
            cluster_signal_count = len([
                sid for sid in cluster.signal_ids if sid in self.signals
            ])
            if cluster_signal_count == 0:
                cluster.resonance = 0.0
                continue

            cross = sum(
                1 for sid in cluster.signal_ids
                if sid in self.signals
                and self.signals[sid].source_cluster_id is not None
                and self.signals[sid].source_cluster_id != cluster.id
            )

            r = cross / cluster_signal_count

            # Boost desde memoria consolidada
            r = min(1.0, r + self.memory.consolidated.resonance_boost(cluster.label))

            cluster.resonance = r

    # ── PASO 5: Densificación ─────────────────────────────────────

    def check_densification(self) -> list[tuple]:
        """
        Retorna lista de (cluster_id, cluster_label) que requieren
        spawn de neurona profunda.
        """
        current_deep = sum(
            1 for n in self._active_neurons if n.depth_type == "profunda"
        )
        max_allowed = max_deep(self.energy)

        candidates = []
        for cluster in self.clusters.values():
            if cluster.should_densify() and current_deep < max_allowed:
                candidates.append((cluster.id, cluster.label))
                cluster.densified_count += 1
                self._last_densify_cycle = self.cycle
                self.log(
                    f"[DENSIFY] Cluster '{cluster.label[:30]}' "
                    f"score={cluster.densify_score():.2f} "
                    f"C={cluster.contradiction:.2f} R={cluster.resonance:.2f}"
                )
                current_deep += 1

        return candidates

    # ── Recepción de señales emitidas por neuronas ────────────────

    def _find_similar_cluster(self, payload: str) -> str | None:
        """Busca un cluster existente suficientemente similar al payload."""
        if not payload:
            return None
        words_new = set(payload.lower().split())
        best_id, best_score = None, 0.0
        for cid, cluster in self.clusters.items():
            words_c = set(cluster.label.lower().split())
            if not words_c:
                continue
            overlap = len(words_new & words_c) / max(len(words_new | words_c), 1)
            if overlap > best_score:
                best_score = overlap
                best_id = cid
        return best_id if best_score >= CLUSTER_MERGE_SIMILARITY else None

    def receive_signals(self, new_signals: list[Signal]):
        """Integra las señales emitidas en el tick al campo."""
        for sig in new_signals:
            self.signals[sig.id] = sig

            # Asignar a cluster o crear uno nuevo
            if sig.cluster_id and sig.cluster_id in self.clusters:
                cluster = self.clusters[sig.cluster_id]
                if sig.id not in cluster.signal_ids:
                    cluster.signal_ids.append(sig.id)
            else:
                # Señal sin cluster: buscar cluster similar antes de crear uno nuevo
                matched = self._find_similar_cluster(sig.payload)
                if matched:
                    self.clusters[matched].signal_ids.append(sig.id)
                    sig.cluster_id = matched
                elif sig.novelty > CLUSTER_NOVELTY_MIN and len(self.clusters) < MAX_CLUSTERS:
                    new_cluster = Cluster(
                        label=sig.payload[:40] or f"cluster_{sig.id}",
                        signal_ids=[sig.id],
                        born_at_cycle=self.cycle,
                    )
                    self.clusters[new_cluster.id] = new_cluster
                    sig.cluster_id = new_cluster.id
                    self.log(f"[CLUSTER] Nuevo: '{new_cluster.label[:30]}'")
                else:
                    # Sin cluster válido: va al cluster raíz
                    root = list(self.clusters.values())[0]
                    root.signal_ids.append(sig.id)
                    sig.cluster_id = root.id

    def reinforce_signal(self, signal_id: str, boost: float = 0.15):
        """Una neurona refuerza una señal: sube intensidad, evita decaimiento."""
        if signal_id in self.signals:
            sig = self.signals[signal_id]
            sig.intensity = min(1.0, sig.intensity + boost - 0.05)

    def inhibit_signal(self, signal_id: str, reduction: float = 0.30):
        """Una neurona inhibe una señal."""
        if signal_id in self.signals:
            self.signals[signal_id].intensity = max(
                0.0,
                self.signals[signal_id].intensity - reduction
            )

    # ── Paso 12: Costo global ─────────────────────────────────────

    def apply_global_cost(self):
        """Descuenta energía global por mantenimiento del campo."""
        from config import COST_MAINTENANCE_NORMAL, COST_MAINTENANCE_DEEP
        for n in self._active_neurons:
            cost = COST_MAINTENANCE_DEEP if n.depth_type == "profunda" else COST_MAINTENANCE_NORMAL
            self.energy -= cost
        self.energy = max(0.0, self.energy)

    # ── Paso 13: Condición de cierre ──────────────────────────────

    def should_close(self) -> tuple[bool, str]:
        """
        Retorna (cerrar, motivo).
        Condiciones duras cierran inmediato.
        Condiciones suaves requieren 2/3 por 2 ciclos.
        """
        # Condiciones duras
        if self.energy < CLOSE_ENERGY_THRESHOLD:
            return True, "agotamiento metabólico"

        if not self.signals:
            return True, "sin señales activas"

        if self.cycle >= MAX_CYCLES:
            return True, "límite de ciclos alcanzado"

        # Condición dura emergente: campo sin pensamiento en curso
        # 0 neuronas activas + sin tensiones creciendo + campo maduro
        if (self.cycle >= 10 and
                len(self._active_neurons) == 0 and
                not self.signals and
                getattr(self, '_dead_field_cycles', 0) >= 2):
            return True, "campo sin actividad — pensamiento completado"
        if len(self._active_neurons) == 0 and not self.signals:
            self._dead_field_cycles = getattr(self, '_dead_field_cycles', 0) + 1
        else:
            self._dead_field_cycles = 0

        # Condiciones suaves
        novelty_avg = (
            sum(self._novelty_history[-CLOSE_NOVELTY_CYCLES:]) /
            CLOSE_NOVELTY_CYCLES
            if len(self._novelty_history) >= CLOSE_NOVELTY_CYCLES
            else 1.0
        )

        if self.clusters:
            stable_count = sum(1 for cl in self.clusters.values() if cl.is_stable())
            all_stable = stable_count >= max(1, len(self.clusters) * 0.60)
        else:
            all_stable = False
        no_recent_densify = (
            self.cycle >= 12 and
            self._last_densify_cycle > 0 and  # hubo al menos una densificación
            (self.cycle - self._last_densify_cycle) >= CLOSE_NO_DENSIFY_CYCLES
        )
        low_novelty = novelty_avg < CLOSE_NOVELTY_THRESHOLD

        # 4ta condición: solo tensiones ESTRUCTURALES activas cuentan
        # tensiones residuales (intensity < 0.35) no bloquean el cierre
        structural_count = getattr(self, '_structural_tensions', len(self.tensions))
        tensions_resolving = (
            self.cycle >= 12 and
            structural_count <= 2
        )

        soft_count = sum([low_novelty, all_stable, no_recent_densify, tensions_resolving])
        if soft_count >= CLOSE_SOFT_MIN_CONDITIONS:
            self._soft_close_streak += 1
        else:
            self._soft_close_streak = 0

        if self._soft_close_streak >= CLOSE_SOFT_MIN_CYCLES:
            reason = " + ".join(filter(None, [
                "baja novedad" if low_novelty else "",
                "clusters estables" if all_stable else "",
                "sin densificación reciente" if no_recent_densify else "",
                "tensiones resueltas" if tensions_resolving else "",
            ]))
            return True, reason

        return False, ""

    # ── Utilidades ────────────────────────────────────────────────

    def tendency_concentration(self, tendency: Tendency) -> float:
        """Fracción de neuronas activas con esta tendencia."""
        total = len(self._active_neurons)
        if total == 0:
            return 0.0
        count = sum(1 for n in self._active_neurons if n.tendency == tendency)
        return count / total

    def top_signals(self, cluster_id: str, k: int = 3) -> list[Signal]:
        """Las señales más intensas de un cluster."""
        cluster = self.clusters.get(cluster_id)
        if not cluster:
            return []
        sigs = [
            self.signals[sid] for sid in cluster.signal_ids
            if sid in self.signals and self.signals[sid].is_alive()
        ]
        return sorted(sigs, key=lambda s: s.intensity, reverse=True)[:k]

    def global_novelty(self) -> float:
        """Novedad promedio del campo en este ciclo."""
        if not self.signals:
            return 0.0
        return sum(s.novelty for s in self.signals.values()) / len(self.signals)

    def update_novelty_history(self):
        self._novelty_history.append(self.global_novelty())

    def get_stats(self) -> dict:
        return {
            "cycle": self.cycle,
            "energy": self.energy,
            "signals": len(self.signals),
            "clusters": len(self.clusters),
            "tensions": len(self.tensions),
            "active_neurons": len(self._active_neurons),
            "dead_neurons": len(self._dead_neurons),
            "novelty": round(self.global_novelty(), 3),
        }

    def log(self, msg: str):
        self.event_log.append(f"[{self.cycle:03d}] {msg}")
        # Mantener solo los últimos 200 eventos
        if len(self.event_log) > 200:
            self.event_log = self.event_log[-200:]

    async def close(self) -> str:
        """Cierra el episodio: transfiere memoria, genera síntesis."""
        await self.memory.close_episode(self.clusters, self.signals, self.cycle)

        # Síntesis final: recopilar payloads de señales consolidadas
        consolidated_signals = sorted(
            self.signals.values(),
            key=lambda s: s.intensity,
            reverse=True
        )[:10]

        cluster_summaries = []
        for cluster in sorted(self.clusters.values(), key=lambda c: c.contradiction, reverse=True)[:5]:
            sigs = self.top_signals(cluster.id, k=3)
            if sigs:
                payloads = " | ".join(s.payload for s in sigs if s.payload)
                cluster_summaries.append(
                    f"• [{cluster.label[:30]}] "
                    f"(C={cluster.contradiction:.2f} R={cluster.resonance:.2f}): {payloads[:120]}"
                )

        tensions_summary = []
        for t in sorted(self.tensions, key=lambda t: t.intensity, reverse=True)[:3]:
            tensions_summary.append(f"• {t.description} (intensidad={t.intensity:.2f})")

        parts = [f"TEMA: {self.perturbation}\n"]

        if cluster_summaries:
            parts.append("CLUSTERS DOMINANTES:")
            parts.extend(cluster_summaries)

        if tensions_summary:
            parts.append("\nTENSIONES ACTIVAS:")
            parts.extend(tensions_summary)

        stats = self.get_stats()
        parts.append(
            f"\nESTADÍSTICAS: {stats['cycle']} ciclos | "
            f"energía restante={stats['energy']:.1f} | "
            f"{stats['active_neurons']} neuronas activas | "
            f"{stats['dead_neurons']} muertas"
        )

        return "\n".join(parts)