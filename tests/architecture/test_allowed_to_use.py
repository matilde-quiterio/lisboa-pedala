import ast
from pathlib import Path


SRC = Path("src")


ALLOWED_DEPENDENCIES = {
    "src.viagens.desbloqueio": {
        "src.viagens.utilizadores",
        "src.estacoes.comunicacao_docas",
    },
    "src.estacoes.comunicacao_docas": {
        "src.viagens.viagens",
        "src.estacoes.consulta_estacoes",
    },
    "src.viagens.viagens": {
        "src.viagens.tarifacao",
        "src.viagens.cobranca",
        "src.viagens.faturacao",
    },
    "src.viagens.tarifacao": {
        "src.viagens.utilizadores",
    },
    "src.viagens.cobranca": {
        "src.viagens.utilizadores",
    },
    "src.viagens.historico": {
        "src.viagens.viagens",
    },
    "src.redistribuicao.planeamento_redistribuicao": {
        "src.estacoes.consulta_estacoes",
        "src.redistribuicao.planeamento_rotas",
    },
    "src.manutencao.telemetria": {
        "src.manutencao.manutencao",
    },
    "src.viagens.faturacao": set(),
    "src.estacoes.consulta_estacoes": set(),
    "src.redistribuicao.planeamento_rotas": set(),
    "src.manutencao.manutencao": set(),
    "src.reporting.relatorios_municipais": set(),
    "src.viagens.utilizadores": set(),
}


def component_from_path(path: Path) -> str | None:
    """
    Identifica o componente arquitetural de um ficheiro.

    Exemplos:
    src/viagens/desbloqueio.py
        -> src.viagens.desbloqueio

    src/viagens/desbloqueio/service.py
        -> src.viagens.desbloqueio
    """
    parts = path.with_suffix("").parts

    if len(parts) < 3:
        return None

    return ".".join(parts[:3])

def get_imports(path: Path) -> set[str]:
    """Obtém imports absolutos e relativos de módulos dentro de src."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()

    module_parts = list(path.with_suffix("").parts)

    # Package onde está o ficheiro atual
    if path.name == "__init__.py":
        package_parts = list(path.parent.parts)
    else:
        package_parts = module_parts[:-1]

    for node in ast.walk(tree):

        # Ex.: import src.viagens.utilizadores
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src."):
                    imports.add(alias.name)

        # Ex.:
        # from src.viagens.utilizadores import X
        # from .desbloqueio import X
        # from ..estacoes import X
        elif isinstance(node, ast.ImportFrom):

            # Import absoluto
            if node.level == 0:
                if node.module and node.module.startswith("src."):
                    imports.add(node.module)

            # Import relativo
            else:
                levels_up = node.level - 1

                if levels_up > len(package_parts):
                    continue

                base_parts = (
                    package_parts[: len(package_parts) - levels_up]
                    if levels_up > 0
                    else package_parts.copy()
                )

                if node.module:
                    full_parts = base_parts + node.module.split(".")
                    full_module = ".".join(full_parts)

                    if full_module.startswith("src."):
                        imports.add(full_module)

                # Ex.: from . import desbloqueio
                else:
                    for alias in node.names:
                        full_module = ".".join(base_parts + [alias.name])

                        if full_module.startswith("src."):
                            imports.add(full_module)

    return imports

def component_from_import(import_name: str) -> str | None:
    """
    Reduz um import ao componente arquitetural.

    Exemplo:
    src.viagens.utilizadores.service
        -> src.viagens.utilizadores
    """
    parts = import_name.split(".")

    if len(parts) < 3:
        return None

    return ".".join(parts[:3])


def test_allowed_to_use():
    errors = []

    for path in SRC.rglob("*.py"):
        if path.name == "__init__.py":
            continue

        source_component = component_from_path(path)

        if source_component not in ALLOWED_DEPENDENCIES:
            continue

        allowed = ALLOWED_DEPENDENCIES[source_component]

        for imported in get_imports(path):
            target_component = component_from_import(imported)

            if target_component is None:
                continue

            if target_component == source_component:
                continue

            if target_component not in allowed:
                errors.append(
                    f"{source_component} não pode depender de "
                    f"{target_component} ({path})"
                )

    assert not errors, "\n" + "\n".join(errors)