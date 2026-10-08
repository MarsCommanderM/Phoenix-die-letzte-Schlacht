"""Phase 0 bring-up: take a machine with O3DE from nothing to a configured build.

Everything in this repository so far has been checked *without* an engine.
`scripts/check_cmake.py` configures all 18 CMakeLists.txt against stubs of the
verified engine API, which shows the build structure is well formed -- not
that the game builds. This script is the first step that needs the real
engine, and it is written for the one session in which that step happens,
where guessing a command costs an hour.

So it does four things in order, refuses to continue past a failure it cannot
interpret, and writes everything it learned to a report file that can be read
somewhere else:

  1. probe    What this machine actually is. Never guessed: every value is
              measured or recorded as unknown.
  2. verdict  Whether the probed machine can do the work, as blockers and
              warnings with reasons rather than a yes/no.
  3. register The engine and the project, with the O3DE CLI.
  4. enable   The eight Phoenix gems. Their gem.json dependencies pull the
              engine gems in, so those are not enabled individually.
  5. configure  cmake, through the preset that fits the probed machine.

Three things it is built around, each of which has cost somebody a day:

**Nothing is enabled yet.** project/Code/enabled_gems.cmake is a comment and
nothing else, by design -- it is an O3DE-managed file this repository does not
hand-maintain. A cmake configure run before `enable-gem` succeeds and
produces a project with no Phoenix code in it. That looks like progress and
is not, which is why enabling comes before configuring here and is verified
afterwards.

**Persistent storage is not the default.** On a hosted studio (Lightning AI
and friends) the home directory and /tmp are thrown away when the instance
stops, while a specific path is kept. Building O3DE and leaving it outside
that path means doing it again tomorrow. The probe therefore locates the
persistent root and says plainly whether the engine and the build directory
are inside it.

**A GPU does not compile anything.** Building the engine is CPU, RAM and disk
work. On a platform that bills GPU time and lets the compute be switched, the
build belongs on the cheapest machine with the most cores, and the GPU gets
attached later to run something that renders. The probe reports an attached
GPU as a *warning* for that reason.

What this script cannot do is prove itself. There is no O3DE in the
environment it was written in, so the steps that invoke the engine CLI are
unexercised and the first real run should be expected to find mistakes in
them. The parts that can be tested without an engine are tested in
tests/Unit/test_bringup.py: version parsing, the verdict rules, command
construction, the persistent-root search and the failure diagnosis. The
design compensates for the rest by being loud: every step states its command,
checks its own precondition, and on failure prints the engine's stderr
verbatim next to the most likely cause rather than a traceback.

Start with `--probe-only`. It touches nothing.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _repo import ROOT, gem_dirs  # noqa: E402

PROJECT = ROOT / "project"

#: Free space to insist on before starting, in GB. A planning figure, not a
#: published O3DE minimum: the engine source, its 3rdParty downloads and one
#: build configuration together are what consume it, and the real number
#: depends on which gems are enabled. The probe reports actual free space, so
#: this only decides whether the run stops; --min-free-gb overrides it.
DEFAULT_MIN_FREE_GB = 120

#: Likewise a planning figure. Linking the engine is the memory-hungry part.
DEFAULT_MIN_RAM_GB = 16

#: Paths that are kept when a hosted studio stops. Ordered most specific
#: first. Lightning AI Studio keeps /teamspace; several others keep /workspace.
PERSISTENT_CANDIDATES = (
    "/teamspace/studios/this_studio",
    "/teamspace",
    "/workspace",
    "/persistent",
)

#: Where the engine CLI lives inside an engine checkout, per platform.
ENGINE_CLI = {"Linux": "scripts/o3de.sh", "Darwin": "scripts/o3de.sh", "Windows": "scripts/o3de.bat"}

#: Engine gems the Phoenix gems depend on. Enabled transitively through each
#: gem.json, listed here only so the report can state what should appear.
EXPECTED_ENGINE_GEMS = (
    "Atom",
    "AudioSystem",
    "EMotionFX",
    "LyShine",
    "Multiplayer",
    "PhysX5",
    "RecastNavigation",
    "SaveData",
)

VERSION_NUMBER = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")

#: Engine and cmake failures worth translating. Matched case-insensitively
#: against combined stdout+stderr, first match wins, so order by specificity.
DIAGNOSES = (
    (
        "already registered",
        "Already registered. Not an error -- this step is idempotent.",
    ),
    (
        "could not find an engine",
        "The engine path is not a registered O3DE engine. Run this script's "
        "register step with --engine pointing at the engine checkout root "
        "(the directory containing scripts/o3de.sh).",
    ),
    (
        "no such file or directory",
        "A path does not exist. Check --engine and that the project is at "
        f"{PROJECT}.",
    ),
    (
        "o3de_gem_setup",
        "The engine's CMake API was reached but a gem did not set itself up. "
        "This is the repository's own CMake and is in scope to fix: send the "
        "report back.",
    ),
    (
        "gem.json",
        "A gem manifest was rejected. scripts/validate.py passes locally, so "
        "the engine expects a field this repository does not declare: send "
        "the report back.",
    ),
    (
        "compatible_engines",
        "The project pins o3de==26.05.0 (project/project.json). A different "
        "engine version will refuse. Either check out engine tag 2605.0 or "
        "raise the pin deliberately -- ADR-0001 is the decision record.",
    ),
    (
        "could not find package",
        "cmake could not resolve a dependency the engine normally provides. "
        "Usually a missing 3rdParty download or an engine that has not been "
        "bootstrapped yet.",
    ),
    (
        "no space left on device",
        "Out of disk. Nothing partial is worth keeping: free space and start "
        "the step again.",
    ),
    (
        "permission denied",
        "A path is not writable by this user, or scripts/o3de.sh is not "
        "executable (chmod +x).",
    ),
)


@dataclass
class Facts:
    """What the machine is. Every field is measured or None, never assumed."""

    system: str | None = None
    release: str | None = None
    machine: str | None = None
    cpu_count: int | None = None
    ram_gb: float | None = None
    free_gb: float | None = None
    free_gb_path: str | None = None
    python: str | None = None
    cmake: tuple[int, ...] | None = None
    ninja: tuple[int, ...] | None = None
    clang: tuple[int, ...] | None = None
    gcc: tuple[int, ...] | None = None
    git: tuple[int, ...] | None = None
    has_display: bool = False
    has_vulkan: bool = False
    gpu: str | None = None
    persistent_root: str | None = None
    repo_persistent: bool | None = None
    engine: str | None = None
    engine_cli: str | None = None
    unknown: list[str] = field(default_factory=list)


@dataclass
class Verdict:
    level: str  # "blocker" | "warning" | "note"
    subject: str
    detail: str


def parse_version(text: str) -> tuple[int, ...] | None:
    """First dotted version in text, as a tuple. None when there is none.

    Written to survive the different shapes these tools print:
    `cmake version 3.28.3`, `1.11.1`, `Ubuntu clang version 18.1.3 (1ubuntu1)`,
    `git version 2.55.0`.
    """
    match = VERSION_NUMBER.search(text or "")
    if match is None:
        return None
    return tuple(int(part) for part in match.groups() if part is not None)


def tool_version(name: str, flag: str = "--version") -> tuple[int, ...] | None:
    path = shutil.which(name)
    if path is None:
        return None
    try:
        result = subprocess.run(
            [path, flag], capture_output=True, text=True, timeout=30, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_version(result.stdout or result.stderr)


def find_persistent_root(candidates=PERSISTENT_CANDIDATES, exists=None) -> str | None:
    """The first candidate path that exists.

    `exists` is injectable so the search is testable without those paths
    being present, which they are not in a container.
    """
    check = exists if exists is not None else (lambda p: Path(p).is_dir())
    for candidate in candidates:
        if check(candidate):
            return candidate
    return None


def read_ram_gb() -> float | None:
    """Total RAM in GB from /proc/meminfo, or None off Linux."""
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                return round(int(line.split()[1]) / 1024 / 1024, 1)
    except (OSError, ValueError, IndexError):
        return None
    return None


def detect_gpu() -> str | None:
    """The GPU name from nvidia-smi, or None. Absence is not an error here."""
    path = shutil.which("nvidia-smi")
    if path is None:
        return None
    try:
        result = subprocess.run(
            [path, "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    name = (result.stdout or "").strip().splitlines()
    return name[0].strip() if name and name[0].strip() else None


def find_engine(explicit: str | None) -> tuple[str | None, str | None]:
    """(engine root, CLI path). Explicit wins; otherwise ask the O3DE manifest.

    No search of likely directories: a wrong engine found by guessing is worse
    than none found at all, because the run proceeds against it.
    """
    cli_relative = ENGINE_CLI.get(platform.system(), "scripts/o3de.sh")

    if explicit:
        root = Path(explicit).expanduser().resolve()
        cli = root / cli_relative
        return str(root), str(cli) if cli.is_file() else None

    manifest = Path.home() / ".o3de" / "o3de_manifest.json"
    try:
        document = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, None
    engines = document.get("engines") or []
    for entry in engines:
        root = Path(entry if isinstance(entry, str) else entry.get("path", ""))
        cli = root / cli_relative
        if cli.is_file():
            return str(root), str(cli)
    return (str(Path(engines[0])) if engines else None), None


def probe(engine: str | None = None) -> Facts:
    facts = Facts()
    facts.system = platform.system()
    facts.release = platform.release()
    facts.machine = platform.machine()
    facts.cpu_count = os.cpu_count()
    facts.python = platform.python_version()

    facts.ram_gb = read_ram_gb()
    if facts.ram_gb is None:
        facts.unknown.append("ram_gb (no readable /proc/meminfo)")

    try:
        usage = shutil.disk_usage(ROOT)
        facts.free_gb = round(usage.free / 1024**3, 1)
        facts.free_gb_path = str(ROOT)
    except OSError as exc:
        facts.unknown.append(f"free_gb ({exc})")

    facts.cmake = tool_version("cmake")
    facts.ninja = tool_version("ninja")
    facts.clang = tool_version("clang")
    facts.gcc = tool_version("gcc")
    facts.git = tool_version("git")

    facts.has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    facts.has_vulkan = shutil.which("vulkaninfo") is not None
    facts.gpu = detect_gpu()

    facts.persistent_root = find_persistent_root()
    if facts.persistent_root:
        facts.repo_persistent = str(ROOT).startswith(facts.persistent_root)

    facts.engine, facts.engine_cli = find_engine(engine)
    return facts


def classify(facts: Facts, min_free_gb: int, min_ram_gb: int) -> list[Verdict]:
    """Turn facts into blockers and warnings. Pure, so it is testable."""
    out: list[Verdict] = []

    if facts.engine_cli is None:
        out.append(
            Verdict(
                "blocker",
                "engine",
                "No O3DE engine CLI found. Pass --engine <engine root>, the "
                "directory holding scripts/o3de.sh. Nothing past the probe can run.",
            )
        )
    if facts.cmake is None:
        out.append(Verdict("blocker", "cmake", "cmake is not on PATH."))
    elif facts.cmake < (3, 22):
        out.append(
            Verdict("blocker", "cmake", f"cmake {facts.cmake} is below the 3.22 the project requires.")
        )
    if facts.clang is None and facts.gcc is None:
        out.append(Verdict("blocker", "compiler", "Neither clang nor gcc is on PATH."))
    if facts.free_gb is not None and facts.free_gb < min_free_gb:
        out.append(
            Verdict(
                "blocker",
                "disk",
                f"{facts.free_gb} GB free at {facts.free_gb_path}; this run plans for "
                f"{min_free_gb} GB. Engine source, 3rdParty downloads and one build "
                "configuration all land on this disk. Raise --min-free-gb only if you "
                "know the real figure for your gem set.",
            )
        )

    if facts.ram_gb is not None and facts.ram_gb < min_ram_gb:
        out.append(
            Verdict(
                "warning",
                "ram",
                f"{facts.ram_gb} GB RAM, below the {min_ram_gb} GB this run plans for. "
                "Linking is the hungry step; it may be killed. Reduce parallelism.",
            )
        )
    if facts.persistent_root is None:
        out.append(
            Verdict(
                "warning",
                "persistence",
                "No known persistent path found (" + ", ".join(PERSISTENT_CANDIDATES) + "). "
                "On a hosted studio, work outside the persistent path is discarded when "
                "the instance stops. Confirm where this machine keeps data before "
                "spending hours on a build.",
            )
        )
    elif facts.repo_persistent is False:
        out.append(
            Verdict(
                "warning",
                "persistence",
                f"This repository is at {ROOT}, outside the persistent root "
                f"{facts.persistent_root}. Move the repository and the engine inside it, "
                "or the next stop discards both.",
            )
        )
    if facts.engine and facts.persistent_root and not str(facts.engine).startswith(
        facts.persistent_root
    ):
        out.append(
            Verdict(
                "warning",
                "persistence",
                f"The engine at {facts.engine} is outside the persistent root "
                f"{facts.persistent_root}. Building it there means building it again "
                "after the next stop.",
            )
        )
    if facts.gpu:
        out.append(
            Verdict(
                "warning",
                "gpu",
                f"A GPU is attached ({facts.gpu}), and compiling uses none of it. If this "
                "platform bills GPU time and lets compute be switched, build on the "
                "cheapest machine with the most cores and attach the GPU only to run "
                "something that renders.",
            )
        )
    if not facts.has_display:
        out.append(
            Verdict(
                "note",
                "display",
                "No DISPLAY or WAYLAND_DISPLAY. The O3DE Editor needs a display and will "
                "not start. The dedicated server and the Asset Processor do not, and the "
                "linux-server preset is the right target here.",
            )
        )
    if not facts.has_vulkan:
        out.append(
            Verdict(
                "note",
                "vulkan",
                "vulkaninfo not found. Atom renders through Vulkan, so anything that "
                "renders needs the Vulkan loader and a driver. Irrelevant for a "
                "server-only build.",
            )
        )
    if facts.ninja is None:
        out.append(
            Verdict(
                "note",
                "ninja",
                "ninja is not on PATH. The linux-server preset asks for Ninja "
                "Multi-Config and will fail to configure without it.",
            )
        )
    if facts.cpu_count:
        out.append(
            Verdict("note", "cores", f"{facts.cpu_count} cores available for the build.")
        )
    return out


def preset_for(facts: Facts) -> str | None:
    """The CMakePresets entry that fits this machine.

    Only two configure presets exist: windows-client and linux-server. A
    headless Linux box maps to linux-server, which is also the only Linux
    preset -- stated here rather than silently defaulted.
    """
    if facts.system == "Windows":
        return "windows-client"
    if facts.system == "Linux":
        return "linux-server"
    return None


@dataclass
class Step:
    name: str
    why: str
    command: list[str]
    allow_failure: bool = False


def plan(facts: Facts, preset: str | None) -> list[Step]:
    """The commands to run, in order. Pure, so the shapes are testable."""
    cli = facts.engine_cli or "o3de"
    steps = [
        Step(
            "register engine",
            "Puts this engine in ~/.o3de/o3de_manifest.json so a project can resolve it.",
            [cli, "register", "--this-engine"],
        ),
        Step(
            "register project",
            "Makes the engine aware of the Phoenix project path.",
            [cli, "register", "-pp", str(PROJECT)],
        ),
    ]
    for gem in gem_dirs():
        steps.append(
            Step(
                f"enable {gem.name}",
                "enabled_gems.cmake is empty by design; without this the configure "
                "produces a project containing no Phoenix code.",
                [cli, "enable-gem", "-gn", gem.name, "-pp", str(PROJECT)],
            )
        )
    if preset:
        steps.append(
            Step(
                f"configure {preset}",
                "The first cmake run against the real engine rather than the stubs in "
                "scripts/check_cmake.py.",
                ["cmake", "--preset", preset, "-S", str(ROOT)],
            )
        )
    return steps


def diagnose(output: str) -> str | None:
    """The most likely cause of a failure, from its own output."""
    lowered = (output or "").lower()
    for needle, explanation in DIAGNOSES:
        if needle in lowered:
            return explanation
    return None


def run_step(step: Step, dry_run: bool) -> dict:
    printable = " ".join(step.command)
    print(f"\n--- {step.name}")
    print(f"    why: {step.why}")
    print(f"    run: {printable}")
    if dry_run:
        print("    (dry run, not executed)")
        return {"step": step.name, "command": printable, "status": "skipped-dry-run"}

    try:
        result = subprocess.run(step.command, capture_output=True, text=True, check=False)
    except OSError as exc:
        print(f"    FAILED to launch: {exc}", file=sys.stderr)
        return {
            "step": step.name,
            "command": printable,
            "status": "launch-failed",
            "error": str(exc),
        }

    combined = (result.stdout or "") + (result.stderr or "")
    record = {
        "step": step.name,
        "command": printable,
        "status": "ok" if result.returncode == 0 else "failed",
        "returncode": result.returncode,
        "output": combined[-8000:],
    }
    if result.returncode == 0:
        print("    ok")
    else:
        print(f"    FAILED (exit {result.returncode})", file=sys.stderr)
        # Verbatim, not summarised: the exact text is what gets pasted back.
        for line in combined.strip().splitlines()[-25:]:
            print(f"      | {line}", file=sys.stderr)
        cause = diagnose(combined)
        if cause:
            record["diagnosis"] = cause
            print(f"    likely cause: {cause}", file=sys.stderr)
        else:
            print(
                "    No known cause for this output. Send the report file back; "
                "this is the useful kind of failure.",
                file=sys.stderr,
            )
    return record


def verify_gems_enabled() -> tuple[list[str], list[str]]:
    """(enabled, missing) Phoenix gems, read from enabled_gems.cmake.

    The step that reported success and the file that proves it are different
    things. enable-gem exiting 0 while writing nothing is exactly the class of
    failure this repository keeps finding, so the file is read back.
    """
    path = PROJECT / "Code" / "enabled_gems.cmake"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return [], [gem.name for gem in gem_dirs()]
    body = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )
    enabled, missing = [], []
    for gem in gem_dirs():
        (enabled if gem.name in body else missing).append(gem.name)
    return enabled, missing


def render_report(facts: Facts, verdicts: list[Verdict], records: list[dict]) -> str:
    lines = ["# Phoenix Phase 0 bring-up report", ""]
    lines.append("## Machine")
    for key, value in asdict(facts).items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Verdicts")
    if not verdicts:
        lines.append("- none")
    for verdict in verdicts:
        lines.append(f"- [{verdict.level}] {verdict.subject}: {verdict.detail}")
    lines.append("")
    lines.append("## Steps")
    if not records:
        lines.append("- none run")
    for record in records:
        lines.append(f"### {record['step']} -- {record['status']}")
        lines.append(f"`{record['command']}`")
        if record.get("diagnosis"):
            lines.append(f"Likely cause: {record['diagnosis']}")
        if record.get("output"):
            lines.append("```")
            lines.append(record["output"].strip())
            lines.append("```")
        lines.append("")
    lines.append("## Expected engine gems (pulled in through gem.json dependencies)")
    lines.append(", ".join(EXPECTED_ENGINE_GEMS))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--engine", help="engine checkout root (holds scripts/o3de.sh)")
    parser.add_argument(
        "--probe-only",
        action="store_true",
        help="report the machine and stop. Touches nothing. Start here.",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="print every command without running it"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="run the steps even with blockers. Only when you know the blocker is wrong.",
    )
    parser.add_argument("--min-free-gb", type=int, default=DEFAULT_MIN_FREE_GB)
    parser.add_argument("--min-ram-gb", type=int, default=DEFAULT_MIN_RAM_GB)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "build" / "bringup-report.md",
        help="where to write the report to send back",
    )
    args = parser.parse_args(argv)

    facts = probe(args.engine)
    verdicts = classify(facts, args.min_free_gb, args.min_ram_gb)
    preset = preset_for(facts)

    print("Phoenix Phase 0 bring-up\n")
    print(f"  system        {facts.system} {facts.release} ({facts.machine})")
    print(f"  cores / ram   {facts.cpu_count} / {facts.ram_gb} GB")
    print(f"  free disk     {facts.free_gb} GB at {facts.free_gb_path}")
    print(f"  persistent    {facts.persistent_root} (repo inside: {facts.repo_persistent})")
    print(f"  engine        {facts.engine or 'not found'}")
    print(f"  engine cli    {facts.engine_cli or 'not found'}")
    print(f"  preset        {preset or 'none for this platform'}")
    if facts.unknown:
        print(f"  not measured  {', '.join(facts.unknown)}")

    blockers = [v for v in verdicts if v.level == "blocker"]
    for verdict in verdicts:
        marker = {"blocker": "BLOCKER", "warning": "warning", "note": "note"}[verdict.level]
        print(f"\n[{marker}] {verdict.subject}: {verdict.detail}")

    records: list[dict] = []
    if args.probe_only:
        print("\nProbe only; nothing was changed.")
    elif blockers and not args.force:
        print(
            f"\nStopping: {len(blockers)} blocker(s). Fix them, or pass --force if a "
            "blocker is wrong about this machine.",
            file=sys.stderr,
        )
    elif preset is None and not args.force:
        print(
            f"\nStopping: no CMakePresets configure preset for {facts.system}. "
            "CMakePresets.json defines windows-client and linux-server only.",
            file=sys.stderr,
        )
    else:
        for step in plan(facts, preset):
            records.append(run_step(step, args.dry_run))
            if records[-1]["status"] in {"failed", "launch-failed"}:
                print(
                    "\nStopping at the first failure: later steps depend on it and "
                    "would fail for the wrong reason.",
                    file=sys.stderr,
                )
                break

        if not args.dry_run:
            enabled, missing = verify_gems_enabled()
            print(f"\nenabled_gems.cmake names: {', '.join(enabled) or 'nothing'}")
            if missing:
                print(
                    f"NOT enabled: {', '.join(missing)}. A configure run now would build "
                    "a project without that code in it.",
                    file=sys.stderr,
                )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(facts, verdicts, records), encoding="utf-8")
    print(f"\nReport: {args.report}")
    print("Send that file back. It holds every command, its output and the machine's facts.")

    failed = [r for r in records if r["status"] in {"failed", "launch-failed"}]
    raise SystemExit(1 if (failed or (blockers and not args.force)) else 0)


if __name__ == "__main__":
    main()
