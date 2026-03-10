"""
dashboard.py — El ojo humano sobre la ecología cognitiva.
Muestra en tiempo real: campo, clusters, señales, neuronas, energía.
"""

import asyncio
import time

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()

# Colores por tendencia
TENDENCY_COLORS = {
    "exploradora":   "cyan",
    "asociativa":    "green",
    "inhibidora":    "red",
    "correctiva":    "yellow",
    "consolidante":  "blue",
    "reactivadora":  "magenta",
    "sintetizadora": "bright_blue",
    "disolutiva":    "dim red",
}

# Colores por tipo de señal
SIGNAL_COLORS = {
    "exploratoria":  "cyan",
    "asociativa":    "green",
    "conflictiva":   "red",
    "correctiva":    "yellow",
    "consolidante":  "blue",
    "inhibitoria":   "dim red",
    "reactivadora":  "magenta",
    "terminal":      "dim white",
}


def _energy_bar(energy: float, max_energy: float = 80.0) -> str:
    pct = min(1.0, energy / max_energy)
    filled = int(pct * 20)
    bar = "█" * filled + "░" * (20 - filled)
    color = "green" if pct > 0.5 else "yellow" if pct > 0.25 else "red"
    return f"[{color}]{bar}[/] {energy:.1f}"


def build_header(field, orchestrator, elapsed: float) -> Panel:
    stats = field.get_stats()
    text = Text()
    text.append("🧬 NEURAL ECOLOGY V2", style="bold white")
    text.append("  |  ", style="dim")
    text.append(f"ciclo {stats['cycle']}", style="cyan")
    text.append("  energía ", style="dim")
    text.append(_energy_bar(stats["energy"]))
    text.append(f"  señales={stats['signals']}", style="dim")
    text.append(f"  clusters={stats['clusters']}", style="dim")
    text.append(f"  tensiones={stats['tensions']}", style="dim")
    text.append(f"  {elapsed:.0f}s", style="dim")
    return Panel(text, border_style="dim white", padding=(0, 1))


def build_neurons_panel(orchestrator) -> Panel:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim white",
                  padding=(0, 1))
    table.add_column("ID", width=7)
    table.add_column("Tendencia", width=13)
    table.add_column("Tipo", width=8)
    table.add_column("E", width=5)
    table.add_column("Age", width=4)
    table.add_column("Estado", width=10)
    table.add_column("Última acción", width=14)

    # Activas
    for n in list(orchestrator.active_neurons)[:12]:
        color = TENDENCY_COLORS.get(n.tendency.value, "white")
        e_color = "green" if n.energy > 1.0 else "yellow" if n.energy > 0.3 else "red"
        table.add_row(
            f"[bold cyan]{n.id}[/]",
            f"[{color}]{n.tendency.value[:12]}[/]",
            f"[dim]{'🔵' if n.depth_type == 'profunda' else '○'}[/]",
            f"[{e_color}]{n.energy:.1f}[/]",
            f"[dim]{n.age}[/]",
            f"[yellow]{n.state.value}[/]",
            f"[dim]{n.last_action.value[:12] if n.last_action else '-'}[/]",
        )

    # Últimas 3 muertas
    for n in list(reversed(orchestrator.dead_neurons))[:3]:
        table.add_row(
            f"[dim]{n.id}[/]",
            f"[dim]{n.tendency.value[:12]}[/]",
            "[dim]×[/]",
            "[dim]0[/]",
            f"[dim]{n.age}[/]",
            "[dim red]dead[/]",
            "[dim]-[/]",
        )

    total = len(orchestrator.active_neurons) + len(orchestrator.dead_neurons)
    title = (
        f"[bold]⚡ NEURONAS[/] "
        f"[cyan]{len(orchestrator.active_neurons)} vivas[/] "
        f"[dim]/ {len(orchestrator.dead_neurons)} muertas / {total} total[/]"
    )
    return Panel(table, title=title, border_style="cyan")


def build_clusters_panel(field) -> Panel:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim white",
                  padding=(0, 1))
    table.add_column("Label", width=25)
    table.add_column("C", width=5)
    table.add_column("R", width=5)
    table.add_column("N", width=5)
    table.add_column("P", width=4)
    table.add_column("Score", width=7)
    table.add_column("Estado", width=10)

    clusters = sorted(
        field.clusters.values(),
        key=lambda c: c.densify_score(),
        reverse=True
    )[:8]

    for c in clusters:
        score = c.densify_score()
        score_color = "bright_green" if score >= 0.68 else "yellow" if score >= 0.40 else "dim white"
        stable_str = "[green]estable[/]" if c.is_stable() else f"[dim]{c.stable_cycles}cy[/]"
        table.add_row(
            f"[white]{c.label[:24]}[/]",
            f"[{'red' if c.contradiction > 0.6 else 'yellow'}]{c.contradiction:.2f}[/]",
            f"[{'green' if c.resonance > 0.35 else 'dim'}]{c.resonance:.2f}[/]",
            f"[dim]{c.novelty:.2f}[/]",
            f"[dim]{c.persistence}[/]",
            f"[{score_color}]{score:.2f}[/]",
            stable_str,
        )

    title = f"[bold]🌐 CLUSTERS[/] [dim]({len(field.clusters)} activos)[/]"
    return Panel(table, title=title, border_style="blue")


def build_signals_panel(field) -> Panel:
    text = Text()
    signals = sorted(
        field.signals.values(),
        key=lambda s: s.intensity,
        reverse=True
    )[:15]

    if not signals:
        text.append("sin señales activas...", style="dim")
    else:
        for s in signals:
            color = SIGNAL_COLORS.get(s.type.value, "white")
            bar_len = int(s.intensity * 10)
            bar = "▪" * bar_len + "·" * (10 - bar_len)
            text.append(f"{s.id} ", style="dim cyan")
            text.append(f"[{bar}] ", style=color)
            text.append(f"{s.intensity:.2f} ", style=color)
            text.append(f"{s.type.value[:10]} ", style=f"dim {color}")
            text.append(f"{s.payload[:35]}\n", style="white")

    title = f"[bold]📡 SEÑALES[/] [dim]({len(field.signals)} activas)[/]"
    return Panel(text, title=title, border_style="yellow")


def build_events_panel(field) -> Panel:
    text = Text()
    events = list(reversed(field.event_log[-16:]))
    for event in events:
        if "[BORN]" in event:
            text.append(event + "\n", style="green")
        elif "[DEAD]" in event:
            text.append(event + "\n", style="dim red")
        elif "[DENSIFY]" in event:
            text.append(event + "\n", style="bold magenta")
        elif "[TENSION]" in event:
            text.append(event + "\n", style="yellow")
        elif "[CLUSTER]" in event:
            text.append(event + "\n", style="blue")
        elif "[CLOSE]" in event:
            text.append(event + "\n", style="bold red")
        elif "[TICK]" in event:
            text.append(event + "\n", style="dim white")
        else:
            text.append(event + "\n", style="dim")

    return Panel(text, title="[bold]📋 EVENTOS[/]", border_style="dim white")


def build_result_panel(result: str | None, close_reason: str | None) -> Panel:
    if not result:
        content = Text("⏳ El episodio está corriendo...", style="dim yellow")
    else:
        content = Text(result[:900], style="white")

    title = (
        f"[bold green]✨ RESULTADO[/]"
        + (f" [dim]— {close_reason}[/]" if close_reason else "")
    )
    return Panel(content, title=title, border_style="green")


def build_layout(field, orchestrator, elapsed: float) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main", ratio=3),
        Layout(name="bottom", ratio=2),
    )
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=3),
    )
    layout["left"].split_column(
        Layout(name="neurons"),
        Layout(name="clusters"),
    )
    layout["bottom"].split_row(
        Layout(name="signals", ratio=2),
        Layout(name="result", ratio=3),
    )

    layout["header"].update(build_header(field, orchestrator, elapsed))
    layout["neurons"].update(build_neurons_panel(orchestrator))
    layout["clusters"].update(build_clusters_panel(field))
    layout["right"].update(build_events_panel(field))
    layout["signals"].update(build_signals_panel(field))
    layout["bottom"]["result"].update(
        build_result_panel(orchestrator.final_result, orchestrator.close_reason)
    )

    return layout


async def run_dashboard(field, orchestrator, episode_task: asyncio.Task):
    start = time.time()
    with Live(console=console, refresh_per_second=2, screen=True) as live:
        while not episode_task.done():
            elapsed = time.time() - start
            live.update(build_layout(field, orchestrator, elapsed))
            await asyncio.sleep(0.5)

        elapsed = time.time() - start
        live.update(build_layout(field, orchestrator, elapsed))
        await asyncio.sleep(3)
