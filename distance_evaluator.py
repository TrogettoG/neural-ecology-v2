"""
distance_evaluator.py
---------------------
Módulo separado de evaluación semántica post-corrida para Neural Ecology V2.

Mide la distancia conceptual entre la perturbación original y el estado final
del campo, clasificando el resultado como paráfrasis, elaboración o migración.

Uso:
    python distance_evaluator.py --run_id 52
    python distance_evaluator.py --inline   # modo interactivo
    python distance_evaluator.py --batch    # evalúa corridas conocidas

Salida JSON por corrida:
    {
        "run_id": int,
        "score": float,          # 0.0–1.0
        "category": str,         # "paráfrasis" | "elaboración" | "migración"
        "trajectory": str,       # "estable" | "profundización" | "deriva" | "salto"
        "pivot_cycle": int|null, # ciclo donde cruzó el umbral de dominio
        "justification": str     # 1 oración
    }
"""

import json
import os
import sys
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional
from google import genai


# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

MODEL = "gemini-2.5-flash-lite"

THRESHOLDS = {
    "paráfrasis":  (0.00, 0.25),
    "elaboración": (0.26, 0.55),
    "migración":   (0.56, 1.00),
}

# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------

@dataclass
class RunInput:
    """Datos de entrada de una corrida para evaluar."""
    run_id: int
    perturbacion: str
    cluster_final_label: str
    cluster_final_payload: str
    synthesis_chain: list[dict]       # [{"cycle": int, "label": str}, ...]
    snapshot_c15: Optional[str] = None
    snapshot_c25: Optional[str] = None
    snapshot_c30: Optional[str] = None

@dataclass
class EvaluationResult:
    """Resultado de la evaluación semántica."""
    run_id: int
    score: float
    category: str
    trajectory: str
    pivot_cycle: Optional[int]
    justification: str
    raw_response: str = field(default="", repr=False)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_response", None)
        return d

    def display(self):
        """Muestra el resultado formateado en consola."""
        cat_emoji = {"paráfrasis": "🔁", "elaboración": "🔍", "migración": "🌍"}.get(self.category, "?")
        traj_emoji = {
            "estable": "→",
            "profundización": "↓",
            "deriva": "↗",
            "salto": "⚡"
        }.get(self.trajectory, "?")

        print(f"\n{'='*60}")
        print(f"  CORRIDA {self.run_id}  {cat_emoji} {self.category.upper()}")
        print(f"{'='*60}")
        print(f"  Score      : {self.score:.2f}")
        print(f"  Trayectoria: {traj_emoji} {self.trajectory}")
        print(f"  Pivot cycle: {self.pivot_cycle if self.pivot_cycle else 'null'}")
        print(f"  Justif.    : {self.justification}")
        print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Prompt del evaluador
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """Eres un evaluador semántico de trayectorias cognitivas.
Tu tarea es medir qué tan lejos terminó un campo conceptual de su punto de partida.

DEFINICIONES EXACTAS:

PARÁFRASIS (score 0.00–0.25):
- El cluster final reformula o reitera la perturbación original.
- El dominio conceptual es el mismo. No hubo transformación real.
- Ejemplo: perturbación sobre "olvido" → cluster final sobre "el olvido como filtro activo"

ELABORACIÓN (score 0.26–0.55):
- El cluster final sigue en el mismo dominio que la perturbación, pero lo complejizó,
  estructuró, o profundizó significativamente.
- El tema sigue siendo el mismo, pero la comprensión es más rica.
- Ejemplo: perturbación sobre "olvido" → cluster final sobre "selectividad como arquitectura activa de la memoria"

MIGRACIÓN (score 0.56–1.00):
- El cluster final pertenece a un dominio conceptual diferente al de la perturbación.
- El campo no resolvió ni profundizó la pregunta original — se alejó de ella y exploró territorio nuevo.
- Ejemplo: perturbación sobre "identidad/colectivo" → cluster final sobre "unicidad: ¿innata o construida?"

TRAYECTORIAS:
- "estable": el campo se mantuvo en el mismo dominio durante toda la corrida
- "profundización": el campo ahondó progresivamente en el mismo tema
- "deriva": el campo se desplazó gradualmente hacia un dominio adyacente
- "salto": el campo cambió de dominio de forma abrupta en algún ciclo

PIVOT_CYCLE: ciclo donde el campo cruzó el umbral de dominio (solo para migración/deriva).
Inferirlo de la cadena de síntesis. Null para paráfrasis y profundización estable.

Responde ÚNICAMENTE con JSON válido, sin texto adicional, sin markdown, sin explicaciones fuera del JSON.
"""

USER_TEMPLATE = """Evalúa esta corrida del sistema Neural Ecology V2.

PERTURBACIÓN ORIGINAL:
{perturbacion}

CADENA DE SÍNTESIS (ordenada por ciclo):
{synthesis_chain}

CLUSTER DOMINANTE FINAL:
  Label  : {cluster_final_label}
  Payload: {cluster_final_payload}

{snapshots_section}

Responde con este JSON exacto (sin markdown):
{{
  "score": <float 0.0-1.0>,
  "category": "<paráfrasis|elaboración|migración>",
  "trajectory": "<estable|profundización|deriva|salto>",
  "pivot_cycle": <int o null>,
  "justification": "<una sola oración explicando el score>"
}}
"""


def build_prompt(run: RunInput) -> str:
    """Construye el prompt de usuario para la evaluación."""
    if run.synthesis_chain:
        chain_str = "\n".join(
            f"  cy={s['cycle']:02d} → {s['label']}"
            for s in sorted(run.synthesis_chain, key=lambda x: x["cycle"])
        )
    else:
        chain_str = "  (sin síntesis generadas)"

    snapshots = []
    if run.snapshot_c15:
        snapshots.append(f"CLUSTER DOMINANTE EN c15:\n  {run.snapshot_c15}")
    if run.snapshot_c25:
        snapshots.append(f"CLUSTER DOMINANTE EN c25:\n  {run.snapshot_c25}")
    if run.snapshot_c30:
        snapshots.append(f"CLUSTER DOMINANTE EN c30:\n  {run.snapshot_c30}")
    snapshots_section = "\n\n".join(snapshots) if snapshots else ""

    return USER_TEMPLATE.format(
        perturbacion=run.perturbacion,
        synthesis_chain=chain_str,
        cluster_final_label=run.cluster_final_label,
        cluster_final_payload=run.cluster_final_payload,
        snapshots_section=snapshots_section,
    )


# ---------------------------------------------------------------------------
# Evaluador principal
# ---------------------------------------------------------------------------

def evaluate(run: RunInput, api_key: Optional[str] = None) -> EvaluationResult:
    """Evalúa una corrida y retorna el resultado semántico."""
    key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError("Se requiere GEMINI_API_KEY o GOOGLE_API_KEY en el entorno.")

    client = genai.Client(api_key=key)
    prompt = build_prompt(run)

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            max_output_tokens=512,
        ),
    )

    raw = response.text.strip()

    # Limpiar posibles backticks
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"El modelo no retornó JSON válido: {e}\nRespuesta: {raw}")

    # Validar y normalizar
    score = float(data.get("score", 0.0))
    score = max(0.0, min(1.0, score))

    category = data.get("category", "elaboración")
    if category not in ("paráfrasis", "elaboración", "migración"):
        # Inferir por score si el modelo mandó algo inesperado
        if score <= 0.25:
            category = "paráfrasis"
        elif score <= 0.55:
            category = "elaboración"
        else:
            category = "migración"

    trajectory = data.get("trajectory", "estable")
    if trajectory not in ("estable", "profundización", "deriva", "salto"):
        trajectory = "estable"

    pivot = data.get("pivot_cycle")
    if pivot is not None:
        try:
            pivot = int(pivot)
        except (TypeError, ValueError):
            pivot = None

    justification = data.get("justification", "").strip()

    return EvaluationResult(
        run_id=run.run_id,
        score=score,
        category=category,
        trajectory=trajectory,
        pivot_cycle=pivot,
        justification=justification,
        raw_response=raw,
    )


# ---------------------------------------------------------------------------
# Corridas conocidas (ground truth para calibración)
# ---------------------------------------------------------------------------

KNOWN_RUNS: list[RunInput] = [
    # C52 — migración confirmada (perturbación 1, MAX_CYCLES=45)
    RunInput(
        run_id=52,
        perturbacion="¿Qué es la identidad cuando el colectivo reemplaza al individuo?",
        cluster_final_label="[S] Unicidad: Naturaleza vs. Construcción",
        cluster_final_payload=(
            "La unicidad reside en una negociación continua entre la esencia innata "
            "y la agencia activa, moldeándose mutuamente a lo largo del tiempo."
        ),
        synthesis_chain=[
            {"cycle": 8,  "label": "[S] Identidad: Tensión entre Yo y Nosotros"},
            {"cycle": 13, "label": "[S] Agencia Única vs. Disolución Colectiva"},
            {"cycle": 18, "label": "[S] Agencia y la Danza Uniformidad-Unicidad"},
            {"cycle": 27, "label": "[S] Unicidad como Resistencia Colectiva"},
            {"cycle": 35, "label": "[S] Unicidad intrínseca vs. rebelión activa"},
            {"cycle": 40, "label": "[S] Unicidad: Origen y Expresión"},
            {"cycle": 45, "label": "[S] Unicidad: Naturaleza vs. Construcción"},
        ],
        snapshot_c15="[S] La uniformidad anula la singularidad (dominante)",
        snapshot_c25="[S] Agencia Única vs. Disolución Colectiva (dominante)",
        snapshot_c30="[S] Agencia Única vs. Disolución Colectiva (dominante)",
    ),

    # C53 — elaboración/paráfrasis (perturbación 2, 1 síntesis)
    RunInput(
        run_id=53,
        perturbacion="¿Qué se pierde y qué se gana cuando un sistema olvida?",
        cluster_final_label="[S] El olvido, un filtro activo",
        cluster_final_payload=(
            "El olvido activo se redefine no como pasividad sino como un mecanismo "
            "de selección esencial para la cognición y la supervivencia."
        ),
        synthesis_chain=[
            {"cycle": 10, "label": "[S] Olvido activo: filtro cognitivo y evolutivo"},
            {"cycle": 15, "label": "[S] El olvido, un filtro activo"},
        ],
        snapshot_c15="[S] El olvido, un filtro activo (dominante)",
        snapshot_c25="[S] El olvido, un filtro activo (dominante)",
        snapshot_c30="[S] El olvido, un filtro activo (dominante)",
    ),

    # C55 — elaboración (perturbación 2, 5 síntesis)
    RunInput(
        run_id=55,
        perturbacion="¿Qué se pierde y qué se gana cuando un sistema olvida?",
        cluster_final_label="El olvido como filtro, la memoria como construcción",
        cluster_final_payload=(
            "El olvido, lejos de ser un mero filtro, actúa como una criba que "
            "junto a una memoria selectiva redefine la memoria como construcción activa."
        ),
        synthesis_chain=[
            {"cycle": 11, "label": "[S] Selectividad vs. Arquitectura Activa"},
            {"cycle": 20, "label": "[S] Olvido: Proceso Activo y Adaptativo"},
            {"cycle": 25, "label": "[S] Olvido activo: Criba de la memoria"},
            {"cycle": 30, "label": "[S] Olvido: Agente de la Memoria"},
        ],
        snapshot_c15="[S] El olvido como filtro, la memoria como construcción (dominante)",
        snapshot_c25="[S] Selectividad vs. Arquitectura Activa (dominante)",
        snapshot_c30="El olvido como filtro, la memoria como construcción (dominante)",
    ),

    # C57 — paráfrasis (perturbación 4, 4 síntesis convergentes)
    RunInput(
        run_id=57,
        perturbacion="¿Puede emerger propósito en un sistema sin intención original?",
        cluster_final_label="[S] Intención y Caos: Danza Creadora Expansiva",
        cluster_final_payload=(
            "La génesis creativa surge de la intención expansiva que, lejos de limitar, "
            "abre potencial al caos libre, forjando propósito emergente en su interacción."
        ),
        synthesis_chain=[
            {"cycle": 10, "label": "[S] Creación: Potencial Libre y Descontrolado"},
            {"cycle": 19, "label": "[S] Intención vs. Potencial Libre"},
            {"cycle": 24, "label": "[S] Intención-Caos: Danza Creadora"},
            {"cycle": 29, "label": "[S] Intención y Caos: Danza Creadora Expansiva"},
        ],
        snapshot_c15="La ausencia de intención inicial (dominante)",
        snapshot_c25="[S] Creación: Potencial Libre (dominante)",
        snapshot_c30="[S] Intención vs. Potencial Libre (dominante)",
    ),
]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_batch(verbose: bool = True) -> list[EvaluationResult]:
    """Evalúa todas las corridas conocidas."""
    results = []
    print(f"\nEvaluando {len(KNOWN_RUNS)} corridas conocidas...\n")

    for run in KNOWN_RUNS:
        print(f"  → Corrida {run.run_id} ...", end=" ", flush=True)
        try:
            result = evaluate(run)
            results.append(result)
            print(f"✓  [{result.category}  score={result.score:.2f}]")
            if verbose:
                result.display()
        except Exception as e:
            print(f"✗  ERROR: {e}")

    # Resumen comparativo
    print("\n" + "="*60)
    print("  RESUMEN DE CALIBRACIÓN")
    print("="*60)
    print(f"  {'ID':>4}  {'Score':>6}  {'Categoría':>14}  {'Trayectoria':>14}  {'Pivot':>6}")
    print(f"  {'-'*4}  {'-'*6}  {'-'*14}  {'-'*14}  {'-'*6}")
    for r in results:
        pivot_str = str(r.pivot_cycle) if r.pivot_cycle else "null"
        print(f"  {r.run_id:>4}  {r.score:>6.2f}  {r.category:>14}  {r.trajectory:>14}  {pivot_str:>6}")
    print("="*60)

    # Guardar resultados
    output_path = "/mnt/user-data/outputs/distance_evaluations.jsonl"
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
    print(f"\n  Resultados guardados en: {output_path}\n")

    return results


def run_inline():
    """Modo interactivo: el usuario ingresa los datos."""
    print("\n--- EVALUADOR SEMÁNTICO NEURAL ECOLOGY V2 ---")
    print("Modo interactivo. Ingresá los datos de la corrida.\n")

    run_id = int(input("Run ID: "))
    perturbacion = input("Perturbación original: ").strip()
    cluster_label = input("Label cluster dominante final: ").strip()
    cluster_payload = input("Payload cluster dominante final: ").strip()

    print("\nCadena de síntesis (ingresá ciclo,label — línea vacía para terminar):")
    chain = []
    while True:
        line = input("  cy,label: ").strip()
        if not line:
            break
        parts = line.split(",", 1)
        if len(parts) == 2:
            try:
                chain.append({"cycle": int(parts[0]), "label": parts[1].strip()})
            except ValueError:
                print("  (formato inválido, saltando)")

    run = RunInput(
        run_id=run_id,
        perturbacion=perturbacion,
        cluster_final_label=cluster_label,
        cluster_final_payload=cluster_payload,
        synthesis_chain=chain,
    )

    print(f"\nEvaluando corrida {run_id}...")
    result = evaluate(run)
    result.display()

    # Guardar
    output_path = f"/mnt/user-data/outputs/eval_run_{run_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
    print(f"Guardado en: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluador de distancia semántica post-corrida — Neural Ecology V2"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--batch", action="store_true",
                       help="Evalúa todas las corridas conocidas (C52, C53, C55, C57)")
    group.add_argument("--inline", action="store_true",
                       help="Modo interactivo: ingresás los datos manualmente")
    group.add_argument("--run_id", type=int,
                       help="Evalúa una corrida específica por ID (debe estar en KNOWN_RUNS)")
    parser.add_argument("--quiet", action="store_true",
                        help="Solo muestra el resumen, sin display detallado")

    args = parser.parse_args()

    if args.batch:
        run_batch(verbose=not args.quiet)

    elif args.inline:
        run_inline()

    elif args.run_id:
        matching = [r for r in KNOWN_RUNS if r.run_id == args.run_id]
        if not matching:
            print(f"Error: corrida {args.run_id} no encontrada en KNOWN_RUNS.")
            sys.exit(1)
        result = evaluate(matching[0])
        result.display()

    else:
        # Por defecto: batch
        run_batch(verbose=True)


if __name__ == "__main__":
    main()