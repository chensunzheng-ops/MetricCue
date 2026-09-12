import re
import sys
from pathlib import Path

import yaml


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "skills/metriccue")
    skill = root / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3 or parts[0].strip() or not parts[2].strip():
        raise SystemExit("Skill must contain closed YAML frontmatter and a body")
    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        raise SystemExit(f"Invalid Skill frontmatter YAML: {exc}") from exc
    if not isinstance(frontmatter, dict) or set(frontmatter) != {"name", "description"}:
        raise SystemExit("Skill frontmatter must contain only name and description")
    if frontmatter["name"] != "metriccue":
        raise SystemExit("Skill name must be metriccue")
    description = frontmatter["description"]
    if not isinstance(description, str) or len(description.strip()) < 20:
        raise SystemExit("Skill description is missing or too short")
    references = re.findall(r"\]\((references/[^)]+)\)", text)
    missing = [name for name in references if not (root / name).is_file()]
    if missing:
        raise SystemExit(f"Missing Skill references: {missing}")
    print("MetricCue Skill is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
