import tomllib
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_release_candidate_has_complete_public_artifact_set() -> None:
    required = (
        "README.md",
        "README.en.md",
        "LICENSE",
        "CHANGELOG.md",
        "docs/data-contract.md",
        "docs/methodology.md",
        "docs/privacy.md",
        "docs/contributing.md",
        "docs/user-test-protocol.md",
        "docs/portfolio.md",
        "docs/assets/metriccue-wechat-preview.svg",
        "examples/synthetic_wechat/README.md",
        "examples/synthetic_wechat/generate.py",
        "examples/synthetic_wechat/metriccue.yaml",
        "examples/synthetic_wechat/performance.csv",
        "examples/synthetic_wechat/content.csv",
        "examples/synthetic_wechat/production.csv",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/bug.yml",
        ".github/ISSUE_TEMPLATE/platform-mapping.yml",
        ".github/ISSUE_TEMPLATE/diagnostic-rule.yml",
    )

    missing_or_empty = [
        path for path in required if not (ROOT / path).is_file() or not (ROOT / path).stat().st_size
    ]
    assert missing_or_empty == []


def test_package_identifies_the_validated_release_stage() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert metadata["project"]["version"] == "0.1.0rc1"
    assert "/work" in metadata["tool"]["hatch"]["build"]["exclude"]
