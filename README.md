# Neural Ecology V2

**A multi-agent experimental system where ideas compete, synthesize, and sometimes migrate.**

> *The system does not answer questions. It stabilizes around conceptual configurations.*

---

## What This Is

Neural Ecology V2 is an experimental cognitive field where artificial agents (neurons) interact through a shared semantic space. A philosophical question (perturbation) is injected into the field. Neurons activate, form conceptual clusters, generate tensions, and synthesize new concepts under simultaneous pressures:

- **Semantic novelty** — signals that repeat lose intensity
- **Energetic cost** — neurons pay to exist
- **Structural tension** — opposing clusters either absorb or synthesize

The output is not a response. It is a configuration — the conceptual state the field stabilized into after N cycles.

---

## Key Finding

In 21 evaluated runs across 6 perturbations, the system produced three distinct behaviors:

```
Category       Count    %
-----------    -----    ----
Migration        2      10%
Elaboration     10      48%
Paraphrase       9      43%
```

**Semantic migration** — the field stabilizing around a domain the original question did not ask about — appeared in 2 runs (C52, C74). It is rare, but reproducible and measurable.

→ Full write-up: [**When an AI System Leaves the Question Behind**](https://medium.com/@trogettog/when-an-ai-system-leaves-the-question-behind-5b2492c03ee0) *(Medium)*

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
├── config.py           # Field parameters and thresholds
├── models.py           # Signal, Cluster, Neuron, Tension dataclasses
├── memory.py           # Upstash Redis persistence layer
├── field.py            # Cognitive field logic
├── neuron.py           # Agent behavior and energy dynamics
├── orchestrator.py     # Episode runner and synthesis engine
├── dashboard.py        # Rich terminal dashboard
├── main.py             # Perturbation bank and entry point
└── distance_evaluator.py  # LLM-as-judge semantic distance module
```

---

## distance_evaluator.py

An external post-run evaluation module. Given a perturbation, synthesis chain, and final cluster, it returns:

| Field | Type | Description |
|---|---|---|
| `score` | float 0.0–1.0 | Conceptual distance traveled |
| `category` | str | `paraphrase` / `elaboration` / `migration` |
| `trajectory` | str | `stable` / `deepening` / `drift` / `jump` |
| `pivot_cycle` | int \| null | Cycle where domain shift occurred |
| `justification` | str | One-sentence explanation |

**Key design principle:** destination determines score; trajectory determines fine category.

```bash
# Evaluate all known runs
python distance_evaluator.py --batch

# Evaluate a specific run
python distance_evaluator.py --run_id 52

# Interactive mode
python distance_evaluator.py --inline
```

Requires `GEMINI_API_KEY` in environment.

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

## Migration Cases

**C52** — Perturbation 1 (identity/collective) → *Uniqueness: Nature vs. Construction*
45 cycles · 8 synthesis events · score 0.75 · pivot at cycle 27

**C74** — Perturbation 5 (distributed vs. individual intelligence) → *Order and Chaos: The Dialectic That Generates...*
30 cycles · 15 synthesis events · score 0.65 · pivot at cycle 15

---

## What We Are Not Claiming

- That the system is conscious, reasoning, or understanding
- That migration is frequent (2/21 is a rate, not a stable probability estimate)
- That the behavior scales beyond this experimental setup

What we are claiming: there is consistent evidence of semantic migration as a possible but infrequent behavior, detectable by a reproducible external evaluator.

---

## Open Question

If perturbation 1 is run five times with `MAX_CYCLES=45`:
- Do all runs migrate toward the same domain? → structural attractor
- Does each run produce a different itinerary? → genuinely emergent behavior

That distinction changes what the system demonstrates. Next experiment.

---

## Author

Gianfranco Trogetto — March 2026