"""
models.py — Estructuras de datos del sistema.
Pequeñas, inmutables donde sea posible, sin lógica.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import time
import uuid


def short_id() -> str:
    return str(uuid.uuid4())[:6]


# ── Tipos de señal ────────────────────────────────────────────────

class SignalType(str, Enum):
    EXPLORATORIA  = "exploratoria"
    ASOCIATIVA    = "asociativa"
    CONFLICTIVA   = "conflictiva"
    CORRECTIVA    = "correctiva"
    CONSOLIDANTE  = "consolidante"
    INHIBITORIA   = "inhibitoria"
    REACTIVADORA  = "reactivadora"
    TERMINAL      = "terminal"


# ── Tendencias de neurona ─────────────────────────────────────────

class Tendency(str, Enum):
    EXPLORADORA   = "exploradora"
    ASOCIATIVA    = "asociativa"
    INHIBIDORA    = "inhibidora"
    CORRECTIVA    = "correctiva"
    CONSOLIDANTE  = "consolidante"
    REACTIVADORA  = "reactivadora"
    SINTETIZADORA = "sintetizadora"
    DISOLUTIVA    = "disolutiva"


# ── Acciones posibles ─────────────────────────────────────────────

class Action(str, Enum):
    AMPLIFICAR  = "AMPLIFICAR"
    ASOCIAR     = "ASOCIAR"
    CONTRADECIR = "CONTRADECIR"
    CONSOLIDAR  = "CONSOLIDAR"
    INHIBIR     = "INHIBIR"
    SPAWNEAR    = "SPAWNEAR"
    TRANSFERIR  = "TRANSFERIR"
    REACTIVAR   = "REACTIVAR"
    CALLAR      = "CALLAR"
    MORIR       = "MORIR"


# ── Señal ─────────────────────────────────────────────────────────

@dataclass
class Signal:
    id: str = field(default_factory=short_id)
    type: SignalType = SignalType.EXPLORATORIA
    intensity: float = 0.5
    origin_id: str = "field"
    cluster_id: Optional[str] = None
    source_cluster_id: Optional[str] = None  # cluster del emisor al momento de emitir
    novelty: float = 0.5
    contradiction: float = 0.0
    resonance: float = 0.0       # calculada por el campo
    persistence: int = 0          # ciclos activa
    ttl: int = 8
    payload: str = ""             # texto corto, max 100 chars
    born_at: float = field(default_factory=time.time)

    def is_alive(self) -> bool:
        return self.intensity >= 0.05 and self.persistence < self.ttl


# ── Cluster ───────────────────────────────────────────────────────

@dataclass
class Cluster:
    id: str = field(default_factory=short_id)
    label: str = ""
    signal_ids: list = field(default_factory=list)
    neuron_ids: list = field(default_factory=list)       # neuronas activas en este cluster
    external_neuron_visits: int = 0                       # visitas desde otros clusters
    external_signal_refs: int = 0                         # señales compartidas con otros clusters

    # Métricas para densificación
    contradiction: float = 0.0   # C
    persistence: int = 0          # P en ciclos
    resonance: float = 0.0        # R calculada
    novelty: float = 0.5          # N

    # Para estabilización
    history_variation: list = field(default_factory=list)    # últimas variaciones
    history_novelty: list = field(default_factory=list)
    history_delta_c: list = field(default_factory=list)
    history_delta_i: list = field(default_factory=list)
    intensity_prev: float = 0.0

    # Control
    densified_count: int = 0      # veces que se densificó
    stable_cycles: int = 0        # ciclos consecutivos estable
    born_at_cycle: int = 0

    def total_intensity(self, signals: dict) -> float:
        return sum(signals[sid].intensity for sid in self.signal_ids if sid in signals)

    def densify_score(self) -> float:
        from config import DENSIFY_W_C, DENSIFY_W_P, DENSIFY_W_R, DENSIFY_W_N
        p_norm = min(1.0, self.persistence / 10.0)
        return (DENSIFY_W_C * self.contradiction +
                DENSIFY_W_P * p_norm +
                DENSIFY_W_R * self.resonance +
                DENSIFY_W_N * self.novelty)

    def should_densify(self) -> bool:
        from config import (DENSIFY_C_MIN, DENSIFY_P_MIN, DENSIFY_R_MIN,
                            DENSIFY_SCORE_MIN, DENSIFY_PERSIST_MIN)
        return (self.contradiction >= DENSIFY_C_MIN and
                self.persistence >= DENSIFY_PERSIST_MIN and
                self.resonance >= DENSIFY_R_MIN and
                self.densify_score() >= DENSIFY_SCORE_MIN)

    def is_stable(self) -> bool:
        from config import (STABLE_VARIATION, STABLE_NOVELTY,
                            STABLE_DELTA_C, STABLE_DELTA_I, STABLE_CYCLES)
        if len(self.history_variation) < STABLE_CYCLES:
            return False
        recent_v = self.history_variation[-STABLE_CYCLES:]
        recent_n = self.history_novelty[-STABLE_CYCLES:]
        recent_c = self.history_delta_c[-STABLE_CYCLES:]
        recent_i = self.history_delta_i[-STABLE_CYCLES:]
        return (all(v < STABLE_VARIATION for v in recent_v) and
                all(n < STABLE_NOVELTY for n in recent_n) and
                all(c <= STABLE_DELTA_C for c in recent_c) and
                all(i <= STABLE_DELTA_I for i in recent_i))


# ── Traza de memoria ──────────────────────────────────────────────

@dataclass
class Trace:
    cluster_label: str
    signal_payloads: list        # textos de señales del cluster
    contradiction: float
    novelty: float
    cycle: int
    weight: float = 1.0          # decae con el tiempo


# ── Tensión ───────────────────────────────────────────────────────

@dataclass
class Tension:
    id: str = field(default_factory=short_id)
    cluster_a: str = ""
    cluster_b: str = ""
    description: str = ""
    intensity: float = 0.5
    cycles_active: int = 0


# ── Decisión de neurona ───────────────────────────────────────────

@dataclass
class NeuronDecision:
    action: Action
    target_cluster: Optional[str] = None
    target_signal_id: Optional[str] = None
    payload: str = ""
    spawn_tendency: Optional[Tendency] = None
    spawn_deep: bool = False