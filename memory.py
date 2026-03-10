"""
memory.py — Memoria del sistema.

Dos tipos con comportamientos distintos:
- Reciente:     sliding window del episodio actual
- Consolidada:  patrones entre episodios, decaen gradualmente
"""

import json
import os
from collections import deque
from typing import Optional

from models import Trace
from config import (
    MEMORY_RECENT_WINDOW,
    MEMORY_CONSOLIDATED_DECAY,
    MEMORY_TRANSFER_MIN_CYCLES,
    MEMORY_TRANSFER_NOVELTY_MIN,
    MEMORY_TRANSFER_SIMILARITY_MAX,
    R_CONSOLIDATED_BOOST,
)

try:
    from upstash_redis.asyncio import Redis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


class RecentMemory:
    """
    Sliding window del episodio actual.
    Accesible para todas las neuronas (costo 0.05).
    Se limpia al cerrar el episodio.
    """

    def __init__(self):
        self._traces: deque[Trace] = deque(maxlen=MEMORY_RECENT_WINDOW)

    def add(self, trace: Trace):
        self._traces.appendleft(trace)

    def get_all(self) -> list[Trace]:
        return list(self._traces)

    def get_relevant(self, cluster_label: str, top_k: int = 3) -> list[Trace]:
        """Devuelve las trazas más relevantes para un cluster dado."""
        scored = []
        for t in self._traces:
            score = 0.0
            # Similitud simple por palabras clave
            label_words = set(cluster_label.lower().split())
            trace_words = set(t.cluster_label.lower().split())
            overlap = len(label_words & trace_words)
            if overlap > 0:
                score = overlap / max(len(label_words), len(trace_words))
            scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k] if _ > 0]

    def clear(self):
        self._traces.clear()

    def summary(self, top_k: int = 3) -> str:
        """Resumen textual para incluir en prompts de neuronas."""
        traces = list(self._traces)[:top_k]
        if not traces:
            return "Sin trazas recientes."
        parts = []
        for t in traces:
            signals = ", ".join(t.signal_payloads[:2])
            parts.append(f"[{t.cluster_label}]: {signals}")
        return " | ".join(parts)

    def __len__(self):
        return len(self._traces)


class ConsolidatedMemory:
    """
    Patrones que persisten entre episodios.
    Solo accesible para neuronas profundas y reactivadoras (costo 0.20).
    Decae 0.80 por episodio sin refuerzo.
    """

    def __init__(self):
        self._patterns: list[Trace] = []
        self._redis: Optional[object] = None
        self._redis_key = "neurona_v2:consolidated"
        self._loaded = False

    async def setup_redis(self):
        """Conecta a Upstash si hay credenciales disponibles."""
        if not _REDIS_AVAILABLE:
            return
        url = os.environ.get("UPSTASH_REDIS_REST_URL")
        token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
        if url and token:
            self._redis = Redis(url=url, token=token)

    async def load(self):
        """Carga patrones persistidos de episodios anteriores."""
        if self._loaded:
            return
        self._loaded = True
        if self._redis:
            try:
                raw = await self._redis.get(self._redis_key)
                if raw:
                    data = json.loads(raw)
                    self._patterns = [Trace(**d) for d in data]
            except Exception:
                pass

    async def save(self):
        """Persiste patrones a Redis."""
        if self._redis:
            try:
                data = [t.__dict__ for t in self._patterns]
                await self._redis.set(self._redis_key, json.dumps(data))
            except Exception:
                pass

    def add(self, trace: Trace):
        """Agrega un patrón nuevo."""
        # Evitar duplicados muy similares
        for existing in self._patterns:
            similarity = self._similarity(existing.cluster_label, trace.cluster_label)
            if similarity > MEMORY_TRANSFER_SIMILARITY_MAX:
                existing.weight = min(1.0, existing.weight + 0.1)
                return
        self._patterns.append(trace)

    def decay_episode(self):
        """Aplica decaimiento por episodio. Elimina patrones con peso < 0.1."""
        for p in self._patterns:
            p.weight *= MEMORY_CONSOLIDATED_DECAY
        self._patterns = [p for p in self._patterns if p.weight >= 0.10]

    def get_relevant(self, cluster_label: str, top_k: int = 3) -> list[Trace]:
        scored = []
        for t in self._patterns:
            sim = self._similarity(cluster_label, t.cluster_label)
            scored.append((sim * t.weight, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [t for _, t in scored[:top_k] if _ > 0.1]

    def resonance_boost(self, cluster_label: str) -> float:
        """
        Devuelve R_CONSOLIDATED_BOOST si hay un patrón consolidado
        con similitud > 0.50 al cluster actual.
        """
        for t in self._patterns:
            if self._similarity(cluster_label, t.cluster_label) > 0.50:
                return R_CONSOLIDATED_BOOST
        return 0.0

    def summary(self, top_k: int = 3) -> str:
        top = sorted(self._patterns, key=lambda t: t.weight, reverse=True)[:top_k]
        if not top:
            return "Sin patrones consolidados."
        parts = [f"[{t.cluster_label} w={t.weight:.1f}]" for t in top]
        return " | ".join(parts)

    def _similarity(self, a: str, b: str) -> float:
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / max(len(words_a), len(words_b))

    def __len__(self):
        return len(self._patterns)


class Memory:
    """
    Fachada unificada de los dos tipos de memoria.
    El campo usa esta clase directamente.
    """

    def __init__(self):
        self.recent = RecentMemory()
        self.consolidated = ConsolidatedMemory()

    async def setup(self):
        await self.consolidated.setup_redis()
        await self.consolidated.load()

    def transfer_to_consolidated(self, clusters: dict, signals: dict, cycle: int):
        """
        Al cierre del episodio: transfiere clusters que merecen persistir.
        Reglas de la spec:
        - Densificado al menos 1 vez
        - Activo >= MEMORY_TRANSFER_MIN_CYCLES ciclos
        - Novedad final > MEMORY_TRANSFER_NOVELTY_MIN
        """
        for cluster in clusters.values():
            if cluster.densified_count < 1:
                continue
            if (cycle - cluster.born_at_cycle) < MEMORY_TRANSFER_MIN_CYCLES:
                continue
            if cluster.novelty < MEMORY_TRANSFER_NOVELTY_MIN:
                continue
            payloads = [
                signals[sid].payload for sid in cluster.signal_ids
                if sid in signals and signals[sid].payload
            ][:5]
            trace = Trace(
                cluster_label=cluster.label,
                signal_payloads=payloads,
                contradiction=cluster.contradiction,
                novelty=cluster.novelty,
                cycle=cycle,
                weight=1.0,
            )
            self.consolidated.add(trace)

    async def close_episode(self, clusters: dict, signals: dict, cycle: int):
        """Ejecuta transferencia, decaimiento y persistencia al cerrar."""
        self.transfer_to_consolidated(clusters, signals, cycle)
        self.consolidated.decay_episode()
        await self.consolidated.save()
        self.recent.clear()
