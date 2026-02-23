"""
[DEPRECADO] Interface NiceGUI — substituída por FastAPI + Vue 3.

Este módulo existe apenas como referência histórica.
A interface gráfica atual é servida pelo backend FastAPI em:

    uv run glifo-gui   →   http://localhost:8080

O código legado da CLI monolítica está em main_legacy.py.
Os assets estáticos do viewer 3D (Three.js) estão em:

    glifo_analise/gui/static/viewer3d.html  (reutilizado pelo frontend Vue 3)
"""


def run() -> None:
    """Ponto de entrada legado — redireciona para o servidor FastAPI."""
    import sys

    print(
        "[AVISO] glifo_analise.gui.app foi substituído por glifo_analise.api.main.\n"
        "        Execute: uv run glifo-gui\n"
        "        O servidor FastAPI será iniciado em http://localhost:8080",
        file=sys.stderr,
    )
    from glifo_analise.api.main import run as _run
    _run()
