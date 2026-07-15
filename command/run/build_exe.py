import subprocess
import sys
from pathlib import Path



def _project_root() -> Path:
    # command/run/build_exe.py -> command/run -> command -> repo root
    return Path(__file__).resolve().parents[2]


def build_listener_exe(output_name: str = "darkglitch_listener.exe") -> Path:
    """Build a Windows GUI-less EXE that starts the bash listener.

    This function is intended to be run on the machine where you want to
    generate the .exe (Windows target expected).
    """

    repo_root = _project_root()

    entry_script = repo_root / "command" / "run" / "listener_exe_entry.py"
    if not entry_script.exists():
        raise FileNotFoundError(f"Missing PyInstaller entry script: {entry_script}")

    dist_dir = repo_root / "dist"
    build_dir = repo_root / "build"

    # Ensure output dirs exist/are clean-ish
    dist_dir.mkdir(parents=True, exist_ok=True)

    # Try to keep build deterministic-ish: clean build/ if present
    # (avoid deleting user dist content).
    if build_dir.exists():
        # PyInstaller uses build/ for intermediates.
        # Best-effort cleanup.
        pass

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name",
        output_name.replace(".exe", ""),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(build_dir),
        str(entry_script),
    ]

    # Run from repo root so relative imports work.
    subprocess.check_call(cmd, cwd=str(repo_root))

    produced = dist_dir / output_name
    if produced.exists():
        return produced

    # PyInstaller sometimes produces without extension on misconfigured systems.
    # Provide a helpful fallback.
    alt = dist_dir / output_name.replace(".exe", "")
    if alt.exists():
        return alt

    raise FileNotFoundError(
        f"PyInstaller finished but output was not found. Expected: {produced}"
    )

