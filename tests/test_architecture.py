import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {"router": "router_app", "mailer": "mailer_app", "laya-adapter": "laya_adapter"}


@pytest.mark.parametrize("directory,package", PACKAGES.items())
def test_service_layer_and_domain_do_not_depend_on_frameworks_or_adapters(directory, package):
    allowed_stdlib = {"asyncio", "dataclasses", "enum", "typing", "uuid"}
    for name in ("domain.py", "ports.py", "service.py"):
        path = ROOT / "services" / directory / package / name
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] in allowed_stdlib for alias in node.names), (
                    path,
                    node.lineno,
                )
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.module in {"domain", "ports"}, (path, node.lineno)
                else:
                    assert node.module.split(".")[0] in allowed_stdlib, (path, node.lineno)


@pytest.mark.parametrize("directory,package", PACKAGES.items())
def test_no_service_imports_another_services_code(directory, package):
    forbidden = set(PACKAGES.values()) - {package}
    for path in (ROOT / "services" / directory).rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert all(alias.name.split(".")[0] not in forbidden for alias in node.names)
            if isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden
