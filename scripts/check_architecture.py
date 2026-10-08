"""Machine-check the architecture rules that CI is required to enforce.

Specification v5.1 section 273 makes architecture validation a CI
responsibility and lists eight rules. The four implemented here are the ones
a reviewer provably cannot hold, because each defect they catch looks
correct in a diff:

* a dependency cycle only exists across three or more `gem.json` files, so no
  single manifest in the pull request looks wrong; the symptom appears later
  as a build order that cannot be satisfied;
* an `#include` that reaches into a neighbouring gem's private `Source/` tree
  compiles happily today and welds two gems together permanently, which is
  the failure the public `Include/Phoenix/...` split exists to prevent;
* an `*.AutoComponent.xml` that nobody added to `Phoenix_autogen_files.cmake`
  does not fail the build, it simply never generates, and the component is
  missing at runtime with no error anywhere;
* a top-level directory that no CODEOWNERS pattern matches has no reviewer,
  and TDD 08 states that a system without an owner may not become production
  ready.

Four of the eight rules in section 273 are deliberately NOT implemented
here, because this repository cannot decide them today:

* **No missing tests for required systems.** Needs a registry that names
  which systems are required and which test file covers each. No such
  registry exists; inferring it from directory names would make the gate
  agree with whatever the tree happens to contain, which is not a check.
* **No invalid asset references.** Already enforced by
  `tools/validation/validate_assets.py`; a second implementation would drift
  from the first.
* **No broken schemas.** Already enforced by `scripts/validate.py`, which
  validates every schema and every sample document against it.
* **No unexpected engine changes.** Needs the O3DE checkout (tag 2605.0) to
  diff against. CI has no engine, so there is nothing to compare; this
  belongs to the Class C stages in TDD 08 that require a registered engine.

Rule 2 is enforced as the general form stated in specification v1.0
section 4.3: no Phoenix unit may include another unit's `Source/` path at
all. That subsumes the narrower "Presentation must not include Gameplay
implementation internals" clause, which is a special case of it, so only the
general rule is implemented. The two containment rules (rendering headers in
PhoenixPresentation, Multiplayer headers in PhoenixNetworking) are not
subsumed and are checked separately.
"""
from __future__ import annotations

import fnmatch
import posixpath
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from _repo import load_json  # noqa: E402

#: The gem that owns rendering integration. Atom, LyShine and the
#: AzFramework render headers are its dependencies alone; see
#: docs/adr/0008-rendering-extension-policy.md.
RENDERING_GEM = "PhoenixPresentation"

#: The gem that owns network authority and replication.
NETWORKING_GEM = "PhoenixNetworking"

#: Engine include roots that are rendering, by first path segment.
RENDERING_ROOTS = frozenset({"Atom", "LyShine"})

#: Engine include root that is multiplayer, by first path segment.
MULTIPLAYER_ROOT = "Multiplayer"

#: Top-level areas that must each have a named owner. A directory absent
#: from the tree cannot be an unowned area and is skipped.
OWNED_AREAS = ("gems", "project", "scripts", "tools", "tests", "docs", ".github")

#: Where GitHub looks for CODEOWNERS, in its own resolution order.
CODEOWNERS_LOCATIONS = ("CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS")

INCLUDE_LINE = re.compile(r'^\s*#\s*include\s*[<"]([^>"]+)[>"]')

AUTOGEN_SET_BLOCK = re.compile(r"set\s*\(\s*PHOENIX_AUTOGEN_FILES(.*?)\)", re.S)

SOURCE_EXTENSIONS = ("*.h", "*.cpp")


def _gem_dirs(root: Path) -> list[Path]:
    """gem.json-bearing directories under <root>/gems.

    Mirrors _repo.gem_dirs(), which is anchored at the repository root. Every
    rule below takes a root instead, so tests/Unit/test_architecture.py can
    exercise it against a constructed tree: a gate whose rules can only run
    against the one tree that already satisfies them has never been seen to
    fail.
    """
    gems = root / "gems"
    if not gems.is_dir():
        return []
    return sorted(p for p in gems.iterdir() if (p / "gem.json").is_file())


def _units(root: Path) -> dict[str, Path]:
    """Phoenix compilation units by name: every gem, plus the project."""
    units = {gem.name: gem / "Code" for gem in _gem_dirs(root)}
    project_code = root / "project" / "Code"
    if project_code.is_dir():
        units["project"] = project_code
    return units


# --------------------------------------------------------------------------
# Rule 1: no cyclic gem dependencies
# --------------------------------------------------------------------------


def gem_dependency_graph(root: Path) -> dict[str, list[str]]:
    """Phoenix-internal dependency edges from every gems/*/gem.json.

    Engine gems (PhysX5, EMotionFX, Multiplayer, ...) are dropped: they are
    O3DE's to order, and an engine gem cannot close a cycle back into
    Phoenix.
    """
    internal = {gem.name for gem in _gem_dirs(root)}
    graph: dict[str, list[str]] = {}
    for gem in _gem_dirs(root):
        manifest = load_json(gem / "gem.json")
        dependencies = manifest.get("dependencies", [])
        graph[gem.name] = sorted(d for d in dependencies if d in internal)
    return graph


def _walk_for_cycles(
    graph: dict[str, list[str]], start: str, stack: list[str], cycles: list[list[str]]
) -> None:
    for successor in graph.get(stack[-1], ()):
        if successor == start:
            cycles.append(list(stack))
        elif successor > start and successor not in stack:
            stack.append(successor)
            _walk_for_cycles(graph, start, stack, cycles)
            stack.pop()


def find_cycles(graph: dict[str, list[str]]) -> list[list[str]]:
    """Every elementary cycle, each reported exactly once.

    Only paths whose smallest member is the entry point are explored, so the
    same cycle reached from three different gems is not reported three times.
    A gem that depends on itself yields a one-element cycle.
    """
    cycles: list[list[str]] = []
    for start in sorted(graph):
        _walk_for_cycles(graph, start, [start], cycles)
    return cycles


def check_gem_cycles(root: Path, errors: list[str]) -> tuple[int, int]:
    graph = gem_dependency_graph(root)
    for cycle in find_cycles(graph):
        path = " -> ".join([*cycle, cycle[0]])
        errors.append(
            f"cyclic gem dependency: {path} "
            "(see docs/architecture/README.md; the graph must stay acyclic)"
        )
    return len(graph), sum(len(v) for v in graph.values())


# --------------------------------------------------------------------------
# Rule 2: no forbidden includes
# --------------------------------------------------------------------------


def _header_indexes(root: Path) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    """Two ways an #include can name a header in this repository.

    by_include_path keys a header by its path relative to the Code/Include or
    Code/Source root, which is how the compiler sees it once those roots are
    on the include path.

    by_explicit_path keys it by every tail of its repository-relative path
    that still contains the Include/ or Source/ segment, which is how a
    header gets named when someone spells a route into another unit's tree.
    Shorter tails are left out on purpose: a bare file name would collide
    with unrelated engine headers.
    """
    by_include_path: dict[str, list[Path]] = {}
    by_explicit_path: dict[str, list[Path]] = {}
    for code in _units(root).values():
        for tree in ("Include", "Source"):
            base = code / tree
            if not base.is_dir():
                continue
            marker = len(base.relative_to(root).parts) - 1
            for header in sorted(base.rglob("*.h")):
                by_include_path.setdefault(
                    header.relative_to(base).as_posix(), []
                ).append(header)
                parts = header.relative_to(root).parts
                for start in range(marker + 1):
                    key = "/".join(parts[start:])
                    by_explicit_path.setdefault(key, []).append(header)
    return by_include_path, by_explicit_path


def _resolve_include(
    include: str,
    source_file: Path,
    root: Path,
    by_include_path: dict[str, list[Path]],
    by_explicit_path: dict[str, list[Path]],
) -> list[Path]:
    """Headers in this repository that an #include target can name.

    Tried in order of how specifically each form identifies a file, and the
    first form that resolves wins. Resolving against the including file's own
    directory first is what keeps a quoted sibling include from being matched
    against a same-named header somewhere else in the tree.
    """
    normalized = posixpath.normpath(include)

    local = (source_file.parent / include).resolve()
    if local.is_file() and local.is_relative_to(root):
        return [local]
    if normalized in by_include_path:
        return by_include_path[normalized]
    return by_explicit_path.get(normalized, [])


def _is_private(header: Path, root: Path) -> bool:
    return "/Code/Source/" in f"/{header.relative_to(root).as_posix()}"


def _names_foreign_source_tree(include: str, unit: str, unit_names: set[str]) -> bool:
    """True when the include spells a route into another unit's Source/ tree.

    Checked on the text as well as on resolution, because a route into a
    neighbour's private tree is a violation whether or not the header at the
    far end happens to exist yet.
    """
    parts = posixpath.normpath(include).split("/")
    if "Source" not in parts:
        return False
    above = parts[: parts.index("Source")]
    return any(part in unit_names and part != unit for part in above)


def _is_rendering_header(parts: list[str]) -> bool:
    if parts[0] in RENDERING_ROOTS:
        return True
    return parts[0] == "AzFramework" and len(parts) > 1 and parts[1].startswith("Render")


def check_forbidden_includes(root: Path, errors: list[str]) -> tuple[int, int]:
    units = _units(root)
    unit_names = set(units)
    by_include_path, by_explicit_path = _header_indexes(root)

    scanned_files = 0
    scanned_includes = 0

    for unit, code in sorted(units.items()):
        sources: list[Path] = []
        for pattern in SOURCE_EXTENSIONS:
            sources += code.rglob(pattern)
        for source_file in sorted(sources):
            scanned_files += 1
            rel = source_file.relative_to(root).as_posix()
            text = source_file.read_text(encoding="utf-8", errors="replace")
            for number, line in enumerate(text.splitlines(), start=1):
                match = INCLUDE_LINE.match(line)
                if match is None:
                    continue
                include = match.group(1)
                scanned_includes += 1
                parts = posixpath.normpath(include).split("/")

                if _names_foreign_source_tree(include, unit, unit_names):
                    errors.append(
                        f"{rel}:{number}: '{include}' names a route into another "
                        "unit's private Source/ tree; only Include/Phoenix/... "
                        "headers are public (v1.0 section 4.3)"
                    )
                else:
                    for header in _resolve_include(
                        include, source_file, root, by_include_path, by_explicit_path
                    ):
                        owner = _unit_of(header, root)
                        if owner is None or owner == unit:
                            continue
                        if _is_private(header, root):
                            errors.append(
                                f"{rel}:{number}: '{include}' resolves to "
                                f"{header.relative_to(root).as_posix()}, inside "
                                f"{owner}'s private Source/ tree; only "
                                "Include/Phoenix/... headers are public "
                                "(v1.0 section 4.3)"
                            )

                if unit != RENDERING_GEM and _is_rendering_header(parts):
                    errors.append(
                        f"{rel}:{number}: '{include}' is a rendering header; "
                        f"rendering integration stays in {RENDERING_GEM} "
                        "(v1.0 section 4.3)"
                    )
                if unit != NETWORKING_GEM and parts[0] == MULTIPLAYER_ROOT:
                    errors.append(
                        f"{rel}:{number}: '{include}' is a Multiplayer header; "
                        f"replication and authority stay in {NETWORKING_GEM} "
                        "(v1.0 section 4.3)"
                    )

    return scanned_files, scanned_includes


def _unit_of(path: Path, root: Path) -> str | None:
    parts = path.relative_to(root).parts
    if parts[0] == "gems" and len(parts) > 1:
        return parts[1]
    if parts[0] == "project":
        return "project"
    return None


# --------------------------------------------------------------------------
# Rule 3: no unregistered AutoComponents
# --------------------------------------------------------------------------


def check_autogen_registration(root: Path, errors: list[str]) -> tuple[int, int]:
    code = root / "project" / "Code"
    cmake_file = code / "Phoenix_autogen_files.cmake"
    autogen_dir = code / "Source" / "AutoGen"

    on_disk = {
        path.relative_to(code).as_posix()
        for path in sorted(autogen_dir.glob("*.AutoComponent.xml"))
    }

    if not cmake_file.is_file():
        errors.append(f"{cmake_file.relative_to(root).as_posix()}: missing")
        return 0, len(on_disk)

    block = AUTOGEN_SET_BLOCK.search(cmake_file.read_text(encoding="utf-8"))
    if block is None:
        errors.append(
            f"{cmake_file.relative_to(root).as_posix()}: no "
            "set(PHOENIX_AUTOGEN_FILES ...) block; nothing would generate"
        )
        return 0, len(on_disk)

    declared: list[str] = []
    for line in block.group(1).splitlines():
        entry = line.split("#", 1)[0].strip()
        if entry:
            declared += entry.split()

    cmake_rel = cmake_file.relative_to(root).as_posix()
    for entry in declared:
        if not (code / entry).is_file():
            errors.append(f"{cmake_rel}: declares missing path '{entry}'")
    for path in sorted(on_disk - set(declared)):
        errors.append(
            f"project/Code/{path} is not listed in {cmake_rel}; O3DE generates "
            "only what that list names, so the component silently never exists"
        )

    return len(declared), len(on_disk)


# --------------------------------------------------------------------------
# Rule 4: no missing owners
# --------------------------------------------------------------------------


def _is_catch_all(pattern: str) -> bool:
    return pattern.strip("/") in ("*", "**")


def covers_area(pattern: str, area: str) -> bool:
    """True when a CODEOWNERS pattern claims a whole top-level area.

    A pattern that reaches into the area (`gems/PhoenixCore/`) deliberately
    does not count: it leaves the rest of the area unowned, which is exactly
    the gap this rule exists to find.
    """
    anchored = pattern.strip("/")
    if _is_catch_all(anchored):
        return True
    head, _, tail = anchored.partition("/")
    return fnmatch.fnmatch(area, head) and tail in ("", "*", "**")


def check_codeowners(root: Path, errors: list[str], warnings: list[str]) -> int:
    present = [root / location for location in CODEOWNERS_LOCATIONS]
    found = next((path for path in present if path.is_file()), None)
    if found is None:
        errors.append(
            "no CODEOWNERS file in any of "
            f"{', '.join(CODEOWNERS_LOCATIONS)}; no area has a named reviewer"
        )
        return 0

    rel = found.relative_to(root).as_posix()
    patterns: list[str] = []
    catch_alls: list[str] = []
    for number, raw in enumerate(found.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        pattern, *owners = line.split()
        if not owners:
            errors.append(f"{rel}:{number}: pattern '{pattern}' has no owner")
            continue
        patterns.append(pattern)
        if _is_catch_all(pattern):
            catch_alls.append(pattern)

    checked = 0
    only_catch_all: list[str] = []
    for area in OWNED_AREAS:
        if not (root / area).is_dir():
            continue
        checked += 1
        covering = [p for p in patterns if covers_area(p, area)]
        if not covering:
            errors.append(f"{rel}: no pattern covers the top-level area '{area}/'")
        elif all(_is_catch_all(p) for p in covering):
            only_catch_all.append(area)

    if only_catch_all:
        # Reported rather than failed: a catch-all is real coverage, but the
        # rule exists to find areas with no named owner, and a catch-all
        # names the same owner for everything. Passing silently here would
        # hide precisely what the rule was written to surface.
        warnings.append(
            f"{rel}: {len(only_catch_all)} of {checked} top-level areas "
            f"({', '.join(f'{a}/' for a in only_catch_all)}) are covered only by "
            f"the catch-all pattern {' '.join(sorted(set(catch_alls)))} and have "
            "no named owner of their own; this is a weak pass"
        )

    return checked


def main() -> None:
    errors: list[str] = []
    warnings: list[str] = []

    gems, edges = check_gem_cycles(ROOT, errors)
    files, includes = check_forbidden_includes(ROOT, errors)
    declared, autogen = check_autogen_registration(ROOT, errors)
    areas = check_codeowners(ROOT, errors, warnings)

    for warning in warnings:
        print(f"WARNING: {warning}", file=sys.stderr)

    if errors:
        print(
            f"Architecture validation FAILED ({len(errors)} problems):",
            file=sys.stderr,
        )
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)

    print(
        f"Architecture validation passed ({gems} gems and {edges} internal "
        f"dependency edges acyclic, {includes} includes in {files} source files, "
        f"{autogen} AutoComponent XMLs against {declared} declared paths, "
        f"{areas} top-level areas owned, {len(warnings)} "
        f"{'warning' if len(warnings) == 1 else 'warnings'})."
    )


if __name__ == "__main__":
    main()
