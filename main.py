"""
main.py — Neural Ecology V2
v2_baseline_stable — congelado tras primera convergencia emergente verificada.

Uso:
  python main.py                                     # perturbación 5, 1 run
  python main.py --perturbation 1                    # perturbación 1, 1 run
  python main.py --perturbation 1 --runs 10          # 10 runs, clear Redis entre cada una
  python main.py --perturbation 1 --runs 3 --no-clear-redis  # sin limpiar Redis
"""

import argparse
import asyncio
import csv
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from field import CognitiveField
from orchestrator import Orchestrator
from dashboard import run_dashboard

load_dotenv()

# ── Banco de perturbaciones ────────────────────────────────────────
PERTURBATIONS = [
    "¿Puede emerger consciencia en una red de agentes mínimos?",
    "¿Qué es la identidad cuando el colectivo reemplaza al individuo?",
    "¿Qué se pierde y qué se gana cuando un sistema olvida?",
    "¿Cuándo la cooperación se convierte en conflicto y viceversa?",
    "¿Puede emerger propósito en un sistema sin intención original?",
    "¿En qué se diferencia la inteligencia distribuida de la inteligencia individual?",
]

# ── CLI args ───────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Neural Ecology V2")
parser.add_argument(
    "--perturbation", type=int, default=5,
    help="Índice de perturbación del banco (0-5). Default: 5"
)
parser.add_argument(
    "--runs", type=int, default=1,
    help="Cantidad de runs consecutivas. Default: 1"
)
parser.add_argument(
    "--no-clear-redis", action="store_true",
    help="No limpiar Redis entre runs (para runs de control con memoria acumulada)"
)
args = parser.parse_args()

PERTURBATION_INDEX = args.perturbation
PERTURBATION = PERTURBATIONS[PERTURBATION_INDEX]

CSV_PATH = Path("runs.csv")
RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)

CSV_HEADERS = [
    "id", "fecha", "hora", "perturbacion_idx", "perturbacion",
    "motivo_cierre", "ciclos", "energia_restante",
    "clusters", "senales", "tensiones", "neuronas_totales",
    "cluster_top_label", "cluster_top_C", "cluster_top_R",
    "tension_1", "tension_2", "tension_3",
    "synthesis_chain",
    "notas",
]


def build_synthesis_chain(field) -> list[dict]:
    """Extrae la cadena de síntesis ordenada por ciclo desde field.clusters."""
    chain = []
    for cid in field.synthesis_clusters:
        cluster = field.clusters.get(cid)
        if cluster:
            chain.append({
                "cycle": getattr(cluster, "synthesis_cycle", None),
                "label": cluster.label,
            })
    chain.sort(key=lambda x: (x["cycle"] is None, x["cycle"]))
    return chain


def save_run(orchestrator, field, run_id: int, perturbation_idx: int, perturbation: str):
    """Guarda resultados en runs.csv y en runs/run_NNN.json."""
    now = datetime.now()
    stats = orchestrator.get_stats()

    # Cluster dominante (mayor C)
    top_cluster = max(
        field.clusters.values(),
        key=lambda c: c.contradiction,
        default=None,
    ) if field.clusters else None

    # Top 3 tensiones por intensidad
    top_tensions = sorted(
        field.tensions, key=lambda t: t.intensity, reverse=True
    )[:3]
    tension_descs = [t.description for t in top_tensions]
    while len(tension_descs) < 3:
        tension_descs.append("")

    # Synthesis chain
    synthesis_chain = build_synthesis_chain(field)
    synthesis_chain_str = " | ".join(
        f"cy={e['cycle']:02d}:{e['label'][:40]}" if e["cycle"] is not None
        else f"cy=??:{e['label'][:40]}"
        for e in synthesis_chain
    )

    row = {
        "id":                  run_id,
        "fecha":               now.strftime("%Y-%m-%d"),
        "hora":                now.strftime("%H:%M:%S"),
        "perturbacion_idx":    perturbation_idx,
        "perturbacion":        perturbation,
        "motivo_cierre":       orchestrator.close_reason or "",
        "ciclos":              stats["cycle"],
        "energia_restante":    round(stats["energy"], 1),
        "clusters":            stats["clusters"],
        "senales":             stats["signals"],
        "tensiones":           stats["tensions"],
        "neuronas_totales":    stats["total_neurons"],
        "cluster_top_label":   top_cluster.label[:50] if top_cluster else "",
        "cluster_top_C":       round(top_cluster.contradiction, 2) if top_cluster else 0,
        "cluster_top_R":       round(top_cluster.resonance, 2) if top_cluster else 0,
        "tension_1":           tension_descs[0],
        "tension_2":           tension_descs[1],
        "tension_3":           tension_descs[2],
        "synthesis_chain":     synthesis_chain_str,
        "notas":               "",
    }

    # CSV
    file_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    # JSON detallado
    from config import MAX_CYCLES
    json_path = RUNS_DIR / f"run_{run_id:03d}.json"
    json_data = {
        # — Identidad del run
        "run_id":           run_id,
        "timestamp":        now.strftime("%Y-%m-%d %H:%M:%S"),
        # — Metadatos del experimento
        "experiment": {
            "perturbation_idx": perturbation_idx,
            "perturbation":     perturbation,
            "max_cycles":       MAX_CYCLES,
            "redis_cleared":    not args.no_clear_redis,
        },
        # — Resultado
        "close_reason":     orchestrator.close_reason or "",
        "cycles":           stats["cycle"],
        "energy":           round(stats["energy"], 1),
        "clusters":         stats["clusters"],
        "signals":          stats["signals"],
        "tensions":         stats["tensions"],
        "total_neurons":    stats["total_neurons"],
        "final_cluster":    top_cluster.label if top_cluster else "",
        # — Cadena de síntesis
        "synthesis_count":  len(synthesis_chain),
        "synthesis_chain":  synthesis_chain,
        # — Early snapshots ciclos 1–5
        "early_snapshots":  orchestrator.early_snapshots,
        # — Tensiones finales
        "top_tensions":     tension_descs,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"\n  → Corrida guardada: {CSV_PATH} (ID #{run_id}) + {json_path}")


def get_next_run_id() -> int:
    """Devuelve el próximo run_id basado en filas existentes en runs.csv."""
    if not CSV_PATH.exists():
        return 1
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        return max(1, sum(1 for _ in f))


# ── Entry point ────────────────────────────────────────────────────

async def run_single(run_number: int, total: int) -> int:
    """Ejecuta un episodio completo y retorna el run_id asignado."""
    print(f"\n{'═'*70}")
    print(f"RUN {run_number}/{total} — PERTURBACIÓN [{PERTURBATION_INDEX}]: {PERTURBATION}")
    print(f"{'═'*70}\n")

    field = CognitiveField(perturbation=PERTURBATION)
    orchestrator = Orchestrator(field)

    # Setup de memoria (necesario antes de clear_redis)
    await field.memory.consolidated.setup_redis()

    # Limpiar Redis si corresponde
    if not args.no_clear_redis:
        await field.memory.clear_redis()
        print("  [REDIS] Memoria limpiada para run independiente.")
    else:
        print("  [REDIS] Memoria conservada (run de control).")

    episode_task = asyncio.create_task(orchestrator.run_episode())
    dashboard_task = asyncio.create_task(
        run_dashboard(field, orchestrator, episode_task)
    )

    await asyncio.gather(episode_task, dashboard_task)

    print("\n" + "═" * 70)
    print(f"EPISODIO COMPLETADO — Motivo: {orchestrator.close_reason}")
    print("═" * 70)
    print(orchestrator.final_result or "Sin resultado.")

    run_id = get_next_run_id()
    save_run(orchestrator, field, run_id, PERTURBATION_INDEX, PERTURBATION)
    return run_id


async def main():
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")

    total = args.runs
    print(f"\nNeural Ecology V2 — {total} run(s) | perturbación {PERTURBATION_INDEX} | "
          f"Redis clear: {not args.no_clear_redis}")

    run_ids = []
    for i in range(1, total + 1):
        run_id = await run_single(i, total)
        run_ids.append(run_id)

    if total > 1:
        print(f"\n{'═'*70}")
        print(f"EXPERIMENTO COMPLETADO — {total} runs")
        print(f"IDs: {run_ids}")
        print(f"CSV: {CSV_PATH}")
        print(f"JSONs: {RUNS_DIR}/run_NNN.json")
        print(f"{'═'*70}")


if __name__ == "__main__":
    asyncio.run(main())