"""
neuron.py — Neurona efímera de la V2.

No es un agente con misión. Es una unidad mínima con tendencia.
Responde localmente a tensiones en el campo.
"""

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, TYPE_CHECKING

from google import genai

from models import Action, NeuronDecision, Signal, SignalType, Tendency
from config import (
    ACTION_COSTS,
    COST_MAINTENANCE_NORMAL, COST_MAINTENANCE_DEEP,
    COST_MEMORY_RECENT, COST_MEMORY_CONSOLIDATED,
    DEATH_ENERGY_NORMAL, DEATH_INACTION_NORMAL, DEATH_SIGNAL_NORMAL,
    DEATH_ENERGY_DEEP, DEATH_INACTION_DEEP, DEATH_SIGNAL_DEEP,
    ENERGY_NORMAL, ENERGY_DEEP,
    NEURON_LIFE_NORMAL_MIN, NEURON_LIFE_NORMAL_MAX,
    NEURON_LIFE_DEEP_MIN, NEURON_LIFE_DEEP_MAX,
    PLASTICITY_PROB, DIVERSITY_THRESHOLD, DIVERSITY_COST_MULT,
    GEMINI_MODEL,
)

if TYPE_CHECKING:
    from field import CognitiveField


class NeuronState(str, Enum):
    IDLE      = "idle"
    DECIDING  = "deciding"
    ACTING    = "acting"
    DYING     = "dying"
    DEAD      = "dead"


# Mapa de tendencia → acciones preferidas (sesgo, no obligación)
TENDENCY_ACTIONS = {
    Tendency.EXPLORADORA:   [Action.AMPLIFICAR, Action.SPAWNEAR, Action.TRANSFERIR],
    Tendency.ASOCIATIVA:    [Action.ASOCIAR, Action.TRANSFERIR, Action.AMPLIFICAR],
    Tendency.INHIBIDORA:    [Action.INHIBIR, Action.CALLAR, Action.MORIR],
    Tendency.CORRECTIVA:    [Action.CONTRADECIR, Action.CONSOLIDAR, Action.INHIBIR],
    Tendency.CONSOLIDANTE:  [Action.CONSOLIDAR, Action.AMPLIFICAR, Action.CALLAR],
    Tendency.REACTIVADORA:  [Action.REACTIVAR, Action.ASOCIAR, Action.AMPLIFICAR],
    Tendency.SINTETIZADORA: [Action.CONSOLIDAR, Action.ASOCIAR, Action.CALLAR],
    Tendency.DISOLUTIVA:    [Action.INHIBIR, Action.MORIR, Action.CALLAR],
}

# Qué tipos de señal emite cada tendencia
TENDENCY_SIGNAL_TYPES = {
    Tendency.EXPLORADORA:   SignalType.EXPLORATORIA,
    Tendency.ASOCIATIVA:    SignalType.ASOCIATIVA,
    Tendency.INHIBIDORA:    SignalType.INHIBITORIA,
    Tendency.CORRECTIVA:    SignalType.CORRECTIVA,
    Tendency.CONSOLIDANTE:  SignalType.CONSOLIDANTE,
    Tendency.REACTIVADORA:  SignalType.REACTIVADORA,
    Tendency.SINTETIZADORA: SignalType.CONSOLIDANTE,
    Tendency.DISOLUTIVA:    SignalType.INHIBITORIA,
}


class Neuron:
    def __init__(
        self,
        tendency: Tendency,
        cluster_id: str,
        cluster_label: str,
        depth_type: str = "normal",
        parent_id: Optional[str] = None,
    ):
        self.id = str(uuid.uuid4())[:6]
        self.tendency = tendency
        self.cluster_id = cluster_id
        self.cluster_label = cluster_label
        self.depth_type = depth_type
        self.parent_id = parent_id

        self.energy = ENERGY_DEEP if depth_type == "profunda" else ENERGY_NORMAL
        self.life_max = (
            random.randint(NEURON_LIFE_DEEP_MIN, NEURON_LIFE_DEEP_MAX)
            if depth_type == "profunda"
            else random.randint(NEURON_LIFE_NORMAL_MIN, NEURON_LIFE_NORMAL_MAX)
        )

        self.age = 0
        self.excitation = 0.5
        self.inhibition = 0.0
        self.state = NeuronState.IDLE
        self.signal_trace: list[str] = []  # últimas 3 señales tocadas
        self.last_action: Optional[Action] = None
        self.cycles_without_action = 0
        self.born_at = time.time()
        self.died_at: Optional[float] = None

        self._client = genai.Client()
        self._pending_decision: Optional[NeuronDecision] = None

    # ── Decisión ──────────────────────────────────────────────────

    async def decide(self, field: "CognitiveField") -> NeuronDecision:
        """
        Paso 7 del tick: la neurona decide su acción.
        Prompt mínimo: tendencia + top señales del cluster + energía + estado.
        """
        self.state = NeuronState.DECIDING

        # Construir contexto mínimo
        cluster = field.clusters.get(self.cluster_id)
        cluster_signals = []
        if cluster:
            for sid in cluster.signal_ids[:3]:
                s = field.signals.get(sid)
                if s and s.is_alive():
                    cluster_signals.append(
                        f"{s.type.value}(i={s.intensity:.2f}): {s.payload[:60]}"
                    )

        # Memoria reciente (opcional, costo 0.05)
        mem_summary = ""
        if self.depth_type == "profunda" or self.tendency == Tendency.REACTIVADORA:
            mem_summary = field.memory.recent.summary(top_k=2)
            self.energy -= COST_MEMORY_RECENT

        # Acciones preferidas por tendencia
        preferred = [a.value for a in TENDENCY_ACTIONS.get(self.tendency, [])]

        prompt = f"""Eres una neurona cognitiva. Tu tendencia es: {self.tendency.value}
Energía: {self.energy:.2f} | Edad: {self.age}/{self.life_max} ciclos
Cluster actual: "{self.cluster_label}"
Señales activas ({len(cluster_signals)}): {' | '.join(cluster_signals) if cluster_signals else 'ninguna señal aún'}
Memoria: {mem_summary if mem_summary else 'vacía'}
Acciones preferidas para tu tendencia: {', '.join(preferred)}

REGLA: CALLAR y MORIR son siempre la última opción. Si hay señales activas, debés actuar sobre ellas.
Tu trabajo es elaborar la tensión conceptual del cluster, no esperar.

Responde SOLO con JSON válido, sin texto extra, sin markdown:
{{
  "action": "AMPLIFICAR|ASOCIAR|CONTRADECIR|CONSOLIDAR|INHIBIR|SPAWNEAR|TRANSFERIR|REACTIVAR|CALLAR|MORIR",
  "payload": "qué estás aportando al campo conceptualmente, max 70 chars",
  "spawn_tendency": "exploradora|asociativa|inhibidora|correctiva|consolidante|reactivadora|sintetizadora|disolutiva (solo si action=SPAWNEAR)",
  "spawn_deep": false
}}"""

        try:
            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=GEMINI_MODEL,
                contents=prompt,
            )
            text = response.text.strip()
            # Limpiar markdown si viene con backticks
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            action = Action(data.get("action", "CALLAR"))
            spawn_tendency = None
            if action == Action.SPAWNEAR and data.get("spawn_tendency"):
                try:
                    spawn_tendency = Tendency(data["spawn_tendency"])
                except ValueError:
                    spawn_tendency = Tendency.EXPLORADORA

            decision = NeuronDecision(
                action=action,
                payload=str(data.get("payload", ""))[:80],
                spawn_tendency=spawn_tendency,
                spawn_deep=bool(data.get("spawn_deep", False)),
                target_cluster=self.cluster_id,
            )
        except Exception:
            # Fallback: acción por defecto según tendencia
            preferred_actions = TENDENCY_ACTIONS.get(self.tendency, [Action.CALLAR])
            decision = NeuronDecision(
                action=preferred_actions[0] if preferred_actions else Action.CALLAR,
                payload=f"{self.tendency.value} en {self.cluster_label[:30]}",
                target_cluster=self.cluster_id,
            )

        self._pending_decision = decision
        return decision

    # ── Ejecución ─────────────────────────────────────────────────

    def execute(self, decision: NeuronDecision, field: "CognitiveField") -> Optional[Signal]:
        """
        Paso 8: ejecuta la decisión y emite señal al campo si corresponde.
        Descuenta energía. Actualiza estado interno.
        """
        self.state = NeuronState.ACTING
        self.last_action = decision.action

        cost = ACTION_COSTS.get(decision.action.value, 0.10)

        # Penalización por diversidad si la tendencia está muy concentrada
        if field.tendency_concentration(self.tendency) > DIVERSITY_THRESHOLD:
            cost *= DIVERSITY_COST_MULT

        self.energy -= cost

        if decision.action == Action.MORIR:
            self.state = NeuronState.DYING
            return None

        if decision.action == Action.CALLAR:
            self.cycles_without_action += 1
            return None

        self.cycles_without_action = 0

        # Emitir señal al campo
        signal_type = TENDENCY_SIGNAL_TYPES.get(self.tendency, SignalType.EXPLORATORIA)
        intensity = max(0.3, min(1.0, self.excitation * 0.8))

        novelty = (
            0.85 if decision.action in [Action.ASOCIAR, Action.REACTIVAR] else
            0.55 if decision.action == Action.AMPLIFICAR else 0.35
        )
        contradiction = (
            0.90 if decision.action == Action.CONTRADECIR else
            0.75 if decision.action == Action.INHIBIR else
            0.40 if decision.action == Action.ASOCIAR else 0.10
        )

        # Exploradoras y asociativas pueden crear clusters nuevos
        # dejando cluster_id=None — el campo decide
        emits_to_new_cluster = (
            decision.action in [Action.ASOCIAR, Action.AMPLIFICAR,
                                 Action.CONTRADECIR, Action.REACTIVAR]
            and novelty > 0.35
            and self.age > 1
        )
        sig = Signal(
            type=signal_type,
            intensity=intensity,
            origin_id=self.id,
            cluster_id=None if emits_to_new_cluster else self.cluster_id,
            source_cluster_id=self.cluster_id,   # rastrea origen para R
            novelty=novelty,
            contradiction=contradiction,
            payload=decision.payload,
            ttl=6 if self.depth_type == "profunda" else 4,
        )

        # Registrar en traza local
        self.signal_trace.append(sig.id)
        if len(self.signal_trace) > 3:
            self.signal_trace.pop(0)

        return sig

    # ── Mantenimiento y muerte ─────────────────────────────────────

    def apply_maintenance(self):
        """Paso 12 (parcial): descuenta energía de mantenimiento por ciclo."""
        cost = COST_MAINTENANCE_DEEP if self.depth_type == "profunda" else COST_MAINTENANCE_NORMAL
        self.energy -= cost
        self.age += 1

    def apply_plasticity(self, tendency_distribution: dict):
        """Paso 10: ajusta tendencia con probabilidad PLASTICITY_PROB."""
        if random.random() > PLASTICITY_PROB:
            return
        # Si la tendencia dominante está saturada, deriva a una menos poblada
        dominant = max(tendency_distribution, key=tendency_distribution.get, default=None)
        if dominant == self.tendency and tendency_distribution.get(self.tendency, 0) > DIVERSITY_THRESHOLD:
            alternatives = [t for t in Tendency if t != self.tendency]
            if alternatives:
                self.tendency = random.choice(alternatives)

    def should_die(self, cluster_max_signal: float) -> bool:
        """Paso 11: evalúa condiciones de muerte por inanición."""
        if self.state == NeuronState.DYING:
            return True
        if self.energy <= 0.0 or self.age >= self.life_max:
            return True

        if self.depth_type == "profunda":
            return (self.energy < DEATH_ENERGY_DEEP and
                    self.cycles_without_action >= DEATH_INACTION_DEEP and
                    cluster_max_signal <= DEATH_SIGNAL_DEEP)
        else:
            return (self.energy < DEATH_ENERGY_NORMAL and
                    self.cycles_without_action >= DEATH_INACTION_NORMAL and
                    cluster_max_signal <= DEATH_SIGNAL_NORMAL)

    def die(self):
        self.state = NeuronState.DEAD
        self.died_at = time.time()

    @property
    def lifetime(self) -> float:
        end = self.died_at or time.time()
        return end - self.born_at

    def __repr__(self):
        return (f"Neuron({self.id} {self.tendency.value} "
                f"e={self.energy:.2f} age={self.age} {self.state.value})")