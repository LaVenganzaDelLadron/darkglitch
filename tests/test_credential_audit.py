import json

from app.tools.credential_audit import format_report, scan


def test_scan_finds_and_redacts_credentials(tmp_path):
    source = tmp_path / "config.env"
    source.write_text('API_KEY="super-secret-value"\nnormal=true\n')
    findings, skipped = scan([tmp_path])
    assert not skipped
    assert len(findings) == 1
    assert findings[0].kind == "credential_assignment"
    assert "super-secret-value" not in format_report(findings, skipped)
    assert "sup...lue" in format_report(findings, skipped)


def test_scan_skips_binary_and_ignored_directories(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text('TOKEN="hidden-secret-value"\n')
    (tmp_path / "binary").write_bytes(b"\xff\xfe")
    findings, skipped = scan([tmp_path])
    assert findings == []
    assert str(tmp_path / "binary") in skipped
    assert json.loads(format_report(findings, skipped, True))["findings"] == []
