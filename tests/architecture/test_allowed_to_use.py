import ast
from pathlib import Path


SRC = Path("src")


# Dependências permitidas entre componentes.
# Tudo o que não está aqui é proibido.
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

    "src.viagens.faturacao": {
        "src.viagens.viagens",
        "src.viagens.cobranca",
    },

    "src.redistribuicao.planeamento_redistribuicao": {
        "src.estacoes.consulta_estacoes",
        "src.redistribuicao.planeamento_rotas",
    },

    "src.manutencao.telemetria": {
        "src.manutencao.manutencao",
    },

    "src.estacoes.consulta_estacoes": set(),
    "src.redistribuicao.planeamento_rotas": set(),
    "src.manutencao.manutencao": set(),
    "src.reporting.relatorios_municipais": set(),
    "src.viagens.utilizadores": set(),
}


def path_to_module(path: Path) -> str:
    """Converte src/viagens/desbloqueio.py em src.viagens.desbloqueio."""
    return ".".join(path.with_suffix("").parts)


def get_imports(path: Path) -> set[str]:
    """Obtém os módulos src.* importados diretamente por um ficheiro Python."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src."):
                    imports.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("src."):
                imports.add(node.module)

    return imports


def component_from_import(import_name: str) -> str | None:
    """
    Reduz um import ao componente arquitetural.

    Ex.:
    src.viagens.utilizadores.servico
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

        source_component = path_to_module(path)

        if source_component not in ALLOWED_DEPENDENCIES:
            continue

        allowed = ALLOWED_DEPENDENCIES[source_component]

        for imported in get_imports(path):
            target_component = component_from_import(imported)

            if target_component is None:
                continue

            # Import do próprio componente é sempre permitido.
            if target_component == source_component:
                continue

            if target_component not in allowed:
                errors.append(
                    f"{source_component} não pode depender de "
                    f"{target_component}"
                )

    assert not errors, "\n" + "\n".join(errors)