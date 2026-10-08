"""Write a reproducible build manifest: what was built, and from what.

Acceptance criterion 1 of docs/tdd/01-engine-baseline.md is that client and
dedicated-server builds reproduce from a defined commit with identical build
metadata. A list of path/sha256/size cannot support that claim. Hashes
identify the *inputs*; they say nothing about the *build*. The same source
tree compiled against a different engine tag, a different compiler, or a
different platform SDK produces different binaries with an identical file
manifest, so a release investigation that starts from such a manifest cannot
tell two unlike artefacts apart. v5.1 section 249 therefore asks for build
identity alongside the file list, and that is what the "build" block is.

Two defects this script is written to prevent:

1. A fabricated identity. Every field it cannot actually read becomes null
   and gains an entry in "warnings"; nothing is guessed from the machine
   running the script, because the machine that generates a manifest is not
   necessarily the machine that performed the build. A null that is admitted
   can be filled in by the build agent that does know; a plausible-looking
   wrong value is believed and never questioned.

2. A nondeterministic buildId. The id is the sha256 of the manifest's own
   content (sorted file hashes plus the identity block, with the id itself
   excluded), never a timestamp or a random value. A timestamped id would
   differ between two builds of the same commit, which defeats the only
   question the id exists to answer: are these two artefacts the same build?
   tests/Unit/test_manifest.py recomputes the recorded id from the recorded
   content, so a clock sneaking back into this function fails the suite.

The "project" field and the "files" array keep their original shape, because
.github/workflows/release.yml publishes this file as an artefact and anything
downstream already reads those two.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# Make the sibling _repo helper importable regardless of cwd or isolated mode.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _repo import ROOT, gem_dirs, iter_source_files  # noqa: E402

DEFAULT_OUTPUT = ROOT / "build" / "source_manifest.json"

#: Identity fields supplied by the caller. They describe the toolchain that
#: performed the build, which this script has no way to observe, so each one
#: is an argument and each unset one is a recorded gap.
TOOLCHAIN_FIELDS = ("compiler", "sdk", "platform", "configuration")

#: The three independently versioned contracts from docs/tdd/06-data-schemas.md.
#: Keyed by manifest field so the build identity names the contract versions
#: the artefact actually speaks, not the ones HEAD happens to declare later.
CONTRACT_FILES = {
    "saveSchema": "save_schema.json",
    "networkProtocol": "network_protocol.json",
    "productVersion": "version.json",
}

#: project.json pins its engine as a PEP-440-style specifier ("o3de==26.05.0").
ENGINE_SPECIFIER = re.compile(r"^o3de==(?P<version>[0-9][0-9A-Za-z.+-]*)$")


def _git(root: Path, *args: str) -> tuple[str | None, str | None]:
    """Run a read-only git command in root as (stdout, reason-it-failed).

    Returning the reason rather than raising is deliberate: a tree exported
    from a tarball has no git metadata, and that is a fact to record, not a
    crash.
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:  # git missing, or not executable on this machine
        return None, f"git is unavailable ({exc.strerror or exc})"
    if result.returncode != 0:
        first_line = next(
            (line for line in result.stderr.splitlines() if line.strip()),
            f"exit status {result.returncode}",
        )
        return None, f"'git {' '.join(args)}' failed: {first_line.strip()}"
    return result.stdout, None


def project_identity(root: Path) -> tuple[str | None, bool | None, list[str]]:
    """The commit the manifest describes, and whether the tree matched it."""
    warnings: list[str] = []

    stdout, reason = _git(root, "rev-parse", "HEAD")
    commit = (stdout or "").strip() or None
    if commit is None:
        warnings.append(
            f"projectCommit is null: {reason or 'git printed no commit'}; the "
            "build agent must supply the commit this artefact was built from"
        )

    stdout, reason = _git(root, "status", "--porcelain")
    if stdout is None:
        dirty = None
        warnings.append(f"projectTreeDirty is null: {reason}")
    else:
        dirty = bool(stdout.strip())
        if dirty:
            # Recording the commit of a dirty tree without saying so is the
            # exact failure this field prevents: the manifest would name a
            # commit that does not reproduce the artefact it describes.
            warnings.append(
                "projectTreeDirty is true: the working tree has uncommitted "
                f"changes, so projectCommit ({commit or 'unknown'}) does not "
                "identify a reproducible build"
            )

    return commit, dirty, warnings


def engine_version(root: Path) -> tuple[str | None, list[str]]:
    """The pinned engine version from project.json's compatible_engines."""
    path = root / "project" / "project.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, [f"engineVersion is null: cannot read {path.name} ({exc})"]
    except json.JSONDecodeError as exc:
        return None, [f"engineVersion is null: {path.name} is invalid JSON ({exc})"]

    engines = document.get("compatible_engines")
    if not isinstance(engines, list) or not engines:
        return None, [
            "engineVersion is null: project/project.json declares no "
            "compatible_engines"
        ]

    versions = []
    for engine in engines:
        match = ENGINE_SPECIFIER.match(engine.strip()) if isinstance(engine, str) else None
        if match:
            versions.append(match.group("version"))

    if len(versions) != 1:
        # A build identity names one engine. Several pins (or none that parse)
        # mean the manifest cannot say which engine produced the artefact, and
        # picking the first would be a guess dressed up as a fact.
        return None, [
            "engineVersion is null: project/project.json compatible_engines "
            f"does not pin exactly one o3de version ({engines!r})"
        ]
    return versions[0], []


def _gem_manifests(root: Path) -> list[Path]:
    """The gem.json files under root, found the way _repo.gem_dirs() finds them.

    Delegating for the repository itself keeps a single definition of "a gem"
    for the committed tree; the fallback exists so the readers here can be
    exercised against a temporary tree in tests.
    """
    if root == ROOT:
        return [gem / "gem.json" for gem in gem_dirs()]
    gems = root / "gems"
    if not gems.is_dir():
        return []
    return sorted(p / "gem.json" for p in gems.iterdir() if (p / "gem.json").is_file())


def gem_versions(root: Path) -> tuple[dict[str, str | None], list[str]]:
    """{gem_name: version} for every gem on disk."""
    warnings: list[str] = []
    versions: dict[str, str | None] = {}
    for path in _gem_manifests(root):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            warnings.append(f"gemVersions: cannot read {path.parent.name}/gem.json ({exc})")
            continue
        # Key on the declared gem_name: that is the name CMake and the engine
        # resolve dependencies by, so it is the name a consumer will look up.
        name = document.get("gem_name") or path.parent.name
        version = document.get("version")
        if not isinstance(version, str) or not version.strip():
            warnings.append(
                f"gemVersions['{name}'] is null: {path.parent.name}/gem.json "
                "declares no version string"
            )
            versions[name] = None
        else:
            versions[name] = version
    if not versions:
        warnings.append("gemVersions is empty: no gems/*/gem.json found")
    return dict(sorted(versions.items())), warnings


def third_party_versions(root: Path) -> tuple[dict[str, str], list[str]]:
    """The pinned Python packages from requirements-dev.txt.

    These are the validation-only dependencies of this repository. The engine's
    own third-party set (the O3DE 3rdParty packages: PhysX, Qt, Python, and the
    rest) is NOT covered here: the engine is not vendored in this tree, so its
    versions are unknowable from here and belong to engineCommit/engineVersion.
    """
    path = root / "requirements-dev.txt"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {}, [f"thirdPartyVersions is empty: cannot read {path.name} ({exc})"]

    warnings: list[str] = []
    pinned: dict[str, str] = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        if not separator or not name.strip() or not version.strip():
            # An unpinned requirement resolves differently on different days,
            # so it cannot be part of a build identity and must not be recorded
            # as though it were.
            warnings.append(
                f"thirdPartyVersions: requirements-dev.txt line {number} "
                f"({line!r}) is not an == pin and was not recorded"
            )
            continue
        pinned[name.strip()] = version.strip()
    return dict(sorted(pinned.items())), warnings


def contract_versions(root: Path, name: str) -> tuple[dict | None, str | None]:
    """A project/Config contract document, or None plus the reason it is absent.

    The three contract files are written and owned elsewhere in the tree. This
    reader records whatever fields they declare, minus "$"-prefixed
    documentation keys, so rewording a $comment does not change the buildId
    while a protocol bump does.
    """
    path = root / "project" / "Config" / name
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"project/Config/{name} does not exist"
    except OSError as exc:
        return None, f"project/Config/{name} cannot be read ({exc})"
    except json.JSONDecodeError as exc:
        return None, f"project/Config/{name} is invalid JSON ({exc})"
    if not isinstance(document, dict):
        return None, f"project/Config/{name} is not a JSON object"
    return {k: v for k, v in document.items() if not k.startswith("$")}, None


def hash_files(root: Path) -> list[dict]:
    """The original file list, unchanged: path, sha256 and size per file."""
    files = []
    for path in iter_source_files() if root == ROOT else sorted(root.rglob("*")):
        if not path.is_file():
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": digest.hexdigest(),
                "size": path.stat().st_size,
            }
        )
    return files


def compute_build_id(files: list[dict], build: dict) -> str:
    """Derive the buildId from the manifest's own content.

    Deliberately content-addressed and nothing else: sorted (path, sha256)
    pairs plus the identity block with buildId removed, serialised
    canonically. Two runs over the same tree and the same identity must agree,
    and any identity field that changes must change the id -- otherwise the id
    cannot distinguish a client build from a dedicated-server build of the
    same commit. "warnings" is excluded because it only ever restates a null
    that is already inside the identity block.
    """
    payload = {
        "files": sorted((entry["path"], entry["sha256"]) for entry in files),
        "build": {key: value for key, value in build.items() if key != "buildId"},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_manifest(root: Path, toolchain: dict[str, str | None]) -> dict:
    """The whole manifest, with every gap it could not fill recorded."""
    warnings: list[str] = []

    commit, dirty, commit_warnings = project_identity(root)
    warnings.extend(commit_warnings)

    engine, engine_warnings = engine_version(root)
    warnings.extend(engine_warnings)

    gems, gem_warnings = gem_versions(root)
    warnings.extend(gem_warnings)

    third_party, third_party_warnings = third_party_versions(root)
    warnings.extend(third_party_warnings)

    for field in TOOLCHAIN_FIELDS:
        if toolchain.get(field) is None:
            warnings.append(
                f"{field} is null: pass --{field} from the build job; it is not "
                "inferred from this machine, which need not be the build machine"
            )

    contracts: dict[str, dict | None] = {}
    for field, name in CONTRACT_FILES.items():
        document, reason = contract_versions(root, name)
        contracts[field] = document
        if document is None:
            warnings.append(f"{field} is null: {reason}")

    # The engine is a separate checkout that this repository does not vendor,
    # so its commit is only knowable to the agent holding that checkout.
    warnings.append(
        "engineCommit is null: the engine is not vendored in this repository; "
        "the build agent with the o3de checkout must supply it"
    )

    build = {
        "buildId": None,
        "projectCommit": commit,
        "projectTreeDirty": dirty,
        "engineVersion": engine,
        "engineCommit": None,
        "compiler": toolchain.get("compiler"),
        "sdk": toolchain.get("sdk"),
        "platform": toolchain.get("platform"),
        "configuration": toolchain.get("configuration"),
        "gemVersions": gems,
        "thirdPartyVersions": third_party,
        "saveSchema": contracts["saveSchema"],
        "networkProtocol": contracts["networkProtocol"],
        "productVersion": contracts["productVersion"],
    }

    files = hash_files(root)
    build["buildId"] = compute_build_id(files, build)

    return {
        "project": "Phoenix",
        "build": build,
        "files": files,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    for field in TOOLCHAIN_FIELDS:
        parser.add_argument(
            f"--{field}",
            default=None,
            help=f"record the build {field}; left null and warned about if omitted",
        )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=(
            "write the manifest here instead of build/source_manifest.json. "
            "Keep it outside the hashed tree: a manifest that hashes itself "
            "has no stable buildId"
        ),
    )
    args = parser.parse_args(argv)

    manifest = build_manifest(
        ROOT, {field: getattr(args, field) for field in TOOLCHAIN_FIELDS}
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    build = manifest["build"]
    if manifest["warnings"]:
        # An unfilled identity field nobody is told about is an identity field
        # nobody fills in. This is not a failure: the build agent completes it.
        print(
            f"Build manifest incomplete ({len(manifest['warnings'])} warnings):",
            file=sys.stderr,
        )
        for warning in manifest["warnings"]:
            print(f"  - {warning}", file=sys.stderr)

    print(
        f"{args.output} ({len(manifest['files'])} files hashed, "
        f"{len(build['gemVersions'])} gem versions, "
        f"{len(build['thirdPartyVersions'])} third-party pins, "
        f"{len(CONTRACT_FILES)} contract files, "
        f"{len(manifest['warnings'])} warnings) buildId {build['buildId']}"
    )


if __name__ == "__main__":
    main()
