#!/usr/bin/env python3
"""Vérifie la cohérence du marketplace et des plugins — miroir Salesforce (plugins/) et maison (reej-plugins/).

Usage :
    python3 scripts/validate.py                    # structure seule
    python3 scripts/validate.py --base origin/main # + exige un incrément de version pour tout plugin maison modifié
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
errors: list[str] = []

ap = argparse.ArgumentParser()
ap.add_argument("--base", help="ref git de la branche cible (ex. origin/main) : tout plugin maison modifié depuis doit avoir une version supérieure")
args = ap.parse_args()


def err(msg: str) -> None:
    errors.append(msg)


def git(*cmd: str) -> str:
    return subprocess.run(["git", *cmd], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True).stdout


def version_key(v: str) -> tuple[int, ...]:
    return tuple(int(x) for x in v.split("."))


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for key in ("name", "description"):
            km = re.search(rf"^{key}:\s*(.+?)\s*$", m.group(1), re.M)
            if km:
                out[key] = km.group(1).strip().strip('"').strip("'")
    return out


market_path = ROOT / ".claude-plugin" / "marketplace.json"
market = json.loads(market_path.read_text(encoding="utf-8"))
for key in ("name", "owner", "plugins"):
    if key not in market:
        err(f"marketplace.json : champ `{key}` manquant")

seen_skills: dict[str, str] = {}
listed = {e.get("name") for e in market.get("plugins", [])}

for entry in market.get("plugins", []):
    name, source = entry.get("name"), entry.get("source")
    if not name or not KEBAB.match(name):
        err(f"marketplace.json : nom de plugin invalide `{name}`")
        continue
    if not (name.startswith("sf-") or name.startswith("reej-")):
        err(f"{name} : préfixe attendu `sf-` (miroir) ou `reej-` (maison)")
    is_reej = name.startswith("reej-")
    expected_root = "./reej-plugins/" if is_reej else "./plugins/"
    if not str(source).startswith(expected_root):
        err(f"{name} : source `{source}` devrait être sous {expected_root}")
    pdir = ROOT / source
    manifest = pdir / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        err(f"{name} : plugin.json manquant ({manifest})")
        continue
    m = json.loads(manifest.read_text(encoding="utf-8"))
    if m.get("name") != name:
        err(f"{name} : plugin.json.name = `{m.get('name')}` ≠ marketplace")
    if not SEMVER.match(str(m.get("version", ""))):
        err(f"{name} : version non semver `{m.get('version')}`")
    if is_reej and not m.get("description"):
        err(f"{name} : description manquante dans plugin.json")
    skills_dir = pdir / "skills"
    if not skills_dir.is_dir():
        err(f"{name} : dossier skills/ manquant")
        continue
    n = 0
    for s in sorted(skills_dir.iterdir()):
        if not s.is_dir():
            continue
        if not KEBAB.match(s.name):
            err(f"{name}/{s.name} : nom de skill non kebab-case")
        if is_reej and not s.name.startswith("reej-"):
            err(f"{name}/{s.name} : un skill maison doit commencer par `reej-`")
        skill_md = s / "SKILL.md"
        if not skill_md.is_file():
            err(f"{name}/{s.name} : SKILL.md manquant")
            continue
        text = skill_md.read_text(encoding="utf-8", errors="replace")
        fm = frontmatter(text)
        if not text.startswith("---") or "name" not in fm or "description" not in fm:
            err(f"{name}/{s.name} : frontmatter incomplet (name + description requis)")
        elif fm["name"] != s.name:
            err(f"{name}/{s.name} : frontmatter name = `{fm['name']}` ≠ nom du dossier")
        if is_reej and "description" in fm and len(fm["description"]) < 80:
            err(f"{name}/{s.name} : description trop courte ({len(fm['description'])} car.) — dire QUAND l'utiliser et quand NE PAS l'utiliser")
        if is_reej:  # tout le dossier du skill, pas seulement SKILL.md : gabarits et références partent aussi chez l'utilisateur
            for f in sorted(s.rglob("*")):
                if not f.is_file():
                    continue
                try:
                    content = f.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue  # binaire (image, police…)
                if "TODO" in content:
                    err(f"{name}/{s.name} : TODO restant dans {f.relative_to(s).as_posix()}")
        if s.name in seen_skills:
            err(f"{s.name} : présent dans {seen_skills[s.name]} ET {name}")
        seen_skills[s.name] = name
        n += 1
    print(f"OK  {name}: {n} skills")

# Plugins maison présents sur disque mais absents du marketplace (oubli de régénération)
reej_dir = ROOT / "reej-plugins"
if reej_dir.is_dir():
    for pdir in reej_dir.iterdir():
        if (pdir / ".claude-plugin" / "plugin.json").is_file() and pdir.name not in listed:
            err(f"reej-plugins/{pdir.name} existe mais n'est pas dans marketplace.json — relancer scripts/sync.py")

# Plugin maison modifié sans incrément de version : les postes déjà installés ne verraient jamais le changement
# (Claude Code met chaque plugin en cache dans un dossier nommé d'après sa version).
if args.base and reej_dir.is_dir():
    try:
        merge_base = git("merge-base", args.base, "HEAD").strip()
    except subprocess.CalledProcessError:
        err(f"--base {args.base} : ref introuvable (en CI, checkout avec fetch-depth: 0)")
        merge_base = None
    for pdir in sorted(reej_dir.iterdir()) if merge_base else []:
        manifest = pdir / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            continue
        rel = pdir.relative_to(ROOT).as_posix()
        # diff contre l'arbre de travail (et non HEAD) : couvre aussi les modifications non commitées en local
        if not (git("diff", "--name-only", merge_base, "--", rel).strip()
                or git("ls-files", "--others", "--exclude-standard", "--", rel).strip()):
            continue
        try:
            old_v = json.loads(git("show", f"{args.base}:{rel}/.claude-plugin/plugin.json")).get("version", "")
        except subprocess.CalledProcessError:
            continue  # nouveau plugin : rien à comparer
        new_v = json.loads(manifest.read_text(encoding="utf-8")).get("version", "")
        if SEMVER.match(old_v) and SEMVER.match(new_v) and version_key(new_v) <= version_key(old_v):
            err(f"{pdir.name} : modifié sans incrément de version ({new_v}, déjà {old_v} sur {args.base}) — incrémenter `version` dans plugin.json")

state = json.loads((ROOT / "SYNC_STATE.json").read_text(encoding="utf-8"))
mirror_skills = {s for s, p in seen_skills.items() if p.startswith("sf-")}
if set(state["skills"]) != mirror_skills:
    err("SYNC_STATE.json ne correspond pas aux skills présents dans plugins/")

if errors:
    print("\n".join(f"ERREUR  {e}" for e in errors), file=sys.stderr)
    sys.exit(1)
print(f"\nMarketplace `{market['name']}` valide — {len(seen_skills)} skills dans {len(market['plugins'])} plugins.")
