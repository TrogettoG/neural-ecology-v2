# Neural Ecology V2 — Changelog

> *The system does not answer questions. It stabilizes around conceptual configurations.*

**Current status:** 31 runs evaluated · 5 migrations confirmed · 2 mechanisms identified

---

## Design Principle #1

> **Explore cheap. Inhibit often. Densify rarely. Depth is a scarce resource.**

This principle governs every architectural decision: signals decay fast, neurons pay energy to exist, deep clusters require high thresholds. Most ideas die. Only genuine tensions survive long enough to synthesize.

---

## Dataset Summary

```
Total runs evaluated: 31
─────────────────────────────────────────────────────
Migration      5   (16%)   C52, C74, R75, R81, R84
Elaboration    9   (29%)   C55, C57, C59, C63–C65, C69–C71, R82, R83, R86
Paraphrase    17   (55%)   remainder
─────────────────────────────────────────────────────
Key finding: semantic migration occurs via 2 distinct mechanisms.
Memory accumulation suppresses tension and eliminates migration entirely.
```

---

## Engineering Changes

### Phase 5 — Distance Evaluator (`distance_evaluator.py`)

External LLM-as-judge module. Given a run's perturbation, synthesis chain, and final cluster, returns:

| Field | Type | Description |
|---|---|---|
| `score` | float 0.0–1.0 | Conceptual distance traveled |
| `category` | str | `paraphrase` / `elaboration` / `migration` |
| `trajectory` | str | `stable` / `deepening` / `drift` / `jump` |
| `pivot_cycle` | int \| null | Cycle where domain shift occurred |
| `justification` | str | One-sentence explanation |

**Key design principle:** destination determines score; trajectory determines fine category.

**Taxonomy:**
- Paraphrase (0.00–0.25): final cluster restates the perturbation
- Elaboration (0.26–0.55): same domain, synthesis chain shows progressive deepening
- Migration (0.56–1.00): genuinely different domain — a reader seeing only perturbation + final cluster would not recognize the connection

Calibrated over 3 prompt iterations on 21 runs. Stable scores across 4 independent batches.

---

### Phase 7 — Controlled experiment infrastructure

**`memory.py`** — added `clear_redis()` method to the `Memory` class. Clears the `neurona_v2:*` Redis namespace and resets local state. Called before each run to guarantee independent episodes.

**`main.py`** — rewritten with:
- `--perturbation` (0–5): select perturbation from the bank
- `--runs` (N): run N consecutive episodes
- `--no-clear-redis`: preserve accumulated memory (for control runs)
- Per-run JSON logging to `runs/run_NNN.json` with full `synthesis_chain` and `synthesis_count`

**JSON structure per run:**
```json
{
  "run_id": 81,
  "timestamp": "2026-03-13 17:57:02",
  "experiment": {
    "perturbation_idx": 1,
    "perturbation": "...",
    "max_cycles": 45,
    "redis_cleared": true
  },
  "cycles": 45,
  "energy": 32.0,
  "synthesis_count": 3,
  "synthesis_chain": [
    {"cycle": 32, "label": "[S] Fluidez Consciente vs. Esencia Adaptativa"},
    {"cycle": 38, "label": "[S] Fluidez: Proceso y Consecuencia"},
    {"cycle": 44, "label": "[S] Esencia fluida en devenir adaptativo"}
  ],
  "final_cluster": "La germinación es devenir, no ser estático",
  "redis_cleared": true
}
```

---

## Experimental Results

### Perturbation bank

| # | Perturbation | Openness type |
|---|---|---|
| 0 | Can consciousness emerge in a network of minimal agents? | Implicit (dominant cultural answer) |
| 1 | What is identity when the collective replaces the individual? | Open |
| 2 | What is lost and gained when a system forgets? | Semi-open |
| 3 | When does cooperation become conflict, and vice versa? | Semi-open |
| 4 | Can purpose emerge in a system without original intention? | Open |
| 5 | How does distributed intelligence differ from individual intelligence? | Bimodal |

---

### Phase 6 — Perturbation bank rotation (C52–C74)

Pattern by perturbation:
- **Perturbation 0** (consciousness): systematic paraphrase — strong implicit answer suppresses exploration
- **Perturbation 1** (identity/collective): elaboration or migration — genuinely open
- **Perturbations 3, 4**: medium elaboration consistently
- **Perturbation 5** (distributed intelligence): bimodal — paraphrase or migration, no middle

Migration cases from this phase:
- **C52**: perturbation 1 · 45 cycles · score 0.75 · pivot c27 → *Uniqueness: Nature vs. Construction*
- **C74**: perturbation 5 · 30 cycles · score 0.65 · pivot c15 → *Order and Chaos: The Dialectic That Generates...*

---

### Phase 7 — Perturbation 1 × 13 runs (R75–R87)

**Protocol:** perturbation 1 · MAX_CYCLES=45 · R75–R85 with Redis cleared · R86–R87 with accumulated memory.

**Results:**

| Run | Cycles | Synth. | Score | Category | Pivot | Redis |
|---|---|---|---|---|---|---|
| R75 | 19 | 1 | 0.65 | migration | c13 | clear |
| R76 | 26 | 3 | 0.10 | paraphrase | — | clear |
| R77 | 13 | 2 | 0.15 | paraphrase | — | clear |
| R78 | 12 | 0 | 0.05 | paraphrase | — | clear |
| R79 | 17 | 1 | 0.15 | paraphrase | — | clear |
| R80 | 12 | 0 | 0.10 | paraphrase | — | clear |
| R81 | 45 | 3 | 0.65 | migration | c38 | clear |
| R82 | 25 | 3 | 0.35 | elaboration | — | clear |
| R83 | 39 | 1 | 0.35 | elaboration | — | clear |
| R84 | 19 | 1 | 0.65 | migration | c8 | clear |
| R85 | 12 | 0 | 0.10 | paraphrase | — | clear |
| R86 | 39 | 3 | 0.45 | elaboration | — | accumulated |
| R87 | 25 | 2 | 0.15 | paraphrase | — | accumulated |

---

### Finding 1 — Two migration mechanisms

| Mechanism | Signal | Runs | Cycles | Final energy |
|---|---|---|---|---|
| A — Strong attractor | Early pivot (≤c15) | R75, R84 | ~19 | High (≥70) |
| B — Accumulated pressure | Late pivot (≥c27) | R81, C52 | 45 (limit) | Low (≤35) |

**Mechanism A:** the field falls into a semantic basin in the first cycles. One synthesis event is enough. High remaining energy indicates the field resolved quickly.

**Mechanism B:** the field spends 30+ cycles in the original domain and escapes through energetic exhaustion and sustained structural tension.

---

### Finding 2 — Uniqueness attractor in perturbation 1

Three of four migrations from perturbation 1 stabilized around the **uniqueness** domain:

- C52 → *Uniqueness: Nature vs. Construction* (pivot c27)
- R75 → *La masa como catalizador de la unicidad* (pivot c13)
- R84 → *La colectividad es el crisol donde la unicidad se forja* (pivot c8)

R81 is the anomalous case — it reached *devenir/fluidez* (pivot c38), possibly a second attractor or an alternative route under accumulated pressure.

---

### Finding 3 — Memory suppresses migration

```
Redis cleared (independent episodes):  11 runs → 3 migrations (27%)
Redis accumulated (prior memory):        2 runs → 0 migrations  (0%)
```

Both control runs (R86, R87) closed with **0 active tensions** — unlike all prior runs which closed with 1–7. The accumulated memory gave the field a pre-built semantic map. It converged without friction toward known synthesis patterns instead of exploring.

> *Memory suppresses tension. Without tension, no exploration. Without exploration, no migration.*

---

## What We Are Not Claiming

- That the system is conscious, reasoning, or understanding
- That migration is frequent (5/31 is a rate, not a stable probability estimate)
- That the two mechanisms fully explain the selection process (what determines which runs fall into the attractor remains open)
- That these findings scale beyond this experimental setup

---

## Open Questions

1. What specific initial condition (cycles 1–5 signal distribution) determines whether the field falls into the uniqueness attractor?
2. Is the uniqueness attractor exclusive to perturbation 1 or does it appear with other open perturbations?
3. How many runs are needed to estimate per-perturbation migration rates with reliable intervals?

---

## Publication

- **Article:** [When an AI System Leaves the Question Behind](https://medium.com/@trogettog/when-an-ai-system-leaves-the-question-behind-5b2492c03ee0) — Medium, March 2026
- **Next:** *Attractors vs Emergence in Semantic Migration* — in progress

---

*Gianfranco Trogetto · Neural Ecology V2 · March 2026*