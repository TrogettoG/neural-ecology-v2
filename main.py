"""
main.py — Neural Ecology V2.

Una perturbación entra al campo.
Señales emergen. Neuronas nacen.
Algunas amplifican, otras inhiben, otras asocian.
Clusters se forman. Tensiones aparecen.
La profundidad emerge donde hay suficiente tensión.
Las neuronas mueren. El campo converge.
El resultado no fue planeado. Emergió.
"""

import asyncio
import os

from dotenv import load_dotenv
from google import genai

from field import CognitiveField
from orchestrator import Orchestrator
from dashboard import run_dashboard

load_dotenv()

# ── Experimento ────────────────────────────────────────────────────────────────
#
# Cambiá PERTURBATION para explorar distintos territorios conceptuales.
# No es una tarea. Es una tensión que el campo va a elaborar.

PERTURBATION = "¿Puede emerger consciencia en una red de agentes mínimos?"

# Otros experimentos posibles:
# PERTURBATION = "El problema del control en sistemas de IA autónomos"
# PERTURBATION = "Qué hace que una arquitectura de IA sea más eficiente que otra"
# PERTURBATION = "La relación entre inhibición y creatividad en sistemas cognitivos"
# PERTURBATION = "Cómo el olvido hace más inteligente a un sistema"


# ── Entry point ────────────────────────────────────────────────────────────────

async def main():
    # Configurar Gemini
    # google-genai acepta GEMINI_API_KEY nativamente — no remapear
    if not os.environ.get("GEMINI_API_KEY"):
        raise RuntimeError("Falta GEMINI_API_KEY en el .env")

    # Construir el campo y el orquestador
    field = CognitiveField(perturbation=PERTURBATION)
    orchestrator = Orchestrator(field)

    # Correr episodio y dashboard en paralelo
    episode_task = asyncio.create_task(orchestrator.run_episode())
    dashboard_task = asyncio.create_task(
        run_dashboard(field, orchestrator, episode_task)
    )

    await asyncio.gather(episode_task, dashboard_task)

    # Resultado final en consola
    print("\n" + "═" * 70)
    print("NEURAL ECOLOGY V2 — EPISODIO COMPLETADO")
    print("═" * 70)
    print(f"\nPerturbación: {PERTURBATION}\n")
    print(f"Motivo de cierre: {orchestrator.close_reason}\n")
    print(orchestrator.final_result or "Sin resultado.")
    print("\n" + "═" * 70)

    stats = orchestrator.get_stats()
    print(f"\nEstadísticas finales:")
    print(f"  Ciclos:          {stats['cycle']}")
    print(f"  Neuronas totales:{stats['total_neurons']}")
    print(f"  Energía restante:{stats['energy']:.1f}")
    print(f"  Clusters:        {stats['clusters']}")
    print(f"  Señales:         {stats['signals']}")
    print(f"  Tensiones:       {stats['tensions']}")


if __name__ == "__main__":
    asyncio.run(main())
