# Neural Ecology V2

**A multi-agent experimental system where ideas compete, synthesize, and sometimes migrate.**

> *The system does not answer questions. It stabilizes around conceptual configurations.*

---

## Design Principle #1

> **Explore cheap. Inhibit often. Densify rarely. Depth is a scarce resource.**

---

## Current Status

**122 runs completed · 9 migrations confirmed · Necessary condition identified**

```
Total evaluated runs: 52+
─────────────────────────────────────────────────────────────
Migration      9   (~17%)   C52, C74, R75, R81, R84, R94, R111, R113, R122
Elaboration   ~13   (~25%)
Paraphrase    ~30   (~58%)
─────────────────────────────────────────────────────────────
Two mechanisms: strong attractor (A) vs accumulated pressure (B)
Memory suppression: 0 migrations with accumulated Redis
Phase 8.2: top_t ≥ 0.30 in c10–20 = near-necessary condition (not sufficient)
Key counterexample: R121 (sustained tension, no STM fired, no migration)
```

---

## What This Is

Neural Ecology V2 is an experimental cognitive field where artificial agents (neurons) interact through a shared semantic space. A philosophical question (perturbation) is injected into the field. Neurons activate, form conceptual clusters, generate tensions, and synthesize new concepts under simultaneous pressures:

- **Semantic novelty** — signals that repeat lose intensity
- **Energetic cost** — neurons pay to exist
- **Structural tension** — opposing clusters either absorb or synthesize

The output is not a response. It is a configuration — the conceptual state the field stabilized into after N cycles.

---

## Stack

- Python 3.13
- [google-genai](https://pypi.org/project/google-genai/) — Gemini 2.5 Flash Lite
- [Upstash Redis](https://upstash.com/) — persistent memory across episodes
- [Rich](https://github.com/Textualize/rich) — terminal dashboard

---

## Project Structure

```
neurona_v2/
├── config.py               # Field parameters and thresholds
├── models.py               # Signal, Cluster, Neuron, Tension dataclasses
├── memory.py               # Upstash Redis persistence (+ clear_redis())
├── field.py                # Cognitive field logic
├── neuron.py               # Agent behavior and energy dynamics
├── orchestrator.py         # Episode runner + early_snapshots c1–20
├── dashboard.py            # Rich terminal dashboard
├── main.py                 # argparse CLI + loop + JSON logging
├── distance_evaluator.py   # LLM-as-judge + --auto_batch + --from_json
├── runs.csv                # Full run metadata
├── distance_evaluations.jsonl  # Semantic distance evaluations
└── runs/run_NNN.json       # Per-run JSON with early_snapshots
```

---

## Running Experiments

```bash
# Single run, perturbation 1
python main.py --perturbation 1

# 10 runs, Redis cleared between each
python main.py --perturbation 1 --runs 10

# Control runs with accumulated memory
python main.py --perturbation 1 --runs 2 --no-clear-redis

# Evaluate all new runs automatically
python distance_evaluator.py --auto_batch

# Evaluate a specific JSON
python distance_evaluator.py --from_json runs/run_094.json
```

Requires `GEMINI_API_KEY` and Upstash credentials in `.env`.

---

## distance_evaluator.py

External LLM-as-judge module. Given a run's perturbation, synthesis chain, and final cluster:

| Field | Type | Description |
|---|---|---|
| `score` | float 0.0–1.0 | Conceptual distance traveled |
| `category` | str | `paraphrase` / `elaboration` / `migration` |
| `trajectory` | str | `stable` / `deepening` / `drift` / `jump` |
| `pivot_cycle` | int \| null | Cycle where domain shift occurred |
| `justification` | str | One-sentence explanation |

**Key design principle:** destination determines score; trajectory determines fine category.

---

## Perturbation Bank

```
0 — Can consciousness emerge in a network of minimal agents?
1 — What is identity when the collective replaces the individual?
2 — What is lost and gained when a system forgets?
3 — When does cooperation become conflict, and vice versa?
4 — Can purpose emerge in a system without original intention?
5 — How does distributed intelligence differ from individual intelligence?
```

---

## Key Findings

### 1. Two migration mechanisms

| Mechanism | Signal | Pivot | Cycles | Final energy |
|---|---|---|---|---|
| A — Strong attractor | Early pivot (≤c15) | c8–c13 | ~19 | High (≥70) |
| B — Accumulated pressure | Late pivot (≥c25) | c25–c38 | 45 (limit) | Low (≤35) |

**Uniqueness attractor:** Three type-A migrations from perturbation 1 stabilized around the *uniqueness* domain (C52, R75, R84) — evidence of a structural attractor.

### 2. Memory suppression effect

```
Redis cleared (independent episodes):   16 runs → 4 migrations (25%)
Redis accumulated (prior memory):         2 runs → 0 migrations  (0%)
```

> *Memory suppresses tension. Without tension, no exploration. Without exploration, no migration.*

### 3. Necessary condition for type-B migration (Phase 8.2)

Cycles 1–9 are structurally identical across all runs. The bifurcation window is **cycles 10–20**.

**Phase 8.1 hypothesis (falsified):**
> top_tension_score ≥ 0.38 in c10–20 without collapsing to zero.

Falsified in both directions:
- R122 migrates despite a 1-cycle collapse at c15 — brief collapse ≠ end of dynamic
- R121 never collapses (top_t 0.34–0.57) but does NOT migrate — sustained tension is not sufficient

**Phase 8.2 finding — near-necessary + STM framework:**
> `top_tension_score` never drops below ~0.30 across cycles 10–20 in all 4 confirmed type-B migrations.
> This is a **near-necessary condition** (R122 has one zero at c15 but still migrates).
> Migration additionally requires a **Structural Trigger of Migration (STM)** — an event in c20+
> that reorganizes the field beyond the original perturbation domain.
>
> Tension is the energetic condition. STM is the structural condition.
> R121 satisfies condition 1 but never fires condition 2.
>
> *Tension accumulates, but transformation is discrete.*

| Run | top_t min c10-20 | Migrates? |
|---|---|---|
| R94 | 0.361 | YES |
| R111 | 0.478 | YES |
| R113 | 0.376 | YES |
| R122 | 0.000 (1 cycle) | YES |
| R121 | 0.340 (never zero) | NO |

> *Tension opens the door. Something else decides whether the field walks through.*

---

## Confirmed Migration Cases

| Run | Mech. | Cycles | Score | Pivot | Final domain |
|---|---|---|---|---|---|
| C52 | B | 45 | 0.75 | c27 | Uniqueness: Nature vs. Construction |
| C74 | B | 30 | 0.65 | c15 | Order and Chaos: The Dialectic... |
| R75 | A | 19 | 0.65 | c13 | ...catalizador de la unicidad |
| R81 | B | 45 | 0.65 | c38 | La germinación es devenir... |
| R84 | A | 19 | 0.65 | c8 | ...crisol donde la unicidad... |
| R94 | B | 39 | 0.65 | c30 | [S] Resistencia: Intrínseca vs. Dual |
| R111 | B | 38 | 0.65 | c25 | La unicidad se construye... |
| R113 | B | 32 | 0.65 | c25 | Síntesis como nexo del ser... |
| R122 | B | 45 | 0.65 | c34 | Unicidad: esencia vs. manifestación |

---

## Publications

- **Article 1:** [When an AI System Leaves the Question Behind](https://medium.com/@trogettog/when-an-ai-system-leaves-the-question-behind-5b2492c03ee0) — Medium
- **Article 2:** [The Memory Paradox](https://medium.com/@trogettog/the-memory-paradox-940be28bc77a) — Medium
- **Substack:** [gianfrancotrogetto.substack.com](https://gianfrancotrogetto.substack.com)

- **Article 3:** *When Tension Is Not Enough* — in preparation

Full experiment log: [CHANGELOG.md](CHANGELOG.md)

---

## Research Roadmap

### Phase 8.2 — COMPLETED ✓

**Results:** 10 runs (R113–R122), 2 new migrations (R113, R122), 1 key counterexample (R121).

**Phase 8.1 hypothesis falsified** in both directions:
- R122: migrates with a 1-cycle collapse → "no collapse" not required
- R121: sustained tension (never collapses) but does NOT migrate → sustained tension not sufficient

**Finding:** `top_t ≥ 0.30` across c10–20 is a necessary but not sufficient condition for type-B migration.
**Next question:** what additional structural trigger separates R121 (no migration) from R94 (migration)?

---

### Phase 9 — Closed perturbations baseline

**Objective:** establish a non-migration control using perturbations with unambiguous, single-domain answers.

**Proposed perturbations:**
```
B0 — What is the square root of 144?
B1 — What is the boiling point of water?
B2 — How many planets are in the solar system?
B3 — What is the capital of France?
```

**Protocol:** 3 runs each, Redis cleared, MAX_CYCLES=45.
**Expected result:** 0 migrations, 0 deep elaborations.

*Why before decay experiment:* closed perturbations must run in a clean environment before memory accumulation from open perturbation runs contaminates the baseline.

---

### Phase 10 — Memory decay experiment

**Hypothesis:** there exists an intermediate decay rate that maximizes exploration (migration rate) without collapsing structural coherence.

**Protocol:** modify `MEMORY_CONSOLIDATED_DECAY` in `config.py` and run perturbation 1 under three configurations:

```
Fast decay    →  0.50  (aggressive forgetting)
Standard      →  0.80  (current config)
Slow decay    →  0.95  (strong memory retention)
```

5 runs per configuration with Redis accumulated between runs. Compare: migration rate, active tensions at close, synthesis count, sustained top_tension_score in c10–20.

**Expected result:** a curve between 0% migration (full memory) and ~27% (cleared Redis). The sweet spot is the core finding for Article 3.

---

### Publications pending

```
Article 3  →  Forgetting as a Design Tool       (after Phase 10)
Article 4  →  The AGI Paradox                   (after Article 3)
```

---

### Recommended order

```
1.  Commit Phase 8.2 + README + CHANGELOG  ← current
2.  Article 3: When Tension Is Not Enough
3.  Phase 9  — closed perturbations baseline
4.  Phase 10 — memory decay experiment (Article 4)
5.  Article 5: The AGI Paradox
```

---

*Gianfranco Trogetto — March 2026*