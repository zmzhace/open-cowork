from pathlib import Path


def test_requirements_allow_supported_pydantic_for_mcp() -> None:
    requirements_path = Path(__file__).resolve().parents[1] / "requirements.txt"
    requirements = requirements_path.read_text()

    assert "mcp>=1.1.2" in requirements
    assert "pydantic==2.6.0" not in requirements
