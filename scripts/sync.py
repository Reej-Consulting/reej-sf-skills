#!/usr/bin/env python3
"""
Synchronise les skills Salesforce (forcedotcom/sf-skills) dans le marketplace Reej.

- Clone (shallow) le repo upstream
- Range chaque skill de `skills/` dans un plugin par domaine (voir DOMAINS)
- Réécrit les liens relatifs `../<skill>/...` qui traversent un plugin
- Régénère `plugins/<plugin>/.claude-plugin/plugin.json` et `.claude-plugin/marketplace.json`
- Écrit `SYNC_STATE.json` (commit upstream, inventaire) et imprime un résumé des changements

Usage :
    python3 scripts/sync.py                 # synchro complète
    python3 scripts/sync.py --dry-run       # affiche ce qui changerait, n'écrit rien
    python3 scripts/sync.py --upstream /chemin/local   # utilise un clone déjà présent
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UPSTREAM_URL = "https://github.com/forcedotcom/sf-skills.git"
ROOT = Path(__file__).resolve().parent.parent
PLUGINS_DIR = ROOT / "plugins"
MARKETPLACE_FILE = ROOT / ".claude-plugin" / "marketplace.json"
STATE_FILE = ROOT / "SYNC_STATE.json"
PLUGIN_PREFIX = "sf-"
LONG_PATH_WARN = 170  # longueur relative au-delà de laquelle un chemin est signalé (Windows MAX_PATH = 260)

# --------------------------------------------------------------------------
# Répartition par domaine. L'ordre compte : la première règle qui matche gagne.
# Un skill non couvert tombe dans DEFAULT_DOMAIN et est signalé dans le résumé.
# --------------------------------------------------------------------------
DOMAINS: dict[str, dict] = {
    "agentforce": {
        "displayName": "Salesforce — Agentforce & Data 360",
        "description": "Agentforce (Agent Script, tests, observabilité, architecture, migration Einstein Bots), Data 360 / Data Cloud, Models API et canaux Agentforce.",
        "keywords": ["salesforce", "agentforce", "agent script", "data cloud", "data 360", "einstein bots"],
        "match": [
            r"^agentforce-", r"^data360-", r"^platform-models-api-",
            r"^platform-agentsetup-", r"^platform-tracing-agentforce-",
            r"^sales-agentforce-", r"^service-agentforce-",
        ],
    },
    "platform": {
        "displayName": "Salesforce — Platform & Apex",
        "description": "Socle plateforme : métadonnées (objets, champs, permissions, sharing), Apex, Flow, SOQL, déploiement/retrieve, Code Analyzer, SLDS, documentation Salesforce.",
        "keywords": ["salesforce", "apex", "flow", "soql", "metadata", "deploy", "slds"],
        "match": [r"^platform-", r"^automation-flow-", r"^design-systems-", r"^external-", r"^dx-code-", r"^dx-apexguru-"],
    },
    "devops": {
        "displayName": "Salesforce — DevOps & Orgs",
        "description": "DevOps Center, pipelines, gestion des orgs (scratch, sandbox, Dev Hub, trials), packaging, post-copy sandbox.",
        "keywords": ["salesforce", "devops", "sandbox", "scratch org", "dev hub", "packaging"],
        "match": [r"^dx-", r"^automation-sandbox-"],
    },
    "service": {
        "displayName": "Salesforce — Service Cloud",
        "description": "Service Cloud : Omni-Channel, Digital Engagement (WhatsApp, messaging), ITSM, Email-to-Case, Help Agent, portails.",
        "keywords": ["salesforce", "service cloud", "omni-channel", "digital engagement", "itsm", "messaging"],
        "match": [r"^service-"],
    },
    "experience": {
        "displayName": "Salesforce — Experience, LWC & Mobile",
        "description": "Experience Cloud, LWC, LDS/GraphQL, UI bundles React, CMS, Commerce B2B, Mobile SDK.",
        "keywords": ["salesforce", "lwc", "experience cloud", "react", "cms", "commerce", "mobile"],
        "match": [r"^experience-", r"^commerce-", r"^mobile-"],
    },
    "integration": {
        "displayName": "Salesforce — Integration & OmniStudio",
        "description": "Connected Apps, Named Credentials, Change Data Capture, Platform Events, OmniStudio (OmniScript, FlexCards, Integration Procedures, DataRaptor).",
        "keywords": ["salesforce", "integration", "connected app", "cdc", "platform events", "omnistudio"],
        "match": [r"^integration-", r"^omnistudio-"],
    },
    "industries": {
        "displayName": "Salesforce — Industries",
        "description": "Field Service, Consumer Goods, Education Cloud, Life Sciences.",
        "keywords": ["salesforce", "field service", "consumer goods", "education cloud", "life sciences"],
        "match": [r"^field-service-", r"^consumer-goods-", r"^education-cloud-", r"^life-sciences-"],
    },
}
DEFAULT_DOMAIN = "platform"

# Skills qui n'existent QUE dans les plugins officiels (pas dans skills/ à la racine)
# et qui sont autonomes (aucune dépendance aux scripts/hooks internes de ce plugin).
# Les autres (destructive-deploy, lsp-integrate, capability-search, environment-validate,
# project-create, deploy-validate, quick-deploy) dépendent de l'outillage du plugin
# `salesforce-development` et ne sont volontairement pas repris.
EXTRA_SKILLS: dict[str, str] = {
    "plugins/builder/salesforce-development/skills/platform-apex-anonymous-run": "platform",
    "plugins/builder/salesforce-development/skills/platform-architecture-analyze": "platform",
    "plugins/builder/salesforce-development/skills/platform-manifest-generate": "platform",
}

REL_LINK_RE = re.compile(r"\.\./([a-z0-9][a-z0-9-]*)/")
TEXT_EXT = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml"}


def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def clone_upstream(dest: Path) -> None:
    log(f"Clonage de {UPSTREAM_URL} …")
    subprocess.check_call(["git", "clone", "--depth", "1", "--quiet", UPSTREAM_URL, str(dest)])


def domain_of(skill: str) -> str | None:
    for name, cfg in DOMAINS.items():
        if any(re.search(p, skill) for p in cfg["match"]):
            return name
    return None


def skill_frontmatter(skill_md: Path) -> dict:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    out = {}
    if m:
        for key in ("name", "description"):
            km = re.search(rf"^{key}:\s*(.+?)\s*$", m.group(1), re.M)
            if km:
                out[key] = km.group(1).strip().strip('"').strip("'")
    return out


def rewrite_cross_links(plugin_dir: Path, placement: dict[str, str], this_domain: str) -> int:
    """Remplace `../autre-skill/...` par une mention textuelle quand la cible est dans un autre plugin."""
    rewritten = 0
    for f in plugin_dir.rglob("*"):
        if not f.is_file() or f.suffix not in TEXT_EXT:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        def repl(m: re.Match) -> str:
            nonlocal rewritten
            target = m.group(1)
            target_domain = placement.get(target)
            if target_domain is None or target_domain == this_domain:
                return m.group(0)
            rewritten += 1
            return f"<skill:{target} — plugin {PLUGIN_PREFIX}{target_domain}>/"

        new = REL_LINK_RE.sub(repl, text)
        if new != text:
            f.write_text(new, encoding="utf-8")
    return rewritten


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"upstream_commit": None, "skills": {}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", type=Path, help="clone local déjà présent (sinon clone frais)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    tmp = None
    if args.upstream:
        upstream = args.upstream
    else:
        tmp = Path(tempfile.mkdtemp(prefix="sf-skills-"))
        upstream = tmp / "sf-skills"
        clone_upstream(upstream)

    try:
        commit = run(["git", "rev-parse", "HEAD"], cwd=upstream)
        commit_date = run(["git", "log", "-1", "--format=%cs"], cwd=upstream)
        src_skills = upstream / "skills"
        sources: dict[str, Path] = {p.name: p for p in src_skills.iterdir() if (p / "SKILL.md").is_file()}
        placement: dict[str, str] = {}
        unmapped: list[str] = []
        for s in sources:
            d = domain_of(s)
            if d is None:
                unmapped.append(s)
                d = DEFAULT_DOMAIN
            placement[s] = d
        missing_extra: list[str] = []
        for rel, d in EXTRA_SKILLS.items():
            p = upstream / rel
            if not (p / "SKILL.md").is_file():
                missing_extra.append(rel)
                continue
            if p.name not in sources:  # si Salesforce le remonte un jour à la racine, la racine gagne
                sources[p.name] = p
                placement[p.name] = d
        skills = sorted(sources)
        log(f"Upstream {commit[:8]} ({commit_date}) — {len(skills)} skills")

        previous = load_state()
        prev_skills = previous.get("skills", {})
        added = sorted(set(skills) - set(prev_skills))
        removed = sorted(set(prev_skills) - set(skills))
        moved = sorted(s for s in skills if s in prev_skills and prev_skills[s] != placement[s])

        # ---- Résumé (stdout, réutilisé dans le corps de la PR) ----
        print(f"## Synchro sf-skills → {commit_date} (`{commit[:8]}`)\n")
        print(f"- Upstream : https://github.com/forcedotcom/sf-skills/commit/{commit}")
        print(f"- Skills : **{len(skills)}** ({len(added)} ajoutés, {len(removed)} retirés, {len(moved)} déplacés)\n")
        for label, items in (("Ajoutés", added), ("Retirés", removed), ("Déplacés de plugin", moved)):
            if items:
                print(f"### {label}\n")
                for s in items:
                    print(f"- `{s}` → {PLUGIN_PREFIX}{placement.get(s, prev_skills.get(s))}")
                print()
        if unmapped:
            print(f"### ⚠️ Non mappés (placés dans {PLUGIN_PREFIX}{DEFAULT_DOMAIN}, à ajouter dans DOMAINS)\n")
            for s in unmapped:
                print(f"- `{s}`")
            print()
        if missing_extra:
            print("### ⚠️ EXTRA_SKILLS introuvables upstream (déplacés ou supprimés ?)\n")
            for rel in missing_extra:
                print(f"- `{rel}`")
            print()
        # Windows : limite MAX_PATH = 260 caractères. Claude Code clone le marketplace sous
        # C:\Users\<user>\.claude\plugins\marketplaces\<temp>\ (≈ 70-90 caractères de préfixe).
        long_paths = []
        for s in skills:
            for f in sources[s].rglob("*"):
                if f.is_file():
                    rel = f"plugins/{PLUGIN_PREFIX}{placement[s]}/skills/{s}/{f.relative_to(sources[s]).as_posix()}"
                    if len(rel) > LONG_PATH_WARN:
                        long_paths.append((len(rel), rel))
        if long_paths:
            long_paths.sort(reverse=True)
            print(f"### ⚠️ {len(long_paths)} chemins > {LONG_PATH_WARN} caractères (risque « Filename too long » sous Windows sans `core.longpaths`)\n")
            for n, rel in long_paths[:10]:
                print(f"- {n} : `{rel}`")
            if len(long_paths) > 10:
                print(f"- … et {len(long_paths) - 10} autres")
            print()
        counts = {d: sum(1 for v in placement.values() if v == d) for d in DOMAINS}
        print("### Répartition\n")
        for d, n in counts.items():
            print(f"- {PLUGIN_PREFIX}{d} : {n}")

        if args.dry_run:
            log("Dry-run : rien n'a été écrit.")
            return 0

        # ---- Écriture des plugins ----
        y, mo, da = (int(x) for x in commit_date.split("-"))
        version = f"{y}.{mo}.{da}"  # 2026-09-10 -> 2026.9.10 (semver valide, croît avec la date upstream)
        if PLUGINS_DIR.exists():
            shutil.rmtree(PLUGINS_DIR)
        upstream_license = upstream / "LICENSE.txt"

        market_plugins = []
        for d, cfg in DOMAINS.items():
            pdir = PLUGINS_DIR / f"{PLUGIN_PREFIX}{d}"
            (pdir / "skills").mkdir(parents=True)
            members = sorted(s for s, dom in placement.items() if dom == d)
            for s in members:
                shutil.copytree(sources[s], pdir / "skills" / s, symlinks=False)
            n_links = rewrite_cross_links(pdir, placement, d)
            if upstream_license.exists():
                shutil.copy(upstream_license, pdir / "LICENSE")

            manifest = {
                "name": f"{PLUGIN_PREFIX}{d}",
                "displayName": cfg["displayName"],
                "version": version,
                "description": f"{cfg['description']} {len(members)} skills, synchronisés depuis forcedotcom/sf-skills@{commit[:8]}.",
                "author": {"name": "Reej Consulting (repackaging) — skills © Salesforce", "url": "https://github.com/forcedotcom/sf-skills"},
                "license": "Apache-2.0",
                "homepage": "https://github.com/forcedotcom/sf-skills",
                "keywords": cfg["keywords"],
                "skills": "./skills/",
            }
            (pdir / ".claude-plugin").mkdir()
            (pdir / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

            readme = [f"# {cfg['displayName']}", "", cfg["description"], "",
                      f"{len(members)} skills, copie de [forcedotcom/sf-skills](https://github.com/forcedotcom/sf-skills) au commit `{commit[:8]}` ({commit_date}). Ne pas éditer à la main : régénéré par `scripts/sync.py`.", "",
                      "| Skill | Description |", "|---|---|"]
            for s in members:
                fm = skill_frontmatter(pdir / "skills" / s / "SKILL.md")
                desc = fm.get("description", "").replace("|", "\\|")
                desc = (desc[:180] + "…") if len(desc) > 180 else desc
                readme.append(f"| `{s}` | {desc} |")
            (pdir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

            market_plugins.append({
                "name": f"{PLUGIN_PREFIX}{d}",
                "source": f"./plugins/{PLUGIN_PREFIX}{d}",
                "description": manifest["description"],
                "version": version,
                "keywords": cfg["keywords"],
            })
            log(f"  {PLUGIN_PREFIX}{d}: {len(members)} skills, {n_links} liens inter-plugins réécrits")

        marketplace = {
            "name": "reej-salesforce",
            "version": version,
            "description": "Marketplace Reej — skills Salesforce & Agentforce (miroir de forcedotcom/sf-skills, repackagé par domaine, synchro quotidienne).",
            "owner": {"name": "Reej Consulting"},
            "plugins": market_plugins,
        }
        MARKETPLACE_FILE.parent.mkdir(exist_ok=True)
        MARKETPLACE_FILE.write_text(json.dumps(marketplace, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        STATE_FILE.write_text(json.dumps({
            "upstream_repo": UPSTREAM_URL,
            "upstream_commit": commit,
            "upstream_commit_date": commit_date,
            "synced_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "skills": placement,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log("Synchro terminée.")
        return 0
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
