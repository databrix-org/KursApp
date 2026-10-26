#!/usr/bin/env python3
"""Offline structural documentation gate; archives/licenses/dependencies are excluded."""

import os, re, sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parent.parent
SKIP = {
    ".git",
    "node_modules",
    ".venv",
    ".next",
    ".turbo",
    "__pycache__",
    "legacy",
    "licenses",
    "test-results",
    "playwright-report",
    "artifacts",
    "backups",
}
errors = []
count = 0
for base, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in SKIP]
    path = Path(base)
    if "src" in dirs and path.relative_to(ROOT).parts[:1] in [("apps",), ("packages",)]:
        errors.append(f"{path}: owned src directory forbidden")
    for name in files:
        p = path / name
        if name == "CLAUDE.md":
            if not p.is_symlink() or os.readlink(p) != "AGENTS.md" or not p.exists():
                errors.append(f"{p}: CLAUDE.md must link to adjacent AGENTS.md")
            continue
        if p.suffix.lower() != ".md":
            continue
        count += 1
        text = p.read_text()
        if len(text.splitlines()) >= 150:
            errors.append(f"{p}: must be below 150 lines")
        if name == "AGENTS.md" and not (path / "CLAUDE.md").is_symlink():
            errors.append(f"{p}: missing CLAUDE.md symlink")
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = target.split(' "')[0].strip("<>")
            if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = unquote(target.split("#")[0])
            if target and not (path / target).exists():
                errors.append(f"{p}: broken link {target}")
required = [
    ROOT,
    ROOT / "apps/web",
    ROOT / "apps/backend",
    ROOT / "apps/backend/course",
]
required += list((ROOT / "packages").iterdir()) + list(
    (ROOT / "apps/web/modules").iterdir()
)
required += [
    ROOT / "apps/backend/course" / x
    for x in [
        "api",
        "services",
        "policies",
        "integrations",
        "integrations/storage",
        "integrations/notebooks",
        "tests",
    ]
]
for directory in required:
    if directory.is_dir() and not (directory / "AGENTS.md").is_file():
        errors.append(f"{directory}: missing scoped guide")
if errors:
    print("\n".join(errors))
    sys.exit(1)
print(
    f"Documentation gate passed: {count} Markdown files, links, guide coverage, symlinks, no-src boundaries"
)
