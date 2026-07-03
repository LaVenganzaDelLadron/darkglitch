import asyncio
import os
import tempfile
from pathlib import Path

from command.upload_file import build_transfer_payload


def test_build_transfer_payload_for_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "sample.txt"
        source.write_text("hello world", encoding="utf-8")

        payload = build_transfer_payload(source, "/tmp/sample.txt")

        assert payload["type"] == "file-transfer"
        assert payload["mode"] == "upload"
        assert payload["path"] == "/tmp/sample.txt"
        assert payload["size"] == len(b"hello world")
        assert payload["content"] == "hello world"


def test_build_transfer_payload_for_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "folder"
        source_dir.mkdir()
        (source_dir / "a.txt").write_text("a", encoding="utf-8")
        (source_dir / "b.txt").write_text("b", encoding="utf-8")

        payload = build_transfer_payload(source_dir, "/tmp/folder")

        assert payload["type"] == "file-transfer"
        assert payload["mode"] == "upload"
        assert payload["path"] == "/tmp/folder"
        assert payload["is_directory"] is True
        assert payload["content"] == {"a.txt": "a", "b.txt": "b"}
