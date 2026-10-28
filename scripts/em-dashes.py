#!/usr/bin/env python3
"""Détecte (et corrige) les tirets cadratins du dépôt.

Deux périmètres :

  * par défaut, les lignes AJOUTÉES par la branche courante (commits depuis `--base`,
    modifications non commitées, fichiers non suivis) : c'est le mode « hygiène de PR » ;
  * `--staged` : les lignes ajoutées dans l'index seulement (usage : hook pre-commit) ;
  * `--all-tracked` : tous les fichiers suivis par git, optionnellement restreints à des
    préfixes (`--path documentation/ --path .claude/`) : c'est le mode « éradication du stock »
    (issue #366), à passer zone par zone.

Remplacement proposé, selon le contexte de la ligne :

  titre Markdown (`# …`)               ->  point médian  (« ## OEDG · Discount Groups »)
  cellule de tableau réduite au tiret  ->  cellule vide  (« | C6015 | … |  | »)
  un gras ou du code juste avant       ->  deux-points   (« **Label** : texte », « `Classe` : rôle »)
  le tiret est à l'intérieur d'un gras ->  point médian  (« **Étape 1 · Configuration** »)
  tout le reste (apposition)           ->  virgule       (« …texte, incise »)

Le script s'exclut lui-même (sa propre documentation contient les caractères qu'il traque).
Les binaires (PDF, images, polices, archives…) ne sont jamais lus ni réécrits.

Dans un fichier Markdown, les lignes situées dans un bloc de code (``` … ```) sont signalées
mais jamais réécrites, sauf `--include-fenced` : un tiret cadratin peut y être une donnée
(sortie SAP, exemple de fichier).

Usage :
    python3 .claude/scripts/em-dashes.py                 # dry-run sur la branche (base: develop)
    python3 .claude/scripts/em-dashes.py --base feat/x   # autre base de comparaison
    python3 .claude/scripts/em-dashes.py --staged --check   # hook pre-commit : sortie 1 s'il en reste
    python3 .claude/scripts/em-dashes.py --apply         # écrit les corrections
    python3 .claude/scripts/em-dashes.py --apply --replacement ' - '   # remplacement fixe
    python3 .claude/scripts/em-dashes.py --all-tracked --quiet   # inventaire repo entier (lecture seule)
    python3 .claude/scripts/em-dashes.py --all-tracked --path documentation/ --apply   # une zone
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

EM_DASH = "—"  # —
OTHER_DASHES = {"–": "en dash", "―": "barre horizontale"}

RE_FENCE = re.compile(r"^\s*(```|~~~)")
RE_HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
# Un libellé (gras, code, italique) juste avant le tiret appelle un deux-points.
RE_AFTER_LABEL = re.compile(r"(\*\*|`|_)\s" + EM_DASH + r"\s")
# Un gras commence et finit par un caractère non blanc : « **x** — y **z** » n'est pas un gras.
RE_INSIDE_BOLD = re.compile(r"\*\*(?=\S)[^*]*" + EM_DASH + r"[^*]*(?<=\S)\*\*")
# Cellule de tableau Markdown réduite au tiret (« | — | ») : sens « vide », pas « incise ».
RE_EMPTY_CELL = re.compile(r"\|(\s*)" + EM_DASH + r"(\s*)(?=\|)")
# Tiret en fin de ligne (« …l'avenir —\nles deux… ») : l'incise continue à la ligne suivante.
RE_START_OF_LINE = re.compile(r"^(\s*)" + EM_DASH + r"\s")
# Code (PHP, Vue, JS, Blade…) : balise fermante de libellé juste avant → deux-points ;
# « — X — » (placeholder de <option>, vide de tableau) → « - X - » ; le segment de texte
# qui précède un tiret s'arrête au dernier de ces délimiteurs.
RE_AFTER_HTML_LABEL = re.compile(r"(</(?:strong|b|em|code|kbd)>)\s" + EM_DASH + r"\s")
RE_PAIRED_PLACEHOLDER = re.compile(r"(?<=[>'\"])\s*" + EM_DASH + r"\s*([^" + EM_DASH + r"<>'\"{}]{1,40}?)\s*" + EM_DASH + r"\s*(?=[<'\"]|$)")
# Tiret collé à un délimiteur ouvrant (« >— texte », « '— texte ») : début de libellé.
RE_AFTER_OPENING = re.compile(r"(?<=[>'\"`])" + EM_DASH + r"\s")
RE_CODE_DELIMITER = re.compile(r"['\"`>(\[{=;]|\}\}|//|/\*|\*|#|--|\{\{--|<!--")
RE_END_OF_LINE = re.compile(r"\s" + EM_DASH + r"\s*$")
SELF = Path(__file__).resolve()

BINARY_SUFFIXES = {
    ".pdf", ".gif", ".png", ".jpg", ".jpeg", ".webp", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".zip", ".gz", ".tgz", ".xlsx", ".xls", ".docx", ".pptx", ".pyc", ".phar",
}

# Textes de tiers reproduits mot pour mot (licences, assets vendor publiés) : on ne les réécrit
# jamais ; pour les licences, seul le générateur (GenerateThirdPartyLicenses) est corrigé.
VERBATIM_PREFIXES = (
    "THIRD-PARTY-LICENSES.md",
    "public/vendor/",
    # Le tiret cadratin (0x97 en CP1252) y est la donnée testée.
    "tests/Unit/Support/SanitizeUtf8RecursivelyTest.php",
)

# Une ligne portant ce marqueur n'est jamais réécrite (le tiret y est une donnée).
KEEP_MARKER = "em-dashes:keep"

Hit = tuple[Path, int, str, str]
Skipped = tuple[Path, int, str]


def run(args: list[str]) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=False).stdout


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    try:
        with path.open("rb") as handle:
            return b"\0" not in handle.read(8192)
    except OSError:
        return False


def read_lines(path: Path) -> list[str] | None:
    if not path.is_file() or path.resolve() == SELF or str(path).startswith(VERBATIM_PREFIXES) or not is_text_file(path):
        return None
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def added_lines_by_file(base: str | None, staged: bool) -> dict[Path, set[str]]:
    """Lignes ajoutées : index seul (`staged`), ou commits + travail non commité depuis `base`."""
    out: dict[Path, set[str]] = {}
    current: Path | None = None
    diff_args = ["git", "diff", "--no-color", "-U0"]
    diff_args += ["--cached"] if staged else [base or "develop"]
    for line in run(diff_args).splitlines():
        if line.startswith("+++ b/"):
            current = Path(line[6:])
            out.setdefault(current, set())
        elif line.startswith("+") and not line.startswith("+++") and current is not None:
            out[current].add(line[1:])

    if staged:
        return out

    for rel in run(["git", "ls-files", "--others", "--exclude-standard"]).split("\n"):
        if not rel.strip():
            continue
        path = Path(rel)
        lines = read_lines(path)
        if lines is not None:
            out[path] = set(lines)
    return out


def tracked_files(prefixes: list[str], excluded: list[str]) -> list[Path]:
    paths = [Path(rel) for rel in run(["git", "ls-files"]).split("\n") if rel.strip()]
    if prefixes:
        paths = [p for p in paths if any(str(p).startswith(prefix) for prefix in prefixes)]
    return [p for p in paths if not any(str(p).startswith(prefix) for prefix in excluded)]


def code_separator(before: str) -> str:
    """Dans du code (libellé, chaîne, commentaire) : point médian après un libellé court,
    virgule après une proposition longue. Le segment considéré s'arrête au dernier délimiteur
    (quote, balise, accolade de template, parenthèse, marqueur de commentaire)."""
    segment = RE_CODE_DELIMITER.split(before)[-1]
    words = [w for w in segment.split() if w]
    return " · " if len(words) <= 5 else ", "


def suggest_code(line: str) -> str:
    if line.strip() == EM_DASH:
        return line.replace(EM_DASH, "-")
    new = RE_PAIRED_PLACEHOLDER.sub(lambda m: "- " + m.group(1) + " -", line)
    new = RE_AFTER_HTML_LABEL.sub(lambda m: m.group(1) + " : ", new)
    new = RE_AFTER_LABEL.sub(lambda m: m.group(1) + " : ", new)
    new = RE_END_OF_LINE.sub(",", new)
    new = RE_START_OF_LINE.sub(lambda m: m.group(1) + "· ", new)
    new = RE_AFTER_OPENING.sub("· ", new)
    out: list[str] = []
    rest = new
    while True:
        idx = rest.find(f" {EM_DASH} ")
        if idx < 0:
            break
        out.append(rest[:idx])
        out.append(code_separator("".join(out)))
        rest = rest[idx + 3:]
    out.append(rest)
    return "".join(out).replace(EM_DASH, "-")


def suggest(line: str, *, markdown: bool) -> str:
    """Réécrit tous les tirets cadratins d'une ligne selon le contexte."""
    if not markdown:
        return suggest_code(line)
    new = line
    if RE_HEADING.match(new):
        return new.replace(f" {EM_DASH} ", " · ").replace(EM_DASH, "·")
    new = RE_EMPTY_CELL.sub(lambda m: "|" + m.group(1) + m.group(2), new)
    new = RE_INSIDE_BOLD.sub(lambda m: m.group(0).replace(EM_DASH, "·"), new)
    new = RE_AFTER_LABEL.sub(lambda m: m.group(1) + " : ", new)
    new = new.replace(f" {EM_DASH} ", ", ")
    new = RE_END_OF_LINE.sub(",", new)
    return new.replace(EM_DASH, "-")


def needs_review(line: str) -> bool:
    """Cas où l'heuristique ligne à ligne est faible : paire d'incises, ou tiret ouvrant la ligne."""
    return line.count(EM_DASH) >= 2 or bool(RE_START_OF_LINE.match(line))


def scan_file(
    path: Path,
    only_lines: set[str] | None,
    forced: str | None,
    include_fenced: bool,
) -> tuple[list[Hit], list[Skipped]]:
    hits: list[Hit] = []
    skipped: list[Skipped] = []
    lines = read_lines(path)
    if lines is None:
        return hits, skipped

    markdown = path.suffix.lower() in {".md", ".markdown"}
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if markdown and RE_FENCE.match(line):
            in_fence = not in_fence
            continue
        if EM_DASH not in line or (only_lines is not None and line not in only_lines):
            continue
        if KEEP_MARKER in line:
            continue
        if in_fence and not include_fenced:
            skipped.append((path, number, line))
            continue
        new = line.replace(EM_DASH, forced) if forced else suggest(line, markdown=markdown)
        hits.append((path, number, line, new))
    return hits, skipped


def scan(
    targets: dict[Path, set[str] | None],
    forced: str | None,
    include_fenced: bool,
) -> tuple[list[Hit], list[Skipped]]:
    hits: list[Hit] = []
    skipped: list[Skipped] = []
    for path, only_lines in sorted(targets.items()):
        if only_lines is not None and not only_lines:
            continue
        file_hits, file_skipped = scan_file(path, only_lines, forced, include_fenced)
        hits += file_hits
        skipped += file_skipped
    return hits, skipped


def apply(hits: list[Hit]) -> int:
    changes: dict[Path, dict[int, str]] = {}
    for path, number, _old, new in hits:
        changes.setdefault(path, {})[number] = new
    for path, per_line in changes.items():
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for number, new in per_line.items():
            ending = "\n" if lines[number - 1].endswith("\n") else ""
            lines[number - 1] = new + ending
        path.write_text("".join(lines), encoding="utf-8")
    return len(changes)


def print_inventory(hits: list[Hit], skipped: list[Skipped]) -> None:
    counts: dict[str, int] = {}
    for path, _n, old, _new in hits:
        counts[str(path)] = counts.get(str(path), 0) + old.count(EM_DASH)
    for path, _n, old in skipped:
        counts[str(path)] = counts.get(str(path), 0) + old.count(EM_DASH)
    for rel, n in sorted(counts.items(), key=lambda kv: -kv[1])[:20]:
        print(f"{n:6d}  {rel}")
    total = sum(counts.values())
    print(f"\n{total} tirets cadratins dans {len(counts)} fichiers suivis"
          f" ({len(skipped)} ligne(s) en bloc de code Markdown, ignorées sans --include-fenced).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="develop", help="Base de comparaison git (défaut : develop)")
    parser.add_argument("--staged", action="store_true", help="Lignes ajoutées dans l'index seulement (hook)")
    parser.add_argument("--apply", action="store_true", help="Écrit les corrections")
    parser.add_argument("--check", action="store_true", help="Sortie 1 s'il reste des tirets cadratins")
    parser.add_argument("--replacement", help="Remplacement fixe au lieu de l'heuristique (ex. ' - ')")
    parser.add_argument("--all-tracked", action="store_true", help="Tous les fichiers suivis (inventaire ou --apply)")
    parser.add_argument("--path", action="append", default=[], metavar="PREFIX",
                        help="Avec --all-tracked : restreint aux chemins commençant par PREFIX (répétable)")
    parser.add_argument("--exclude", action="append", default=[], metavar="PREFIX",
                        help="Avec --all-tracked : ignore les chemins commençant par PREFIX (répétable)")
    parser.add_argument("--include-fenced", action="store_true",
                        help="Traite aussi les lignes en bloc de code Markdown")
    parser.add_argument("--quiet", action="store_true", help="N'affiche pas le détail ligne à ligne")
    args = parser.parse_args()

    if args.all_tracked:
        targets: dict[Path, set[str] | None] = {p: None for p in tracked_files(args.path, args.exclude)}
    else:
        targets = dict(added_lines_by_file(args.base, args.staged))

    hits, skipped = scan(targets, args.replacement, args.include_fenced)

    if not args.quiet:
        for path, number, old, new in hits:
            flag = "  [à relire : incise double ou tiret en début de ligne]" if needs_review(old) else ""
            print(f"\n{path}:{number}{flag}")
            print(f"  - {old.strip()[:180]}")
            print(f"  + {new.strip()[:180]}")
        for path, number, line in skipped:
            print(f"\n{path}:{number}  [bloc de code, ignoré]")
            print(f"    {line.strip()[:180]}")

    others: list[str] = []
    for path, _n, old, _new in hits:
        for char, name in OTHER_DASHES.items():
            if char in old:
                others.append(f"{path} : {name}")
    if others and not args.quiet:
        print("\nAutres tirets longs repérés (non traités) :")
        for line in sorted(set(others)):
            print(f"  {line}")

    if args.all_tracked:
        print("\nInventaire par fichier (20 premiers) :\n")
        print_inventory(hits, skipped)

    scope = "repo entier" if args.all_tracked else ("index" if args.staged else f"base : {args.base}")
    print(f"\n{len(hits)} ligne(s) à corriger, {len(skipped)} ignorée(s) en bloc de code ({scope}).")

    if args.check:
        return 1 if hits else 0
    if args.apply and hits:
        n = apply(hits)
        print(f"✔ {len(hits)} ligne(s) réécrite(s) dans {n} fichier(s).")
    elif not args.apply:
        print("(dry-run : relancer avec --apply pour écrire)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
