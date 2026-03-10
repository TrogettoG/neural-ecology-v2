"""
config.py — Todos los parámetros de la V2.
Fijos al arrancar. Observar 10-20 corridas antes de ajustar.
"""

# ── Energía del episodio ───────────────────────────────────────────
ENERGY_EPISODE = 100.0

# ── Energía por tipo de neurona ───────────────────────────────────
ENERGY_NORMAL = 1.0
ENERGY_DEEP   = 3.5

# ── Costos de spawn ───────────────────────────────────────────────
COST_SPAWN_NORMAL = 0.60
COST_SPAWN_DEEP   = 2.00

# ── Costos de mantenimiento por ciclo ─────────────────────────────
COST_MAINTENANCE_NORMAL = 0.50
COST_MAINTENANCE_DEEP   = 1.00

# ── Costos de acciones ────────────────────────────────────────────
ACTION_COSTS = {
    "AMPLIFICAR":  0.15,
    "ASOCIAR":     0.25,
    "CONTRADECIR": 0.20,
    "CONSOLIDAR":  0.30,
    "INHIBIR":     0.20,
    "TRANSFERIR":  0.10,
    "REACTIVAR":   0.35,
    "CALLAR":      0.02,
    "MORIR":       0.00,
}

# ── Costo de acceso a memoria ─────────────────────────────────────
COST_MEMORY_RECENT      = 0.05
COST_MEMORY_CONSOLIDATED = 0.20

# ── Densificación ─────────────────────────────────────────────────
DENSIFY_C_MIN       = 0.50
DENSIFY_P_MIN       = 0.55
DENSIFY_R_MIN       = 0.35
DENSIFY_SCORE_MIN   = 0.55
DENSIFY_PERSIST_MIN = 3        # ciclos mínimos activo

DENSIFY_W_C = 0.40
DENSIFY_W_P = 0.30
DENSIFY_W_R = 0.20
DENSIFY_W_N = 0.10

# ── Límite de neuronas profundas ──────────────────────────────────
MAX_DEEP_CLAMP_MIN = 1
MAX_DEEP_CLAMP_MAX = 8
MAX_DEEP_DIVISOR   = 12.0

def max_deep(energy_total: float) -> int:
    raw = int(energy_total / MAX_DEEP_DIVISOR)
    return max(MAX_DEEP_CLAMP_MIN, min(raw, MAX_DEEP_CLAMP_MAX))

# ── Muerte por inanición ──────────────────────────────────────────
DEATH_ENERGY_NORMAL   = 0.15
DEATH_INACTION_NORMAL = 2      # ciclos sin acción
DEATH_SIGNAL_NORMAL   = 0.30   # señal mínima en cluster

DEATH_ENERGY_DEEP     = 0.25
DEATH_INACTION_DEEP   = 3
DEATH_SIGNAL_DEEP     = 0.25

# ── Estabilización de clusters ────────────────────────────────────
STABLE_VARIATION  = 0.20
STABLE_NOVELTY    = 0.25
STABLE_DELTA_C    = 0.10
STABLE_DELTA_I    = 0.15
STABLE_CYCLES     = 3

# ── Decaimiento de señales ────────────────────────────────────────
DECAY_RATE              = 0.15
SIGNAL_DEATH_THRESHOLD  = 0.05

# ── Memoria ───────────────────────────────────────────────────────
MEMORY_RECENT_WINDOW         = 10    # ciclos
MEMORY_CONSOLIDATED_DECAY    = 0.80  # por episodio sin refuerzo
MEMORY_TRANSFER_MIN_CYCLES   = 5
MEMORY_TRANSFER_NOVELTY_MIN  = 0.30
MEMORY_TRANSFER_SIMILARITY_MAX = 0.80

# ── Resonancia ────────────────────────────────────────────────────
R_WEIGHT_SIGNALS      = 0.60
R_WEIGHT_NEURONS      = 0.40
R_CONSOLIDATED_BOOST  = 0.15

# ── Cierre del episodio ───────────────────────────────────────────
CLOSE_ENERGY_THRESHOLD    = 0.10
CLOSE_NOVELTY_THRESHOLD   = 0.40
CLOSE_NOVELTY_CYCLES      = 3
CLOSE_NO_DENSIFY_CYCLES   = 3
CLOSE_SOFT_MIN_CONDITIONS = 2    # de 3 condiciones suaves
CLOSE_SOFT_MIN_CYCLES     = 1    # ciclos consecutivos
MAX_CYCLES                = 30

# ── Plasticidad ───────────────────────────────────────────────────
PLASTICITY_PROB        = 0.10
DIVERSITY_THRESHOLD    = 0.60
DIVERSITY_COST_MULT    = 1.50

# ── Neuronas ──────────────────────────────────────────────────────
NEURON_LIFE_NORMAL_MIN = 6
NEURON_LIFE_NORMAL_MAX = 12
NEURON_LIFE_DEEP_MIN   = 5
NEURON_LIFE_DEEP_MAX   = 8

# ── LLM ───────────────────────────────────────────────────────────
GEMINI_MODEL = "gemini-2.5-flash-lite"
LLM_MAX_TOKENS = 300    # neuronas normales: prompts cortos

# ── Control de clusters ───────────────────────────────────────────
CLUSTER_NOVELTY_MIN    = 0.45   # umbral mínimo para crear cluster nuevo
CLUSTER_MERGE_SIMILARITY = 0.70 # similitud para fusionar dos clusters
MAX_CLUSTERS           = 12     # techo de clusters simultáneos

# ── Control de tensiones ──────────────────────────────────────────
MAX_TENSIONS           = 15     # techo global
TENSION_MAX_CYCLES     = 8      # ciclos antes de expirar