"""
main.py — Neural Ecology V2
v2_baseline_stable — congelado tras primera convergencia emergente verificada.

Última corrida validada:
  Perturbación: ¿Puede emerger consciencia en una red de agentes mínimos?
  Cierre: baja novedad + tensiones resueltas (ciclo 12)
  Tensiones: 3 activas con semántica real
  Clusters dominantes: inherentismo, autoorganización, emergencia

Para experimentar: cambiar PERTURBATION_INDEX (0-5) y correr.
Cada corrida se guarda automáticamente en runs.csv.
"""

import asyncio
import csv
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

PERTURBATION_INDEX = 4   # ← cambiar para rotar

PERTURBATION = PERTURBATIONS[PERTURBATION_INDEX]

CSV_PATH = Path("runs.csv")

CSV_HEADERS = [
    "id", "fecha", "hora", "perturbacion_idx", "perturbacion",
    "motivo_cierre", "ciclos", "energia_restante",
    "clusters", "senales", "tensiones", "neuronas_totales",
    "cluster_top_label", "cluster_top_C", "cluster_top_R",
    "tension_1", "tension_2", "tension_3",
    "notas",
]


def save_run(orchestrator, field, perturbation_idx: int, perturbation: str):
    """Guarda los resultados de la corrida en runs.csv."""
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

    # ID: contar filas existentes
    run_id = 1
    if CSV_PATH.exists():
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            run_id = max(1, sum(1 for _ in f))  # header ya incluido

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
        "notas":               "",
    }

    file_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    print(f"\n  → Corrida guardada en {CSV_PATH} (ID #{run_id})")


# ── Entry point ────────────────────────────────────────────────────

async def main():
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")

    print(f"\n{'═'*70}")
    print(f"PERTURBACIÓN [{PERTURBATION_INDEX}]: {PERTURBATION}")
    print(f"{'═'*70}\n")

    field = CognitiveField(perturbation=PERTURBATION)
    orchestrator = Orchestrator(field)

    episode_task = asyncio.create_task(orchestrator.run_episode())
    dashboard_task = asyncio.create_task(
        run_dashboard(field, orchestrator, episode_task)
    )

    await asyncio.gather(episode_task, dashboard_task)

    print("\n" + "═" * 70)
    print("NEURAL ECOLOGY V2 — EPISODIO COMPLETADO")
    print("═" * 70)
    print(f"\nPerturbación: {PERTURBATION}\n")
    print(f"Motivo de cierre: {orchestrator.close_reason}\n")
    print(orchestrator.final_result or "Sin resultado.")
    print("\n" + "═" * 70)

    stats = orchestrator.get_stats()
    print(f"\nEstadísticas finales:")
    print(f"  Ciclos:           {stats['cycle']}")
    print(f"  Neuronas totales: {stats['total_neurons']}")
    print(f"  Energía restante: {stats['energy']:.1f}")
    print(f"  Clusters:         {stats['clusters']}")
    print(f"  Señales:          {stats['signals']}")
    print(f"  Tensiones:        {stats['tensions']}")

    save_run(orchestrator, field, PERTURBATION_INDEX, PERTURBATION)


if __name__ == "__main__":
    asyncio.run(main())