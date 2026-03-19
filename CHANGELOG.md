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

---

## Phase 8 — Early cycle instrumentation (cycles 1–20)

### Engineering

**`orchestrator.py`** — added `early_snapshots` capture after each of cycles 1–20:

```json
{
  "cycle": 10,
  "energy": 85.5,
  "cluster_count": 5,
  "tension_count": 1,
  "neurons_alive": 4,
  "top_tension_score": 0.492,
  "top_2_clusters": [...]
}
```

**`distance_evaluator.py`** — added `--from_json` and `--auto_batch` flags. No longer requires KNOWN_RUNS for new runs. Added `load_dotenv()`.

---

## Phase 8.1 — Early bifurcation signal

**Objective:** detect structural differences in cycles 1–20 between type-B migration runs and non-migration runs.

### Finding: cycles 1–9 are structurally identical

All runs — migrations and non-migrations — produce the same snapshot pattern in cycles 1–9:
- Cycles 1–4: single cluster, zero tensions
- Cycle 5: first 3 tensions appear (~0.415 top_t)
- Cycle 9: tension reset to zero in all runs

The bifurcation window is **cycles 10–20**, not 1–5.

### Hypothesis lifecycle

**H1 — Single-axis tension (tc=1)**
```
Formulated: R94 shows tc=1 with top_t 0.49→0.43 for 4 consecutive cycles (c10-c13)
Tested: pattern present in R94 (migration)
Falsified: R111 (tc=3 throughout, migration occurred at pivot c25)
Status: REJECTED
```

**H2 — Sustained dominant tension (refined)**
```
Hypothesis: Type-B migration occurs when top_tension_score remains >= ~0.38
across cycles 10–20 without collapsing to zero.

Evidence:
  R94  (migration): top_t never collapses in c10-20 (9/11 cycles >= 0.40)
  R111 (migration): top_t never collapses in c10-20 (11/11 cycles >= 0.47)

Non-migrations: most runs show at least one cycle where top_t = 0.0
(the c9 reset pattern re-emerges intermittently in c10-20)

Counterexample candidate:
  R102 (paraphrase): sustained top_t similar to R94, but closed at cycle 20
  → suggests sustained tension + sufficient cycles are both required

Status: PRELIMINARY EVIDENCE — 2 confirmed cases, replication pending
```

### Conceptual reframe

The signal is not *concentration* of tension but *continuity* of semantic pressure.

> *A field that never relaxes eventually escapes its basin.*

This shifts the interpretive frame from structural geometry (single axis) to temporal dynamics (sustained pressure). The tension count matters less than whether the dominant tension survives each cycle without resolution.

### Dataset summary (Phase 8.1)

```
Runs with early snapshots c10-20: 11
  Type-B migrations confirmed:  2  (R94, R111)
  Non-migrations:                9
  Open case:                     1  (R102)
```

### Next experiment

Reproduce 2–3 additional type-B migrations with snapshots c1–20 and verify:
- Does `top_tension_score` remain >= 0.38 throughout c10-20 in all cases?
- Does R102-style early closure explain the exception?

---

*Gianfranco Trogetto · Neural Ecology V2 · March 2026*

---

## Phase 8.2 — Hypothesis validation + falsification (R113–R122)

**Protocol:** 10 runs, perturbation 1, Redis cleared, MAX_CYCLES=45.
**Results:** 2 migrations (R113, R122), 7 paraphrases, 1 elaboration.

### Hypothesis lifecycle — Phase 8.1 → 8.2

**H1 (Phase 8.1):** top_tension_score ≥ 0.38 in c10-20 without collapse
- Falsified direction 1: R122 migrates despite 1-cycle collapse at c15
- Falsified direction 2: R121 never collapses but does NOT migrate
- Status: **REJECTED**

**H2 (Phase 8.2 — finding):** near-necessary condition + STM framework

> `top_tension_score` never drops below ~0.30 across cycles 10–20 in all
> 4 confirmed type-B migrations. This is a **near-necessary condition**
> (R122 has one zero at c15 but migrates anyway — brief single-cycle collapse
> does not disrupt the overall regime).
>
> Migration requires two conditions:
> 1. Near-necessary: top_t ≥ 0.30 sustained in c10–20
> 2. Structural Trigger of Migration (STM): an event in c20+ that reorganizes
>    the field beyond the original perturbation domain
>
> Tension is the energetic condition. STM is the structural condition.
> R121 satisfies condition 1 but never fires condition 2.
>
> *Tension accumulates, but transformation is discrete.*

### New migration cases

| Run | Cycles | Score | Pivot | Notes |
|---|---|---|---|---|
| R113 | 32 | 0.65 | c25 | Clean type-B, top_t never collapses |
| R122 | 45 | 0.65 | c34 | 1-cycle collapse at c15, recovers, migrates to uniqueness attractor |

### Key counterexample: R121

R121 is the most important data point of Phase 8.2.

- 41 cycles, energy 29.1 (type-B profile)
- top_t c10-20: 0.34→0.57, **never collapses**
- Did NOT migrate → elaboration 0.35

This falsifies the "sustained tension = migration" direction and establishes that
the field can sustain pressure for 40+ cycles without escaping its domain.
Something beyond tension — the STM — determines whether migration occurs.
Naming the unknown precisely converts R121 from a counterexample into a research question.

### Evidence table

| Run | top_t min c10-20 | Collapses | Migrates |
|---|---|---|---|
| R94 | 0.361 | 0 | YES |
| R111 | 0.478 | 0 | YES |
| R113 | 0.376 | 0 | YES |
| R122 | 0.000 (1 cycle) | 1 | YES |
| R97 | 0.000 | 2 | NO |
| R121 | 0.340 | 0 | NO |

### Conceptual reframe

> *Tension opens the door. Something else decides whether the field walks through.*

The field operates in three phases:
- c1-9: structurally identical across all runs (no bifurcation signal)
- c10-20: tension regime established — near-necessary condition (top_t ≥ 0.30)
- c20+: the STM either fires or doesn't — this is the open research question

Phase 3 is where the paper opens, not closes. R121 and R94 enter Phase 3
identically (both with sustained tension). Only R94 fires the STM at c30.
What is different between them in Phase 3? That is Article 4's question.

### Dataset summary

```
Total runs: 122
Migrations confirmed: 9
  Type A (strong attractor): C52, R75, R84
  Type B (accumulated pressure): C74, R81, R94, R111, R113, R122
Phases complete: 1–8.2
```

### Next: Article 3

"When Tension Is Not Enough: Necessary Conditions for Semantic Migration
in Multi-Agent Systems"

This is Paper 3. Not a correction of Paper 2 — a different type of knowledge.
Paper 2 = observation. Paper 3 = theory about the phenomenon.

The scientific value: falsifying your own hypothesis in both directions,
then identifying a robust partial finding and naming the unknown precisely
(STM), is the structure of real research.

Key phrase: *Tension accumulates, but transformation is discrete.*

---

*Gianfranco Trogetto · Neural Ecology V2 · March 2026*

---

## Phase 9 — Input Invariance Test (R123–R134)

**Original objective:** establish a non-migration baseline using closed perturbations.
**What actually happened:** epistemic pivot.

### Protocol
- 4 closed perturbations (B6–B9), 3 runs each, Redis cleared, MAX_CYCLES=45
- Perturbations: √144, boiling point of water, planets in solar system, capital of France

### Results

```
Perturbation             Migrations   Rate
────────────────────────────────────────
Raíz cuadrada (144)      1/3          33%
Punto de ebullición      3/3         100%
Planetas sistema solar   2/3          67%
Capital de Francia       1/3          33%
────────────────────────────────────────
Total                    7/12         58%
```

**Open perturbation 1 baseline for comparison:** ~17% migration rate.

### Epistemic pivot — "closed perturbations" do not exist in this system

The original hypothesis was falsified completely:

> *"Closed perturbations never produce migration."*

Not only did they produce migration — they produced it at a higher rate than open perturbations.

### What this reveals

**Conceptual openness is a property of the processor, not the input.**

The field does not read that √144 has a unique answer. When the LLM generates signals in response to the question, it produces semantically rich content (numbers, perfection, base 10, mathematical construction) that is sufficient to create tensions and eventually migrate.

What we call a "closed question" is a human epistemic category. For the semantic field, it is just another starting point.

### Failure of the near-necessary condition

The top_t ≥ 0.30 pattern identified in Phase 8.2 does not generalize:

```
R126 (migration): 2 collapses in c10-20  → migrates anyway
R128 (migration): 8 collapses in c10-20  → migrates anyway
R129 (migration): 8 collapses in c10-20  → migrates anyway
R130 (migration): 8 collapses in c10-20  → migrates anyway
```

The near-necessary condition holds for perturbation 1 (type-B migrations) but does not hold cross-perturbation. It may be a perturbation-specific pattern, not a universal property.

### Reframing: Phase 9 as input invariance test

Phase 9 is not a failed baseline experiment. It is evidence that the system is largely **input-invariant** at the level of question structure.

Migration is not triggered by open-ended questions. It is the default behavior of the system under sufficient semantic pressure — regardless of what triggered that pressure.

### New research questions

The relevant question is no longer:
> *"When does the system migrate?"*

It is:
> *"What inhibits migration?"*

Three candidates:
1. **Memory** — confirmed in Phase 7 (0% with accumulated Redis)
2. **Semantic constraints** — untested
3. **Run length** — does everything migrate given enough cycles?

### Impact on Article 5

This finding reframes The AGI Paradox entirely.

The system is not *capable* of migration under certain conditions.
The system *defaults* to migration — and memory is what suppresses it.

The industry is not just failing to build systems that can explore.
It may be actively suppressing a default exploratory behavior that emerges naturally from semantic tension.

---

*Gianfranco Trogetto · Neural Ecology V2 · March 2026*

---

## Phase 10 — Memory Decay Experiment (R156–R187)

**Objective:** determine whether an intermediate decay rate maximizes exploration without collapsing structural coherence.

**Protocol:**
- 3 configurations × 10 runs each, Redis cleared between configurations
- Redis accumulated within each configuration (--no-clear-redis)
- Perturbation 1, MAX_CYCLES=45
- Clean run discarded at start of each configuration

### Results

```
Configuration          Migrations   Elaborations   Paraphrases   Mean score
──────────────────────────────────────────────────────────────────────────
Fast  decay (0.50)        1/10 (10%)    4/10 (40%)    5/10 (50%)   0.260
Standard   (0.80)         0/10  (0%)    4/10 (40%)    6/10 (60%)   0.205
Slow  decay (0.95)        0/10  (0%)    4/10 (40%)    6/10 (60%)   0.240
```

### Suppression spectrum (complete)

```
Condition                    Migration rate   Dominant behavior
──────────────────────────────────────────────────────────────
Redis cleared (~17%)              ~17%        Pure exploration
Fast decay 0.50 (accumulated)     10%         Assisted exploration
Standard   0.80 (accumulated)      0%         Local elaboration
Slow decay 0.95 (accumulated)      0%         Rigid deepening
Redis full — Phase 7               0%         Full suppression
```

### Hypothesis result

**Hypothesis:** there exists an intermediate decay rate that maximizes exploration without collapsing structural coherence.

**Result:** NOT confirmed in this range.

The pattern is not a curve with a sweet spot — it is a **threshold**.

- Below ~0.60 decay: memory never reaches critical mass → exploration preserved
- Above ~0.80 decay: critical mass reached → migration suppressed completely

### Key finding: the suppression threshold is a switch, not a gradient

Standard (0.80) and Slow (0.95) produce identical migration rates (0%) and near-identical elaboration rates (~40%). More retention does not add more suppression once the threshold is crossed. The system is already on the other side.

This means suppression is binary at the macro level: the field either has enough accumulated memory to block migration, or it doesn't. The exact decay rate above the threshold is irrelevant.

### The Depth Paradox

Slow decay (0.95) has a slightly higher mean score (0.240) than Standard (0.205). The system with more retention explores more deeply *within* the original domain — but that same depth makes the walls higher. It becomes an expert in the domain of the perturbation. That expertise is precisely what prevents migration.

> *The system digs deeper into the well, but the walls grow with it.*

This is the technical definition of algorithmic confirmation bias.

### Conceptual reframe

The suppression threshold is the "semantic escape velocity":

> If the system retains more than ~50-60% of what it processes across a series of episodes, the association network becomes dense enough that no individual tension — however high — can break the structure.

Forgetting is not a data loss. It is the mechanism that keeps the system below the suppression threshold.

### Impact on Article 4

The article's core argument shifts from "there is a sweet spot" to something stronger:

> *Forgetting is not a design flaw. It is the mechanism that preserves the field's capacity for transformation. The industry is not building smarter systems — it is building systems with higher semantic gravity. Past a certain threshold, no tension can achieve escape velocity.*

### Note on protocol

First attempt (R135–R149) was invalidated: Redis was not cleared between configurations, making groups non-comparable. Those runs were discarded. This dataset (R156–R187) uses the correct protocol.

---

*Gianfranco Trogetto · Neural Ecology V2 · March 2026*