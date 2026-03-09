from pathlib import Path

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version


EXPECTED_REQUIREMENTS = {
    "mcp": SpecifierSet(">=1.1.2"),
    "pydantic": SpecifierSet(">=2.11.0,<3"),
}


def _parse_requirements(lines: list[str]) -> dict[str, Requirement]:
    reqs: dict[str, Requirement] = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        requirement = Requirement(line)
        reqs[requirement.name] = requirement
    return reqs


def test_mcp_and_pydantic_requirements_match_supported_contract():
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    reqs = _parse_requirements(requirements_path.read_text().splitlines())

    assert reqs["mcp"].specifier == EXPECTED_REQUIREMENTS["mcp"]
    assert reqs["pydantic"].specifier == EXPECTED_REQUIREMENTS["pydantic"]
    assert Version("2.11.0") in reqs["pydantic"].specifier
    assert Version("2.12.5") in reqs["pydantic"].specifier
    assert Version("3.0.0") not in reqs["pydantic"].specifier
