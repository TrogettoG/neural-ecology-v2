# Neural Ecology V2

**A multi-agent experimental system where ideas compete, synthesize, and sometimes migrate.**

> *The system does not answer questions. It stabilizes around conceptual configurations.*

---

## Design Principle #1

> **Explore cheap. Inhibit often. Densify rarely. Depth is a scarce resource.**

---

## Current Status

**112 runs completed · 7 migrations confirmed · Early bifurcation signal identified**

```
Total evaluated runs: 42+
─────────────────────────────────────────────────────────────
Migration      7   (~16%)   C52, C74, R75, R81, R84, R94, R111
Elaboration   ~12   (~29%)
Paraphrase    ~23   (~55%)
─────────────────────────────────────────────────────────────
Two mechanisms: strong attractor (A) vs accumulated pressure (B)
Memory suppression: 0 migrations with accumulated Redis
Early bifurcation signal: sustained top_tension_score in cycles 10–20
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

### 3. Early bifurcation signal (preliminary)

Cycles 1–9 are structurally identical across all runs. The bifurcation window is **cycles 10–20**.

**Refined hypothesis:**
> Type-B migration correlates with `top_tension_score` remaining ≥ ~0.38 across cycles 10–20 without collapsing to zero.

Status: preliminary evidence — 2 confirmed cases (R94, R111), replication pending.

> *A field that never relaxes eventually escapes its basin.*

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

---

## Publications

- **Article 1:** [When an AI System Leaves the Question Behind](https://medium.com/@trogettog/when-an-ai-system-leaves-the-question-behind-5b2492c03ee0)
- **Article 2:** *The Memory Paradox* — publishing soon

Full experiment log: [CHANGELOG.md](CHANGELOG.md)

---

*Gianfranco Trogetto — March 2026*