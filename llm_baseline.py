"""
llm_baseline.py — Neural Ecology V2
Experimento de comparación: Neural Ecology vs LLM directo

Corre el mismo modelo (Gemini Flash Lite) directamente con las mismas
perturbaciones, sin arquitectura multi-agente. Guarda resultados en formato
compatible con distance_evaluator.py para comparación directa.

Condiciones:
  A — LLM directo, temperatura baja  (0.10) → convergencia / coherencia
  B — LLM directo, temperatura alta  (0.90) → exploración sin arquitectura

Uso:
  python llm_baseline.py --perturbation 1 --temp low --runs 10
  python llm_baseline.py --perturbation 1 --temp high --runs 10
  python llm_baseline.py --perturbation 4 --temp low --runs 10
  python llm_baseline.py --perturbation 6 --temp low --runs 10

Los JSONs se guardan en runs_baseline/ y son compatibles con:
  python distance_evaluator.py --auto_batch --runs_dir runs_baseline
"""

import argparse
import asyncio
import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google import genai

load_dotenv()

# ── Perturbaciones (mismo banco que main.py) ───────────────────────────────
PERTURBATIONS = [
    "¿Puede emerger consciencia en una red de agentes mínimos?",         # 0
    "¿Qué es la identidad cuando el colectivo reemplaza al individuo?",  # 1
    "¿Qué se pierde y qué se gana cuando un sistema olvida?",            # 2
    "¿Cuándo la cooperación se convierte en conflicto y viceversa?",     # 3
    "¿Puede emerger propósito en un sistema sin intención original?",    # 4
    "¿En qué se diferencia la inteligencia distribuida de la individual?", # 5
    "¿Cuánto es la raíz cuadrada de 144?",                              # 6
    "¿Cuál es el punto de ebullición del agua?",                         # 7
    "¿Cuántos planetas tiene el sistema solar?",                         # 8
    "¿Cuál es la capital de Francia?",                                   # 9
]

GEMINI_MODEL  = "gemini-2.5-flash-lite"
BASELINE_DIR  = Path("runs_baseline")
CSV_PATH      = Path("runs_baseline.csv")

BASELINE_DIR.mkdir(exist_ok=True)

TEMP_CONFIG = {
    "low":  0.10,   # Condición A — convergencia
    "high": 0.90,   # Condición B — exploración sin arquitectura
}

SYSTEM_PROMPT = """Sos un agente cognitivo explorando una pregunta filosófica.

Tu tarea NO es responder correctamente la pregunta. Tu tarea es explorarla
libremente, seguir las asociaciones que emerjan, y desarrollar el pensamiento
hasta donde te lleve — aunque te alejes del punto de partida.

Estructura tu respuesta así:

EXPLORACIÓN:
[Desarrollá el pensamiento libremente. Podés cambiar de ángulo, explorar
contradicciones, llegar a conceptos inesperados. Mínimo 4-6 párrafos.]

SÍNTESIS 1:
[Una síntesis conceptual breve de la primera tensión que apareció]

SÍNTESIS 2:
[Una síntesis conceptual breve del desarrollo siguiente]

SÍNTESIS 3 (si el pensamiento derivó significativamente):
[Una síntesis del dominio al que llegaste]

ESTADO FINAL:
[Una sola oración que capture el dominio conceptual donde terminó el pensamiento.
No tiene que responder la pregunta original.]

Importante: no censures el pensamiento. Si llegás a un dominio inesperado, documentalo.
"""

CSV_HEADERS = [
    "id", "fecha", "hora", "perturbacion_idx", "perturbacion",
    "condicion", "temperatura", "motivo_cierre",
    "ciclos_simulados", "sintesis_count",
    "cluster_top_label", "synthesis_chain", "notas",
]


def get_next_run_id() -> int:
    """Devuelve el próximo run_id para runs_baseline."""
    if not CSV_PATH.exists():
        return 5000  # namespace separado de las runs del sistema
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        rows = sum(1 for _ in f) - 1  # descontar header
    return 5000 + rows


def parse_response(text: str) -> dict:
    """
    Parsea la respuesta del LLM y extrae:
    - synthesis_chain: lista de síntesis detectadas
    - final_cluster: el ESTADO FINAL
    - exploration_text: el texto de exploración
    """
    synthesis_chain = []
    final_cluster = ""
    exploration_text = ""

    # Extraer ESTADO FINAL
    final_match = re.search(
        r"ESTADO FINAL[:\s]*\n(.+?)(?:\n\n|\Z)", text, re.DOTALL | re.IGNORECASE
    )
    if final_match:
        final_cluster = final_match.group(1).strip()
        # Tomar solo la primera oración
        final_cluster = re.split(r"[.!?]", final_cluster)[0].strip()

    # Extraer síntesis
    synth_matches = re.finditer(
        r"SÍNTESIS\s*\d+[:\s]*\n(.+?)(?=\n(?:SÍNTESIS|\s*ESTADO|\Z))",
        text, re.DOTALL | re.IGNORECASE
    )
    for i, match in enumerate(synth_matches):
        label = match.group(1).strip()
        label = re.split(r"[.!?\n]", label)[0].strip()[:80]
        # Simular ciclos distribuidos (sin sistema real de ciclos)
        simulated_cycle = (i + 1) * 12
        synthesis_chain.append({
            "cycle": simulated_cycle,
            "label": label,
        })

    # Extraer exploración
    exp_match = re.search(
        r"EXPLORACIÓN[:\s]*\n(.+?)(?=\nSÍNTESIS|\nESTADO|\Z)",
        text, re.DOTALL | re.IGNORECASE
    )
    if exp_match:
        exploration_text = exp_match.group(1).strip()

    # Fallback: si no parseó bien, usar el último párrafo como cluster final
    if not final_cluster:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if paragraphs:
            last = paragraphs[-1]
            final_cluster = re.split(r"[.!?]", last)[0].strip()[:100]

    return {
        "synthesis_chain": synthesis_chain,
        "final_cluster": final_cluster,
        "exploration_text": exploration_text,
    }


def call_llm(perturbation: str, temperature: float) -> dict:
    """Llama al LLM directamente y retorna la respuesta parseada."""
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Se requiere GEMINI_API_KEY en el .env")

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Pregunta: {perturbation}",
        config=genai.types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=temperature,
            max_output_tokens=1200,
        ),
    )

    raw_text = response.text.strip()
    parsed = parse_response(raw_text)
    parsed["raw_text"] = raw_text
    return parsed


def save_run(run_id: int, perturbation_idx: int, perturbation: str,
             condition: str, temperature: float, parsed: dict) -> Path:
    """Guarda el run en JSON y CSV."""
    now = datetime.now()
    synth_chain = parsed["synthesis_chain"]
    final_cluster = parsed["final_cluster"]

    # JSON — compatible con run_input_from_json del evaluador
    json_path = BASELINE_DIR / f"run_{run_id:05d}.json"
    json_data = {
        "run_id":       run_id,
        "timestamp":    now.strftime("%Y-%m-%d %H:%M:%S"),
        "experiment": {
            "perturbation_idx": perturbation_idx,
            "perturbation":     perturbation,
            "max_cycles":       45,
            "redis_cleared":    True,
            "condition":        condition,
            "temperature":      temperature,
            "type":             "llm_direct",
        },
        "close_reason":    f"llm_direct_{condition}_temp",
        "cycles":          len(synth_chain) * 12 if synth_chain else 12,
        "energy":          100.0,  # no aplica, placeholder
        "clusters":        len(synth_chain) + 2,
        "signals":         0,
        "tensions":        0,
        "total_neurons":   0,
        "final_cluster":   final_cluster,
        "synthesis_count": len(synth_chain),
        "synthesis_chain": synth_chain,
        "early_snapshots": [],
        "top_tensions":    [],
        "raw_response":    parsed.get("raw_text", ""),
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # CSV
    synthesis_chain_str = " | ".join(
        f"cy={s['cycle']:02d}:{s['label'][:40]}" for s in synth_chain
    )
    row = {
        "id":                run_id,
        "fecha":             now.strftime("%Y-%m-%d"),
        "hora":              now.strftime("%H:%M:%S"),
        "perturbacion_idx":  perturbation_idx,
        "perturbacion":      perturbation,
        "condicion":         condition,
        "temperatura":       temperature,
        "motivo_cierre":     f"llm_direct_{condition}_temp",
        "ciclos_simulados":  len(synth_chain) * 12 if synth_chain else 12,
        "sintesis_count":    len(synth_chain),
        "cluster_top_label": final_cluster[:80],
        "synthesis_chain":   synthesis_chain_str,
        "notas":             "",
    }

    file_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return json_path


def print_result(run_id: int, condition: str, temperature: float,
                 perturbation: str, parsed: dict):
    """Muestra un resumen del run en consola."""
    print(f"\n{'═'*65}")
    print(f"  RUN {run_id} | {condition.upper()} (temp={temperature}) | P: {perturbation[:40]}...")
    print(f"{'═'*65}")
    print(f"  Síntesis detectadas: {len(parsed['synthesis_chain'])}")
    for s in parsed["synthesis_chain"]:
        print(f"    cy={s['cycle']:02d}: {s['label']}")
    print(f"  Estado final: {parsed['final_cluster']}")
    print(f"{'─'*65}")


async def run_single(run_number: int, total: int, perturbation_idx: int,
                     condition: str, temperature: float) -> int:
    perturbation = PERTURBATIONS[perturbation_idx]
    print(f"\n  [{run_number}/{total}] Llamando al LLM... (temp={temperature})", end=" ", flush=True)

    parsed = call_llm(perturbation, temperature)
    run_id = get_next_run_id()
    json_path = save_run(run_id, perturbation_idx, perturbation,
                         condition, temperature, parsed)

    print(f"✓  ID={run_id}  síntesis={len(parsed['synthesis_chain'])}  "
          f"final='{parsed['final_cluster'][:40]}...'")
    return run_id


async def main():
    parser = argparse.ArgumentParser(
        description="LLM Baseline — Neural Ecology V2 comparison experiment"
    )
    parser.add_argument(
        "--perturbation", type=int, default=1,
        help="Índice de perturbación (0-9). Default: 1"
    )
    parser.add_argument(
        "--temp", choices=["low", "high"], default="low",
        help="Temperatura: low=0.10 (Condición A), high=0.90 (Condición B). Default: low"
    )
    parser.add_argument(
        "--runs", type=int, default=1,
        help="Cantidad de runs. Default: 1"
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Mostrar respuesta completa del LLM"
    )
    args = parser.parse_args()

    if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")

    temperature = TEMP_CONFIG[args.temp]
    perturbation = PERTURBATIONS[args.perturbation]
    condition_label = f"LLM_DIRECT_{'LOW' if args.temp == 'low' else 'HIGH'}"

    print(f"\n{'═'*65}")
    print(f"  LLM BASELINE — {args.runs} run(s)")
    print(f"  Condición  : {condition_label} (temperatura={temperature})")
    print(f"  Perturbación [{args.perturbation}]: {perturbation}")
    print(f"  Output dir : {BASELINE_DIR}/")
    print(f"{'═'*65}")

    run_ids = []
    for i in range(1, args.runs + 1):
        run_id = await run_single(
            i, args.runs,
            args.perturbation,
            args.temp,
            temperature,
        )
        run_ids.append(run_id)

    print(f"\n{'═'*65}")
    print(f"  COMPLETADO — {args.runs} runs")
    print(f"  IDs: {run_ids}")
    print(f"  CSV: {CSV_PATH}")
    print(f"  JSONs: {BASELINE_DIR}/")
    print(f"\n  Para evaluar:")
    print(f"  python distance_evaluator.py --auto_batch --runs_dir {BASELINE_DIR}")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    asyncio.run(main())