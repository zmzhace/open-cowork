from pathlib import Path


EXPECTED_REQUIREMENTS = {
    "mcp": ">=1.1.2",
    "pydantic": ">=2.11.0,<3",
}


def _parse_requirements(lines: list[str]) -> dict[str, str]:
    reqs: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        for operator in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            if operator in line:
                name, spec = line.split(operator, 1)
                reqs[name.strip()] = f"{operator}{spec.strip()}"
                break
        else:
            reqs[line] = ""

    return reqs


def test_mcp_and_pydantic_requirements_match_supported_contract():
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    reqs = _parse_requirements(requirements_path.read_text().splitlines())

    assert reqs["mcp"] == EXPECTED_REQUIREMENTS["mcp"]
    assert reqs["pydantic"] == EXPECTED_REQUIREMENTS["pydantic"]
