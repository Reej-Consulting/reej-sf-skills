#!/usr/bin/env python3
"""Vérifie la cohérence du marketplace et des plugins (équivalent local de `claude plugin validate`)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
errors: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


market_path = ROOT / ".claude-plugin" / "marketplace.json"
market = json.loads(market_path.read_text(encoding="utf-8"))
for key in ("name", "owner", "plugins"):
    if key not in market:
        err(f"marketplace.json : champ `{key}` manquant")

seen_skills: dict[str, str] = {}
for entry in market.get("plugins", []):
    name, source = entry.get("name"), entry.get("source")
    if not name or not KEBAB.match(name):
        err(f"marketplace.json : nom de plugin invalide `{name}`")
    pdir = ROOT / source
    manifest = pdir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        err(f"{name} : plugin.json manquant ({manifest})")
        continue
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if m.get("name") != name:
        err(f"{name} : plugin.json.name = `{m.get('name')}` ≠ marketplace")
    if not re.match(r"^\d+\.\d+\.\d+$", str(m.get("version", ""))):
        err(f"{name} : version non semver `{m.get('version')}`")
    skills_dir = pdir / "skills"
    if not skills_dir.is_dir():
        err(f"{name} : dossier skills/ manquant")
        continue
    n = 0
    for s in sorted(skills_dir.iterdir()):
        if not s.is_dir():
            continue
        if not (s / "SKILL.md").is_file():
            err(f"{name}/{s.name} : SKILL.md manquant")
            continue
        text = (s / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            err(f"{name}/{s.name} : SKILL.md sans frontmatter")
        if s.name in seen_skills:
            err(f"{s.name} : présent dans {seen_skills[s.name]} ET {name}")
        seen_skills[s.name] = name
        n += 1
    print(f"OK  {name}: {n} skills")

state = json.loads((ROOT / "SYNC_STATE.json").read_text(encoding="utf-8"))
if set(state["skills"]) != set(seen_skills):
    err("SYNC_STATE.json ne correspond pas aux skills présents dans plugins/")

if errors:
    print("\n".join(f"ERREUR  {e}" for e in errors), file=sys.stderr)
    sys.exit(1)
print(f"\nMarketplace `{market['name']}` valide — {len(seen_skills)} skills dans {len(market['plugins'])} plugins.")
