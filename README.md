# Neural Ecology V2

**A multi-agent experimental system where ideas compete, synthesize, and sometimes migrate.**

> *The system does not answer questions. It stabilizes around conceptual configurations.*

---

## Design Principle #1

> **Explore cheap. Inhibit often. Densify rarely. Depth is a scarce resource.**

---

## Current Status

**235 runs completed · 19 migrations confirmed · Suppression spectrum mapped · STM frontier identified**

```
Total evaluated runs: 235+
─────────────────────────────────────────────────────────────
Migration     ~19   (~17%)
Elaboration   ~40   (~25%)
Paraphrase    ~75   (~58%)
─────────────────────────────────────────────────────────────
Two mechanisms: strong attractor (A) vs accumulated pressure (B)
Phase 7:   memory suppression — 0/10 migrations with accumulated Redis (N=10)
Phase 8.2: top_t ≥ 0.30 in c10–20 = near-necessary condition (perturbation 1)
Phase 9:   epistemic pivot — closed perturbations migrate at 58%
Phase 10:  suppression threshold between decay 0.50–0.80 (switch, not gradient)
Phase 11:  STM forensic search — migration is not locally observable
           The system cannot detect its own conceptual transition.
Phase 12:  LLM direct comparison — architecture redistributes, not amplifies
           LLM direct migrates more with closed questions (P6: 90% vs 33%)
           Neural Ecology produces more variance, not more exploration quality

Series closed — March 2026
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

### 4. Input invariance (Phase 9 — epistemic pivot)

Closed perturbations (√144, boiling point, planets, capital of France) were expected to produce zero migrations. Instead, 7 of 12 runs migrated — a 58% rate, higher than open perturbations.

**Core insight:** conceptual openness is not a property of the question. It is a property of the LLM. The field generates semantically rich signals from any input, sufficient to create tensions and migrate.

What we call a "closed question" is a human epistemic category. For the field, it is just a starting point.

> *The system does not migrate when conditions are right. It migrates by default — and memory is what suppresses it.*

**New research question:** what inhibits migration? Three candidates: memory (confirmed), semantic constraints (untested), run length.

### 5. Suppression spectrum — decay rates (Phase 10)

The memory decay experiment mapped the full suppression spectrum:

```
Decay 0.50 (accumulated)  →  10% migration  — below suppression threshold
Decay 0.80 (accumulated)  →   0% migration  — threshold crossed
Decay 0.95 (accumulated)  →   0% migration  — threshold crossed
```

Suppression is a **switch**, not a gradient. Standard and Slow produce identical migration rates — more retention above the threshold adds no additional suppression. The system is already locked.

**The Depth Paradox:** Slow decay (0.95) scores slightly higher than Standard (0.205 vs 0.240) — it explores more deeply *within* the original domain, but that depth raises the walls. Expert-level confirmation bias.

> *Forgetting is not data loss. It is the mechanism that keeps the field below its suppression threshold.*

### 6. STM forensic search — Phase 11

40 runs with full cycle-by-cycle snapshots (c1–45). Objective: identify the Structural Trigger of Migration.

Three hypotheses tested: synthesis chain direction, domain-exit events, no-return condition. All partially falsified by the same case: **R217 vs R214** — structurally identical Phase 3 profiles, one migrates, one does not.

**Core finding:** migration is not a locally observable event. The system cannot detect its own conceptual transition.

Two types of domain exit:

- **Noise drift** — field exits the domain but reaches a semantically generic configuration. Evaluator: elaboration.
- **True migration** — field exits the domain and stabilizes in a coherent alternative configuration. Evaluator: migration.

Both look identical from inside the system. The distinction is visible only from outside.

> *The STM is not a structural event internal to the system. It is a classification of the outcome by an external observer.*

This is not a failure of the experiment. It defines the frontier of internal observability — and opens the next research question: what makes a destination domain stable enough for the field to remain in it?

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
| R137 | B | 18 | 0.75 | c13 | (Phase 10 — Fast decay) |
| R158 | B | 26 | 0.75 | c26 | (Phase 10 — Fast decay) |
| R214 | B | 45 | 0.65 | c38 | [S] Individuo Activo vs. Esencia Única |
| R220 | B | 45 | 0.65 | c34 | [S] Fragilidad: Puerta al Crecimiento |
| R227 | B | 45 | 0.65 | c38 | [S] Fluidez Autónoma en la Unidad |

---

## Publications

- **Article 1:** [When an AI System Leaves the Question Behind](https://medium.com/@trogettog/when-an-ai-system-leaves-the-question-behind-5b2492c03ee0) — Medium
- **Article 2:** [The Memory Paradox](https://medium.com/@trogettog/the-memory-paradox-940be28bc77a) — Medium
- **Article 3:** [When Tension Is Not Enough](https://medium.com/@trogettog/when-tension-is-not-enough-1d4089971368) — Medium
- **Article 4:** [Forgetting as a Design Tool](https://medium.com/@trogettog/forgetting-as-a-design-tool-dabc357a379f) — Medium
- **Substack:** [gianfrancotrogetto.substack.com](https://gianfrancotrogetto.substack.com)

Full experiment log: [CHANGELOG.md](CHANGELOG.md)

---

---

*Gianfranco Trogetto — March 2026*