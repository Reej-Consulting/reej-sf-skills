#!/usr/bin/env python3
"""
Synchronise les skills Salesforce (forcedotcom/sf-skills) dans le marketplace Reej.

- Clone (shallow) le repo upstream
- Range chaque skill de `skills/` dans un plugin par domaine (voir DOMAINS)
- Réécrit les liens relatifs `../<skill>/...` qui traversent un plugin en nom appelable `sf-<plugin>:<skill>`
- Régénère `plugins/<plugin>/.claude-plugin/plugin.json` et `.claude-plugin/marketplace.json`
- Écrit `SYNC_STATE.json` (commit upstream, inventaire) et imprime un résumé des changements,
  dont les scripts embarqués et les `allowed-tools` modifiés (ce qui s'exécute chez l'utilisateur, à relire)

Usage :
    python3 scripts/sync.py                 # synchro complète
    python3 scripts/sync.py --dry-run       # affiche ce qui changerait, n'écrit rien
    python3 scripts/sync.py --upstream /chemin/local   # utilise un clone déjà présent
"""
from __future__ import annotations

import argparse
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
REEJ_PLUGINS_DIR = ROOT / "reej-plugins"   # plugins maison : jamais effacés ni régénérés par ce script
REEJ_PREFIX = "reej-"
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
            r"^platform-agent(ic)?setup-", r"^platform-tracing-agentforce-",
            r"^sales-agentforce-", r"^service-agentforce-",
        ],
    },
    "platform": {
        "displayName": "Salesforce — Platform & Apex",
        "description": "Socle plateforme : métadonnées (objets, champs, permissions, sharing), Apex, Flow, SOQL, déploiement/retrieve, Code Analyzer, SLDS, documentation Salesforce.",
        "keywords": ["salesforce", "apex", "flow", "soql", "metadata", "deploy", "slds"],
        "match": [r"^platform-", r"^automation-flow-", r"^design-systems-", r"^external-", r"^dx-code-", r"^dx-apexguru-",
                  r"^tableau-", r"^marketing-", r"^sales-"],  # clouds isolés (1-2 skills) : pas de plugin dédié tant que ça reste marginal
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
        "match": [r"^field-service-", r"^consumer-goods-", r"^education-cloud-", r"^life-sciences-", r"^insurance-"],
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
    "plugins/builder/salesforce-code-quality/skills/platform-architecture-analyze": "platform",  # déplacé upstream le 2026-10-07
    "plugins/builder/salesforce-development/skills/platform-manifest-generate": "platform",
}

REL_LINK_RE = re.compile(r"(?:\.\./)+([a-z0-9][a-z0-9-]*)/")
MD_LINK_RE = re.compile(r"\[([^\]\n]+)\]\((?:\.\./)+([a-z0-9][a-z0-9-]*)/([^)\s]*)\)")
TEXT_EXT = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".json", ".yaml", ".yml"}
SCRIPT_EXT = {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".ps1"}
TOOL_RE = re.compile(r"[^\s,(]+(?:\([^)]*\))?")  # `Read`, `Bash(sf agent:*)`…
SUMMARY_CAP = 40  # lignes max par section « à relire » (corps de PR limité à 65 536 caractères)


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


def rewrite_links(text: str, placement: dict[str, str], this_domain: str) -> tuple[str, int]:
    """Remplace les liens `../autre-skill/...` dont la cible est dans un autre plugin par son nom appelable
    `sf-<plugin>:<skill>` : Claude l'invoque si ce plugin est installé, sinon le nom dit lequel installer."""
    rewritten = 0

    def callable_name(skill: str) -> str | None:
        d = placement.get(skill)
        return None if d is None or d == this_domain else f"{PLUGIN_PREFIX}{d}:{skill}"

    def md_link(m: re.Match) -> str:
        nonlocal rewritten
        label, skill, path = m.groups()
        name = callable_name(skill)
        if name is None:
            return m.group(0)
        rewritten += 1
        other_file = path not in ("", "SKILL.md")
        ref = f"skill `{name}`" + (f", file `{path}`" if other_file else "")
        return ref if label == skill and not other_file else f"{label} ({ref})"

    def bare(m: re.Match) -> str:  # chemin hors lien Markdown (code, prose)
        nonlocal rewritten
        name = callable_name(m.group(1))
        if name is None:
            return m.group(0)
        rewritten += 1
        return f"<skill {name}>/"

    text = MD_LINK_RE.sub(md_link, text)
    return REL_LINK_RE.sub(bare, text), rewritten


def rewrite_cross_links(plugin_dir: Path, placement: dict[str, str], this_domain: str) -> int:
    rewritten = 0
    for f in plugin_dir.rglob("*"):
        if not f.is_file() or f.suffix not in TEXT_EXT:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new, n = rewrite_links(text, placement, this_domain)
        if n:
            f.write_text(new, encoding="utf-8")
            rewritten += n
    return rewritten


def allowed_tools(skill_md: Path) -> set[str]:
    """Outils que le skill peut utiliser sans demander (`allowed-tools` du frontmatter)."""
    if not skill_md.is_file():
        return set()
    m = re.match(r"^---\n(.*?)\n---", skill_md.read_text(encoding="utf-8", errors="replace"), re.S)
    km = m and re.search(r"^allowed-tools:[ \t]*(.*(?:\n[ \t]+.*)*)", m.group(1), re.M)
    if not km:
        return set()
    return {t for t in TOOL_RE.findall(re.sub(r"[\[\]\"']", " ", km.group(1))) if t != "-"}


def review_changes(skills: list[str], sources: dict[str, Path], placement: dict[str, str],
                   prev_skills: dict[str, str]) -> tuple[list[str], list[str]]:
    """Ce qui s'exécute chez l'utilisateur et a changé depuis la dernière synchro : scripts embarqués
    ajoutés/modifiés et `allowed-tools` modifiés. Comparaison avec plugins/ tel qu'il est avant régénération."""
    scripts, tools = [], []
    for s in skills:
        old_root = PLUGINS_DIR / f"{PLUGIN_PREFIX}{prev_skills[s]}" / "skills" / s if s in prev_skills else None
        for f in sorted(sources[s].rglob("*")):
            if not f.is_file() or f.suffix not in SCRIPT_EXT:
                continue
            rel = f.relative_to(sources[s]).as_posix()
            new = f.read_bytes()
            if f.suffix in TEXT_EXT:  # même réécriture qu'à l'écriture, sinon faux « modifié » à chaque run
                try:
                    new = rewrite_links(new.decode("utf-8"), placement, placement[s])[0].encode("utf-8")
                except UnicodeDecodeError:
                    pass
            old = old_root / rel if old_root else None
            if old is None or not old.is_file():
                scripts.append(f"ajouté : `{s}/{rel}`")
            elif old.read_bytes().replace(b"\r\n", b"\n") != new.replace(b"\r\n", b"\n"):
                scripts.append(f"modifié : `{s}/{rel}`")
        new_t = allowed_tools(sources[s] / "SKILL.md")
        old_t = allowed_tools(old_root / "SKILL.md") if old_root else set()
        if new_t != old_t:
            tools.append(f"`{s}` : " + " · ".join([f"+ `{t}`" for t in sorted(new_t - old_t)] +
                                                   [f"− `{t}`" for t in sorted(old_t - new_t)]))
    return scripts, tools


def collect_reej_plugins() -> list[dict]:
    """Entrées marketplace des plugins maison (reej-plugins/<nom>/.claude-plugin/plugin.json)."""
    entries = []
    if not REEJ_PLUGINS_DIR.is_dir():
        return entries
    for pdir in sorted(REEJ_PLUGINS_DIR.iterdir()):
        manifest = pdir / ".claude-plugin" / "plugin.json"
        if not manifest.is_file():
            continue
        m = json.loads(manifest.read_text(encoding="utf-8"))
        if m.get("name") != pdir.name:
            raise SystemExit(f"reej-plugins/{pdir.name}: plugin.json.name = {m.get('name')!r} ≠ nom du dossier")
        if not pdir.name.startswith(REEJ_PREFIX):
            raise SystemExit(f"reej-plugins/{pdir.name}: le nom doit commencer par {REEJ_PREFIX!r}")
        entries.append({
            "name": m["name"],
            "source": f"./reej-plugins/{pdir.name}",
            "description": m.get("description", ""),
            "version": m.get("version", "0.1.0"),
            "keywords": m.get("keywords", []),
        })
    return entries


def marketplace_doc(version: str, reej_entries: list[dict], mirror_entries: list[dict]) -> dict:
    return {
        "name": "reej-salesforce",
        "version": version,
        "description": "Marketplace Reej — skills Salesforce & Agentforce (miroir de forcedotcom/sf-skills, repackagé par domaine, synchro quotidienne) et skills maison Reej (reej-*).",
        "owner": {"name": "Reej Consulting"},
        "plugins": reej_entries + mirror_entries,
    }


def write_marketplace_only() -> int:
    """Régénère marketplace.json sans toucher aux plugins : entrées miroir relues depuis plugins/, maison depuis reej-plugins/."""
    mirror = []
    for pdir in sorted(PLUGINS_DIR.iterdir()) if PLUGINS_DIR.is_dir() else []:
        manifest = pdir / ".claude-plugin" / "plugin.json"
        if manifest.is_file():
            m = json.loads(manifest.read_text(encoding="utf-8"))
            mirror.append({"name": m["name"], "source": f"./plugins/{pdir.name}", "description": m.get("description", ""),
                           "version": m.get("version", "0.0.0"), "keywords": m.get("keywords", [])})
    order = [f"{PLUGIN_PREFIX}{d}" for d in DOMAINS]  # même ordre que la synchro complète, sinon diff parasite
    mirror.sort(key=lambda e: order.index(e["name"]) if e["name"] in order else len(order))
    reej = collect_reej_plugins()
    state = load_state()
    version = state.get("version") or (MARKETPLACE_FILE.is_file() and json.loads(MARKETPLACE_FILE.read_text(encoding="utf-8")).get("version")) or "0.0.0"
    MARKETPLACE_FILE.parent.mkdir(exist_ok=True)
    MARKETPLACE_FILE.write_text(json.dumps(marketplace_doc(version, reej, mirror), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log(f"marketplace.json régénéré : {len(reej)} plugin(s) maison + {len(mirror)} miroir")
    return 0


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"upstream_commit": None, "skills": {}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", type=Path, help="clone local déjà présent (sinon clone frais)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--marketplace-only", action="store_true",
                    help="ne clone rien : régénère seulement marketplace.json à partir des plugins présents (après ajout d'un plugin maison)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Windows : sortie redirigée en cp1252 sinon, plantage sur « → »

    if args.marketplace_only:
        return write_marketplace_only()

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
        scripts_changed, tools_changed = review_changes(skills, sources, placement, prev_skills)

        # ---- Résumé (stdout, réutilisé dans le corps de la PR) ----
        print(f"## Synchro sf-skills → {commit_date} (`{commit[:8]}`)\n")
        print(f"- Upstream : https://github.com/forcedotcom/sf-skills/commit/{commit}")
        print(f"- Skills : **{len(skills)}** ({len(added)} ajoutés, {len(removed)} retirés, {len(moved)} déplacés)")
        print(f"- À relire : **{len(scripts_changed)}** scripts ajoutés ou modifiés, **{len(tools_changed)}** `allowed-tools` modifiés\n")
        for label, items in (("Ajoutés", added), ("Retirés", removed), ("Déplacés de plugin", moved)):
            if items:
                print(f"### {label}\n")
                for s in items:
                    print(f"- `{s}` → {PLUGIN_PREFIX}{placement.get(s, prev_skills.get(s))}")
                print()
        for label, items in (("🔍 Scripts ajoutés ou modifiés — code que Claude peut exécuter sur les postes", scripts_changed),
                             ("🔍 `allowed-tools` modifiés — outils que le skill utilise sans demander", tools_changed)):
            if items:
                print(f"### {label}\n")
                for line in items[:SUMMARY_CAP]:
                    print(f"- {line}")
                if len(items) > SUMMARY_CAP:
                    print(f"- … et {len(items) - SUMMARY_CAP} autres (voir le diff de la PR)")
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

        # ---- Plugins maison (reej-plugins/) : jamais touchés par la synchro, seulement listés ----
        reej_entries = collect_reej_plugins()
        for e in reej_entries:
            log(f"  {e['name']} (maison) v{e['version']}")

        MARKETPLACE_FILE.parent.mkdir(exist_ok=True)
        MARKETPLACE_FILE.write_text(json.dumps(marketplace_doc(version, reej_entries, market_plugins), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        STATE_FILE.write_text(json.dumps({
            "upstream_repo": UPSTREAM_URL,
            "upstream_commit": commit,
            "upstream_commit_date": commit_date,
            "version": version,
            # pas d'horodatage du run : le fichier ne doit changer que si l'upstream change,
            # sinon chaque exécution ouvrirait une PR vide
            "skills": dict(sorted(placement.items())),  # trié : l'ordre de iterdir() varie selon l'OS et le système de fichiers
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        log("Synchro terminée.")
        return 0
    finally:
        if tmp and tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
