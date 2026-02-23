"""
glifo_analise.api.state
~~~~~~~~~~~~~~~~~~~~~~~
Estado global da sessão — thread-safe.
Compartilhado entre todas as rotas via injeção de dependência.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import List, Literal, Optional

from glifo_analise.models import ExtendedReport, GlyphProfile, ResolutionReport


TaskStatus = Literal["idle", "running", "done", "error"]


@dataclass
class AppState:
    """Estado mutável da sessão (análise + geração 3D).

    Todos os acessos a campos mutáveis devem ser feitos com o lock adquirido:

        with state.lock:
            state.profiles = ...
    """

    lock: threading.Lock = field(default_factory=threading.Lock)

    # Resultados da última análise
    profiles: List[GlyphProfile] = field(default_factory=list)
    reports: List[ResolutionReport] = field(default_factory=list)
    extended_reports: List[ExtendedReport] = field(default_factory=list)

    # Status de tarefas longas
    task_status: TaskStatus = "idle"
    task_id: Optional[str] = None
    task_error: Optional[str] = None

    def reset(self) -> None:
        """Limpa resultados anteriores mantendo o lock."""
        with self.lock:
            self.profiles = []
            self.reports = []
            self.extended_reports = []
            self.task_status = "idle"
            self.task_id = None
            self.task_error = None


# Instância singleton — importada por todos os routers
_state = AppState()


def get_state() -> AppState:
    """FastAPI dependency: retorna a instância global de AppState."""
    return _state
