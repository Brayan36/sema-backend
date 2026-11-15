import json
from pathlib import Path


def test_user_management_contracts_are_valid_json():
    contracts = Path(__file__).parents[1] / "data" / "contracts"
    files = sorted(contracts.glob("*.json"))

    assert {file.stem for file in files} == {"usuarios", "roles", "permisos", "asignaciones"}
    for file in files:
        document = json.loads(file.read_text(encoding="utf-8"))
        assert document["resource"]
