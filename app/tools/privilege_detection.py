"""Read-only inventory and baseline comparison for privileged identities."""
from __future__ import annotations

import argparse
import json
import os
import platform
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

try:
    import grp
    import pwd
except ImportError:  # Windows
    grp = None
    pwd = None


@dataclass(frozen=True, slots=True)
class PrivilegeEntry:
    identity: str
    privilege: str
    source: str

    @property
    def key(self) -> str:
        return "|".join((self.identity, self.privilege, self.source))


@dataclass(slots=True)
class PrivilegeReport:
    platform: str
    entries: list[PrivilegeEntry] = field(default_factory=list)
    new_entries: list[PrivilegeEntry] = field(default_factory=list)
    unsupported: list[str] = field(default_factory=list)
    baseline_path: str | None = None

    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "entries": [asdict(entry) for entry in self.entries],
            "new_entries": [asdict(entry) for entry in self.new_entries],
            "unsupported": self.unsupported,
            "baseline_path": self.baseline_path,
        }


def collect_entries(system: str | None = None,
                    root: str | os.PathLike[str] = "/") -> tuple[list[PrivilegeEntry], list[str]]:
    system = system or platform.system()
    root_path = Path(root)
    if system not in {"Linux", "Darwin"} or pwd is None or grp is None:
        return [], [f"unsupported platform: {system}"]

    passwd_path = root_path / "etc/passwd"
    group_path = root_path / "etc/group"
    entries: list[PrivilegeEntry] = []
    unsupported: list[str] = []

    if root_path == Path("/"):
        users = [(user.pw_name, user.pw_uid) for user in pwd.getpwall()]
        groups = [(group.gr_name, group.gr_mem) for group in grp.getgrall()]
    else:
        users = []
        groups = []
        try:
            for line in passwd_path.read_text(errors="replace").splitlines():
                fields = line.split(":")
                if len(fields) > 2:
                    users.append((fields[0], int(fields[2])))
        except (OSError, ValueError):
            unsupported.append(str(passwd_path))
        try:
            for line in group_path.read_text(errors="replace").splitlines():
                fields = line.split(":")
                if len(fields) > 3:
                    groups.append((fields[0], fields[3].split(",") if fields[3] else []))
        except OSError:
            unsupported.append(str(group_path))

    for username, uid in users:
        if uid == 0:
            entries.append(PrivilegeEntry(username, "uid_0", str(passwd_path)))
    for group_name, members in groups:
        if group_name in {"sudo", "wheel", "admin"}:
            entries.extend(
                PrivilegeEntry(member, f"group:{group_name}", str(group_path))
                for member in members if member
            )
    return entries, unsupported


def load_baseline(path: str | os.PathLike[str]) -> set[str]:
    try:
        values = json.loads(Path(path).read_text())
        values = values.get("entries", values) if isinstance(values, dict) else values
        return {
            item.get("key") or "|".join((str(item.get("identity", "")),
                                         str(item.get("privilege", "")),
                                         str(item.get("source", ""))))
            if isinstance(item, dict) else str(item)
            for item in values
        }
    except (OSError, ValueError, TypeError, KeyError):
        return set()


def save_baseline(path: str | os.PathLike[str], entries: Iterable[PrivilegeEntry]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(
        {"version": 1, "entries": [asdict(entry) for entry in entries]},
        indent=2, sort_keys=True,
    ))


def detect(baseline_path: str | os.PathLike[str] | None = None, *,
           system: str | None = None, root: str | os.PathLike[str] = "/",
           save: bool = False) -> PrivilegeReport:
    entries, unsupported = collect_entries(system, root)
    baseline = load_baseline(baseline_path) if baseline_path else set()
    new = [entry for entry in entries if entry.key not in baseline]
    if baseline_path and save:
        save_baseline(baseline_path, entries)
    return PrivilegeReport(system or platform.system(), entries, new, unsupported,
                           str(baseline_path) if baseline_path else None)


def format_report(report: PrivilegeReport, json_output: bool = False) -> str:
    if json_output:
        return json.dumps(report.to_dict(), indent=2, sort_keys=True)
    lines = [f"Privilege detection ({report.platform}): {len(report.entries)} entries, "
             f"{len(report.new_entries)} new"]
    new_keys = {entry.key for entry in report.new_entries}
    for entry in report.entries:
        marker = "NEW " if entry.key in new_keys else ""
        lines.append(f"- {marker}{entry.identity}: {entry.privilege} ({entry.source})")
    lines.extend(f"Note: {item}" for item in report.unsupported)
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="darkglitch privileges")
    parser.add_argument("--baseline")
    parser.add_argument("--save-baseline", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args(argv)
    print(format_report(detect(args.baseline, save=args.save_baseline), args.json_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
