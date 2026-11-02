import ast
from pathlib import Path


SRC = Path("src")


def component_from_path(path: Path) -> str | None:
    parts = path.with_suffix("").parts

    if len(parts) < 3:
        return None

    return ".".join(parts[:3])


def get_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = set()

    module_parts = list(path.with_suffix("").parts)
    package_parts = module_parts[:-1]

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("src."):
                    imports.add(alias.name)

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
                    full_module = ".".join(
                        base_parts + node.module.split(".")
                    )

                    if full_module.startswith("src."):
                        imports.add(full_module)

                else:
                    for alias in node.names:
                        full_module = ".".join(
                            base_parts + [alias.name]
                        )

                        if full_module.startswith("src."):
                            imports.add(full_module)

    return imports


def component_from_import(import_name: str) -> str | None:
    parts = import_name.split(".")

    if len(parts) < 3:
        return None

    return ".".join(parts[:3])


def build_dependency_graph() -> dict[str, set[str]]:
    graph = {}

    for path in SRC.rglob("*.py"):

        if path.name == "__init__.py":
            continue

        source_component = component_from_path(path)

        if source_component is None:
            continue

        graph.setdefault(source_component, set())

        for imported in get_imports(path):
            target_component = component_from_import(imported)

            if target_component is None:
                continue

            if target_component != source_component:
                graph[source_component].add(target_component)

    return graph


def find_cycle(graph: dict[str, set[str]]):
    visited = set()
    current_path = set()
    path = []

    def visit(node):
        if node in current_path:
            index = path.index(node)
            return path[index:] + [node]

        if node in visited:
            return None

        current_path.add(node)
        path.append(node)

        for dependency in graph.get(node, set()):
            cycle = visit(dependency)

            if cycle:
                return cycle

        path.pop()
        current_path.remove(node)
        visited.add(node)

        return None

    for node in graph:
        cycle = visit(node)

        if cycle:
            return cycle

    return None


def test_no_circular_dependencies():
    graph = build_dependency_graph()

    cycle = find_cycle(graph)

    assert cycle is None, (
        "Dependência circular encontrada: "
        + " -> ".join(cycle)
    )