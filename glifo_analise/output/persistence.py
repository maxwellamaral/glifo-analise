"""
Persistência de candidatos viáveis em disco (JSON).
"""
from __future__ import annotations

import json
import pathlib
from typing import List

from glifo_analise.config import CANDIDATES_FILE as _DEFAULT_CANDIDATES_FILE
from glifo_analise.models import ExtendedReport

# Variável de módulo — pode ser substituída via monkeypatch nos testes
CANDIDATES_FILE: pathlib.Path = _DEFAULT_CANDIDATES_FILE


def _save_candidates(viable: List[ExtendedReport]) -> None:
    """Serializa a lista de candidatos viáveis em JSON para uso futuro.

    Args:
        viable: Lista de ExtendedReport dos candidatos aprovados.
    """
    CANDIDATES_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = [
        {
            "rank":         idx + 1,
            "resolution":   list(er.resolution),
            "spacing_mm":   er.spacing_mm,
            "cell_w_mm":    er.cell_w_mm,
            "cell_h_mm":    er.cell_h_mm,
            "reading_mode": er.reading_mode,
            "seq_capacity": er.seq_capacity,
            "seq_in_range": er.seq_in_range,
            "coverage_pct": round(er.report.coverage_pct, 2),
        }
        for idx, er in enumerate(viable)
    ]
    CANDIDATES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_candidates() -> List[dict]:
    """Carrega a lista de candidatos salva em disco.

    Returns:
        Lista de dicts; lista vazia se o arquivo não existir ou for inválido.
    """
    if not CANDIDATES_FILE.exists():
        return []
    try:
        return json.loads(CANDIDATES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []
