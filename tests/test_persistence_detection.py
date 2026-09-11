import json

from app.tools.persistence_detection import (
    DetectionReport,
    PersistenceEntry,
    detect,
    format_report,
    load_baseline,
    save_baseline,
    watch,
)


def test_linux_collectors_and_baseline(tmp_path):
    (tmp_path / "etc/systemd/system").mkdir(parents=True)
    (tmp_path / "etc/cron.d").mkdir(parents=True)
    service = tmp_path / "etc/systemd/system/example.service"
    service.write_text("[Service]\nExecStart=/usr/bin/example\n")
    (tmp_path / "etc/cron.d/job").write_text("/usr/bin/job\n")

    baseline = tmp_path / "baseline.json"
    report = detect(baseline, system="Linux", root=tmp_path, save=True)
    assert {entry.mechanism for entry in report.entries} == {"system_service", "scheduled_task"}
    assert len(report.new_entries) == 2
    assert load_baseline(baseline)

    second = detect(baseline, system="Linux", root=tmp_path)
    assert second.new_entries == []


def test_json_report_contains_required_fields():
    entry = PersistenceEntry("demo", "autorun_entry", "/usr/bin/demo")
    report_text = format_report(DetectionReport("Linux", [entry], [entry]), json_output=True)
    assert json.loads(report_text)["entries"][0]["name"] == "demo"


def test_human_report_includes_entry_details():
    entry = PersistenceEntry(
        "demo", "system_service", "/usr/bin/demo",
        process_name="demo",
        creation_time="2026-01-01T00:00:00+00:00",
        digital_signature_status="valid",
    )
    report = format_report(DetectionReport("Linux", [entry], [entry]))
    assert "Process: demo" in report
    assert "Created: 2026-01-01T00:00:00+00:00" in report
    assert "Signature: valid" in report


def test_save_baseline_is_read_only_for_entries(tmp_path):
    entry = PersistenceEntry("x", "startup_application")
    path = tmp_path / "nested" / "baseline.json"
    save_baseline(path, [entry])
    assert json.loads(path.read_text())["entries"][0]["mechanism"] == "startup_application"


def test_watch_rejects_non_positive_interval():
    try:
        watch(0)
    except ValueError as error:
        assert str(error) == "watch interval must be greater than zero"
    else:
        raise AssertionError("watch should reject a non-positive interval")
