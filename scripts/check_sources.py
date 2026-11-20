#!/usr/bin/env python3
"""
Surveille les sources externes des contenus adaptés (réécrits) dans les plugins maison.

Un plugin maison dont des fichiers sont adaptés d'un dépôt tiers déclare cette origine dans
`reej-plugins/<plugin>/sources.json` : dépôt, commit adapté, correspondance référence → fichiers
source, et empreinte (blob git) de chaque fichier source à ce commit. Ce script compare ces
empreintes à la tête de la branche source et rapporte ce qui a changé, référence par référence,
ainsi que les nouveaux skills apparus dans la source. Rien n'est réécrit automatiquement :
le report dans nos références se fait à la main (voir MAINTENANCE.md du plugin).

Usage :
    python3 scripts/check_sources.py                      # rapport Markdown sur stdout
    python3 scripts/check_sources.py --out-dir DIR        # un fichier <plugin>.md par source modifiée (CI)
    python3 scripts/check_sources.py --snapshot reej-revenue   # enregistre la tête actuelle comme adaptée
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REEJ_PLUGINS_DIR = ROOT / "reej-plugins"


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True, encoding="utf-8").strip()


def fetch_tree(repo: str, branch: str, dest: Path) -> tuple[str, str, dict[str, str]]:
    """Clone minimal (arbres sans contenu des fichiers) : commit, date, {chemin: blob} de la tête."""
    subprocess.check_call(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none", "--no-checkout",
                           "--branch", branch, repo, str(dest)])
    commit = run(["git", "rev-parse", "HEAD"], cwd=dest)
    date = run(["git", "log", "-1", "--format=%cs"], cwd=dest)
    tree = {}
    for line in run(["git", "ls-tree", "-r", "HEAD"], cwd=dest).splitlines():
        meta, path = line.split("\t", 1)
        _mode, kind, sha = meta.split()
        if kind == "blob":
            tree[path] = sha
    return commit, date, tree


def matches(path: str, patterns: list[str]) -> bool:
    # fnmatch : `*` traverse aussi les `/`, donc `dossier/*` couvre les sous-dossiers
    return any(fnmatch.fnmatchcase(path, p) for p in patterns)


def check(plugin: str, cfg: dict, tree: dict[str, str], head: str, head_date: str) -> str:
    src = cfg["source"]
    refs: dict[str, list[str]] = cfg["references"]
    all_patterns = [p for pats in refs.values() for p in pats]
    old: dict[str, str] = cfg["files"]
    now = {p: sha for p, sha in tree.items() if matches(p, all_patterns)}

    changed = sorted(p for p in now if p in old and now[p] != old[p])
    added = sorted(p for p in now if p not in old)
    removed = sorted(p for p in old if p not in now)

    # Nouveaux skills de la source : ni adaptés (cités dans un motif), ni écartés volontairement
    known = set(cfg.get("not_adapted", []))
    for pats in refs.values():
        for p in pats:
            parts = p.split("/")
            if len(parts) > 2 and parts[0] == ".cursor" and parts[1] == "skills":
                known.add(parts[2])
    new_skills = sorted({p.split("/")[2] for p in tree if fnmatch.fnmatchcase(p, cfg["watch"])} - known)

    if not (changed or added or removed or new_skills):
        return ""

    repo_url = src["repo"].removesuffix(".git")
    out = [f"## {plugin} : source modifiée ({src['commit'][:7]} → {head[:7]}, {head_date})", "",
           f"- Source : {repo_url} (branche `{src['branch']}`)",
           f"- Diff : {repo_url}/compare/{src['commit']}...{head} (si l'ancien commit n'existe plus, relire les fichiers en entier)",
           f"- Procédure de report : `reej-plugins/{plugin}/MAINTENANCE.md`", ""]
    for ref, pats in refs.items():
        lines = ([f"- modifié : `{p}`" for p in changed if matches(p, pats)] +
                 [f"- ajouté : `{p}`" for p in added if matches(p, pats)] +
                 [f"- supprimé : `{p}`" for p in removed if matches(p, pats)])
        if lines:
            out += [f"### `{ref}`", "", *lines, ""]
    if new_skills:
        out += ["### Nouveaux skills dans la source", "",
                "À adapter (nouvelle référence + motif dans `references`) ou à écarter (`not_adapted`) :", ""]
        out += [f"- `{s}`" for s in new_skills] + [""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, help="écrit un rapport <plugin>.md par source modifiée")
    ap.add_argument("--snapshot", metavar="PLUGIN", help="enregistre la tête de la source comme adaptée (après report)")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    configs = sorted(REEJ_PLUGINS_DIR.glob("*/sources.json")) if REEJ_PLUGINS_DIR.is_dir() else []
    if args.snapshot:
        configs = [c for c in configs if c.parent.name == args.snapshot]
        if not configs:
            raise SystemExit(f"reej-plugins/{args.snapshot}/sources.json introuvable")
    if args.out_dir:
        args.out_dir.mkdir(parents=True, exist_ok=True)

    for path in configs:
        plugin = path.parent.name
        cfg = json.loads(path.read_text(encoding="utf-8"))
        tmp = Path(tempfile.mkdtemp(prefix="src-"))
        try:
            head, head_date, tree = fetch_tree(cfg["source"]["repo"], cfg["source"]["branch"], tmp / "repo")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        all_patterns = [p for pats in cfg["references"].values() for p in pats]

        if args.snapshot:
            cfg["source"]["commit"], cfg["source"]["commit_date"] = head, head_date
            cfg["files"] = dict(sorted((p, s) for p, s in tree.items() if matches(p, all_patterns)))
            path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print(f"{plugin} : source enregistrée à {head[:7]} ({head_date}), {len(cfg['files'])} fichiers suivis", file=sys.stderr)
            continue

        report = check(plugin, cfg, tree, head, head_date)
        if not report:
            print(f"{plugin} : source inchangée ({cfg['source']['commit'][:7]})", file=sys.stderr)
        elif args.out_dir:
            (args.out_dir / f"{plugin}.md").write_text(report + "\n", encoding="utf-8")
            print(f"{plugin} : source modifiée, rapport écrit", file=sys.stderr)
        else:
            print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
