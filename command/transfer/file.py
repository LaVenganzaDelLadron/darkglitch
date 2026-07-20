import base64
import json
from pathlib import Path
from transfer_utils.transfer import build_transfer_payload, _run_transfer


async def upload_file(target, local_path, remote_path=None):
    local_path = Path(local_path)
    if remote_path is None:
        remote_path = local_path.name

    payload = build_transfer_payload(local_path, remote_path, mode="upload")
    result = await _run_transfer(target, payload)

    if result is None:
        print("[-] NO RESPONSE RECEIVED FOR FILE UPLOAD")
        return
    if result.get("status") == "success":
        print("[+] FILE UPLOAD SUCCESSFULLY")
    else:
        print("[-] FILE UPLOAD FAILED")
        print("ERROR: ", result.get("error", "Unknown Error"))


async def download_file(target, remote_path, local_path=None):
    remote_path_obj = Path(remote_path)
    if local_path is None:
        local_path = Path(remote_path_obj.name)
    else:
        local_path = Path(local_path)
        if local_path.exists() and local_path.is_dir():
            local_path = local_path / remote_path_obj.name

    payload = {"type": "file-transfer", "mode": "download", "path": str(remote_path)}
    result = await _run_transfer(target, payload)

    if result is None:
        print("[-] NO RESPONSE RECEIVED FOR FILE DOWNLOAD")
        return

    if result.get("status") != "success":
        print("[-] DOWNLOAD FAILED")
        print("ERROR:", result.get("error", "Unknown error"))
        return

    try:
        response = json.loads(result.get("output", "{}"))
    except json.JSONDecodeError:
        print("[-] INVALID DOWNLOAD PAYLOAD SERVICE")
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

    print(f"[+] DOWNLOAD COMPLETED TO {destination}")
