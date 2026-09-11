"""Read-only persistence detection and baseline comparison.

Collectors intentionally use standard-library APIs and best-effort discovery.  A
collector failing (or running on an unsupported platform) never prevents the
other collectors from producing a report.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import platform
import plistlib
import shlex
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True, slots=True)
class PersistenceEntry:
    name: str
    mechanism: str
    executable_path: str = ""
    process_name: str = ""
    creation_time: str | None = None
    digital_signature_status: str = "unknown"
    risk_level: str = "low"
    suspiciousness_explanation: str = ""
    source: str = ""

    @property
    def identity(self) -> str:
        return "|".join((self.mechanism, self.name, self.executable_path))


@dataclass(slots=True)
class DetectionReport:
    platform: str
    entries: list[PersistenceEntry] = field(default_factory=list)
    new_entries: list[PersistenceEntry] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    baseline_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "entries": [asdict(x) for x in self.entries],
            "new_entries": [asdict(x) for x in self.new_entries],
            "unsupported": self.unsupported,
            "baseline_path": self.baseline_path,
        }


def _time_for(path: Path) -> str | None:
    try:
        info = path.stat()
        timestamp = getattr(info, "st_birthtime", info.st_ctime)
        return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
    except (OSError, ValueError, OverflowError):
        return None


def _signature(path: str, system: str) -> str:
    if not path:
        return "unknown"
    if system == "Windows":
        command = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
                   "(Get-AuthenticodeSignature -LiteralPath $args[0]).Status", path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=5,
                                    check=False)
            value = result.stdout.strip().lower()
            return {"valid": "valid", "nottrusted": "invalid", "hashmismatch": "invalid"}.get(
                value, "unknown"
            )
        except (OSError, subprocess.SubprocessError):
            return "unknown"
    if system == "Darwin" and shutil.which("codesign"):
        try:
            result = subprocess.run(["codesign", "--verify", "--deep", path],
                                    capture_output=True, timeout=5, check=False)
            return "valid" if result.returncode == 0 else "invalid"
        except (OSError, subprocess.SubprocessError):
            return "unknown"
    return "unknown"


def _risk(name: str, executable: str, signature: str) -> tuple[str, str]:
    text = f"{name} {executable}".lower()
    reasons: list[str] = []
    if any(part in text for part in ("/tmp/", "/var/tmp/", "\\temp\\", "appdata\\local\\temp")):
        reasons.append("runs from a temporary directory")
    if any(word in text for word in ("download", "powershell", "wscript", "mshta", "curl", "wget")):
        reasons.append("contains a script or download utility")
    if signature == "invalid":
        reasons.append("digital signature is invalid")
    if signature == "unknown":
        reasons.append("digital signature could not be verified")
    if reasons:
        return ("high" if signature == "invalid" or "temporary" in reasons[0] else "medium",
                "; ".join(reasons))
    return "low", "no immediately suspicious indicators found"


def _entry(name: str, mechanism: str, path: str = "", source: str = "",
           system: str | None = None) -> PersistenceEntry:
    system = system or platform.system()
    signature = _signature(path, system)
    risk, explanation = _risk(name, path, signature)
    file_path = Path(path) if path else None
    source_path = Path(source) if source else None
    creation_path = source_path if source_path and source_path.exists() else file_path
    return PersistenceEntry(name=name, mechanism=mechanism, executable_path=path,
                            process_name=Path(path).name if path else name,
                            creation_time=_time_for(creation_path) if creation_path else None,
                            digital_signature_status=signature, risk_level=risk,
                            suspiciousness_explanation=explanation, source=source)


def _linux(root: Path) -> tuple[list[PersistenceEntry], list[str]]:
    entries: list[PersistenceEntry] = []
    unsupported: list[str] = []
    unit_dirs = [root / "etc/systemd/system", root / "usr/lib/systemd/system",
                 root / "lib/systemd/system"]
    for directory in unit_dirs:
        if directory.is_dir():
            for path in directory.glob("*.service"):
                command = ""
                try:
                    for line in path.read_text(errors="replace").splitlines():
                        if line.startswith("ExecStart="):
                            try:
                                command = shlex.split(line.split("=", 1)[1])[0]
                                command = command.lstrip("-@+:")
                            except ValueError:
                                command = line.split("=", 1)[1].strip().split()[0]
                            break
                except OSError:
                    pass
                entries.append(_entry(path.name, "system_service", command,
                                      str(path), "Linux"))
    for directory in (root / "etc/cron.d", root / "etc/cron.daily", root / "etc/cron.hourly",
                      root / "etc/cron.weekly", root / "etc/cron.monthly"):
        if directory.is_dir():
            for path in directory.iterdir():
                if path.is_file() and not path.name.startswith("."):
                    entries.append(_entry(path.name, "scheduled_task", str(path), str(path), "Linux"))
    startup_directories = [
        root / "etc/xdg/autostart",
        root / "etc/profile.d",
    ]
    for home in (root / "home").glob("*"):
        startup_directories.append(home / ".config/autostart")
    for path in (root / "etc/rc.local",):
        if path.is_file():
            entries.append(_entry(path.name, "startup_application", str(path), str(path), "Linux"))
    for directory in startup_directories:
        if directory.is_dir():
            for child in directory.iterdir():
                if child.is_file() and not child.name.startswith("."):
                    entries.append(_entry(child.name, "startup_application", str(child),
                                          str(child), "Linux"))
    return entries, unsupported


def _darwin(root: Path) -> tuple[list[PersistenceEntry], list[str]]:
    entries: list[PersistenceEntry] = []
    for directory, mechanism in (
        (root / "System/Library/LaunchDaemons", "system_service"),
        (root / "Library/LaunchDaemons", "system_service"),
        (root / "Library/LaunchAgents", "startup_application"),
        (root / "System/Library/LaunchAgents", "login_item"),
    ):
        if not directory.is_dir():
            continue
        for path in directory.glob("*.plist"):
            executable = ""
            try:
                data = plistlib.loads(path.read_bytes())
                args = data.get("ProgramArguments") or []
                executable = str(args[0]) if args else str(data.get("Program", ""))
            except (OSError, plistlib.InvalidFileException, ValueError):
                pass
            entries.append(_entry(path.stem, mechanism, executable, str(path), "Darwin"))
    return entries, []


def _windows() -> tuple[list[PersistenceEntry], list[str]]:
    # Registry access is deliberately read-only.  Importing winreg on other
    # platforms is avoided so this module remains importable everywhere.
    entries: list[PersistenceEntry] = []
    unsupported: list[str] = []
    try:
        import winreg  # type: ignore
        roots = ((winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
                 (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run"))
        for root, key_name in roots:
            try:
                with winreg.OpenKey(root, key_name) as key:
                    for index in range(winreg.QueryInfoKey(key)[1]):
                        name, value, _ = winreg.EnumValue(key, index)
                        entries.append(_entry(name, "autorun_entry", str(value), key_name, "Windows"))
            except OSError:
                continue
    except ImportError:
        unsupported.append("Windows registry")
    # These commands only query the service/task databases.  Keep each
    # collector independent because restricted Windows environments commonly
    # deny one of them.
    try:
        result = subprocess.run(["schtasks", "/query", "/fo", "csv", "/v"],
                                capture_output=True, text=True, timeout=10, check=False)
        for row in csv.DictReader(io.StringIO(result.stdout)):
            name = row.get("TaskName", "").strip()
            command = row.get("Task To Run", "").strip()
            if name:
                entries.append(_entry(name, "scheduled_task", command, "schtasks", "Windows"))
    except (OSError, subprocess.SubprocessError):
        unsupported.append("Windows scheduled tasks")
    try:
        result = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command",
                                 "Get-CimInstance Win32_Service | Select Name,PathName | ConvertTo-Json -Compress"],
                                capture_output=True, text=True, timeout=10, check=False)
        values = json.loads(result.stdout or "[]")
        if isinstance(values, dict):
            values = [values]
        for value in values:
            name, command = str(value.get("Name", "")), str(value.get("PathName", ""))
            if name:
                entries.append(_entry(name, "system_service", command, "Win32_Service", "Windows"))
    except (OSError, subprocess.SubprocessError, ValueError, TypeError):
        unsupported.append("Windows services")
    startup_roots = [
        Path(value) / "Microsoft/Windows/Start Menu/Programs/Startup"
        for value in (os.environ.get("APPDATA"), os.environ.get("PROGRAMDATA"))
        if value
    ]
    for directory in startup_roots:
        if not directory.is_dir():
            continue
        try:
            for path in directory.iterdir():
                if path.is_file():
                    entries.append(_entry(path.name, "startup_application", str(path),
                                          str(path), "Windows"))
        except OSError:
            unsupported.append(f"Windows startup folder: {directory}")
    return entries, unsupported


def collect_entries(system: str | None = None, root: str | os.PathLike[str] = "/") -> tuple[list[PersistenceEntry], list[str]]:
    system = system or platform.system()
    root_path = Path(root)
    if system == "Linux":
        return _linux(root_path)
    if system == "Darwin":
        return _darwin(root_path)
    if system == "Windows":
        return _windows()
    return [], [f"unsupported platform: {system}"]


def load_baseline(path: str | os.PathLike[str]) -> set[str]:
    try:
        data = json.loads(Path(path).read_text())
        values = data.get("entries", data) if isinstance(data, dict) else data
        identities = set()
        for item in values:
            if isinstance(item, dict):
                identities.add(item.get("identity") or "|".join((
                    str(item.get("mechanism", "")), str(item.get("name", "")),
                    str(item.get("executable_path", "")),
                )))
            else:
                identities.add(str(item))
        return identities
    except (OSError, ValueError, TypeError, KeyError):
        return set()


def save_baseline(path: str | os.PathLike[str], entries: Iterable[PersistenceEntry]) -> None:
    payload = {"version": 1, "entries": [asdict(entry) for entry in entries]}
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True))


def detect(baseline_path: str | os.PathLike[str] | None = None, *,
           system: str | None = None, root: str | os.PathLike[str] = "/",
           save: bool = False) -> DetectionReport:
    entries, unsupported = collect_entries(system, root)
    baseline = load_baseline(baseline_path) if baseline_path else set()
    new = [entry for entry in entries if entry.identity not in baseline]
    if baseline_path and save:
        save_baseline(baseline_path, entries)
    return DetectionReport(system or platform.system(), entries, new, unsupported,
                           str(baseline_path) if baseline_path else None)


def format_report(report: DetectionReport, json_output: bool = False) -> str:
    if json_output:
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    lines = [f"Persistence detection ({report.platform}): {len(report.entries)} entries, "
             f"{len(report.new_entries)} new"]
    new_ids = {entry.identity for entry in report.new_entries}
    for entry in report.entries:
        marker = "NEW " if entry.identity in new_ids else ""
        lines.append(
            f"- {marker}[{entry.risk_level.upper()}] {entry.mechanism}: {entry.name}\n"
            f"  Process: {entry.process_name or 'unknown'}\n"
            f"  Executable: {entry.executable_path or 'no executable'}\n"
            f"  Created: {entry.creation_time or 'unknown'}\n"
            f"  Signature: {entry.digital_signature_status}\n"
            f"  Why: {entry.suspiciousness_explanation}"
        )
    lines.extend(f"Note: {item}" for item in report.unsupported)
    return "\n".join(lines)


def watch(interval: float = 60.0, *, baseline_path: str | os.PathLike[str] | None = None,
          system: str | None = None, root: str | os.PathLike[str] = "/",
          json_output: bool = False) -> None:
    """Continuously report persistence entries added since the previous scan.

    This is intentionally a foreground, read-only monitor.  It does not create
    a service, task, startup entry, or any other mechanism to keep itself
    running.
    """
    if interval <= 0:
        raise ValueError("watch interval must be greater than zero")

    entries, unsupported = collect_entries(system, root)
    previous = load_baseline(baseline_path) if baseline_path else {
        entry.identity for entry in entries
    }
    initial = DetectionReport(
        system or platform.system(), entries,
        [entry for entry in entries if entry.identity not in previous],
        unsupported, str(baseline_path) if baseline_path else None,
    )
    print(format_report(initial, json_output), flush=True)

    try:
        while True:
            time.sleep(interval)
            entries, unsupported = collect_entries(system, root)
            current = {entry.identity for entry in entries}
            added = [entry for entry in entries if entry.identity not in previous]
            if added or unsupported:
                report = DetectionReport(
                    system or platform.system(), entries, added, unsupported,
                    str(baseline_path) if baseline_path else None,
                )
                print(format_report(report, json_output), flush=True)
            previous = current
    except KeyboardInterrupt:
        return


class PersistenceDetector:
    """Small object-oriented facade for callers that prefer a reusable detector."""

    def __init__(self, system: str | None = None,
                 root: str | os.PathLike[str] = "/") -> None:
        self.system = system
        self.root = root

    def collect(self) -> list[PersistenceEntry]:
        return collect_entries(self.system, self.root)[0]

    def detect(self, baseline_path: str | os.PathLike[str] | None = None,
               save_baseline: bool = False) -> DetectionReport:
        return detect(baseline_path, system=self.system, root=self.root,
                      save=save_baseline)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="darkglitch persistence")
    parser.add_argument("--baseline", help="JSON baseline file")
    parser.add_argument("--save-baseline", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--watch", nargs="?", const=60.0, type=float, metavar="SECONDS",
        help="Keep scanning in the foreground; default interval is 60 seconds",
    )
    args = parser.parse_args(argv)
    if args.watch is not None:
        if args.watch <= 0:
            parser.error("--watch interval must be greater than zero")
        watch(args.watch, baseline_path=args.baseline, json_output=args.json_output)
        return 0
    report = detect(args.baseline, save=args.save_baseline)
    print(format_report(report, args.json_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
