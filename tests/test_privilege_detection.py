import json

from app.tools.privilege_detection import detect, format_report, save_baseline


def test_detects_uid_zero_and_admin_group(tmp_path):
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/sh\nalice:x:1000:1000::/home/alice:/bin/sh\n")
    (tmp_path / "etc/group").write_text("sudo:x:27:alice\nusers:x:100:alice\n")
    report = detect(system="Linux", root=tmp_path)
    assert {(entry.identity, entry.privilege) for entry in report.entries} == {
        ("root", "uid_0"), ("alice", "group:sudo")
    }


def test_baseline_marks_new_privileged_identity(tmp_path):
    entry_path = tmp_path / "baseline.json"
    save_baseline(entry_path, [])
    (tmp_path / "etc").mkdir()
    (tmp_path / "etc/passwd").write_text("root:x:0:0:root:/root:/bin/sh\n")
    (tmp_path / "etc/group").write_text("")
    report = detect(entry_path, system="Linux", root=tmp_path)
    assert len(report.new_entries) == 1
    assert json.loads(format_report(report, json_output=True))["new_entries"][0]["identity"] == "root"
