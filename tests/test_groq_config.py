from app.core.ai.groq import GroqKeyManager


def test_numbered_groq_keys_without_underscores_are_supported(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    for index in range(2, 6):
        monkeypatch.delenv(f"GROQ_API_KEY_{index}", raising=False)
    monkeypatch.setenv("GROQ_API_KEY1", "key-one")
    monkeypatch.setenv("GROQ_API_KEY2", "key-two")
    monkeypatch.setenv("GROQ_API_KEY3", "key-three")

    manager = GroqKeyManager.from_environment()

    assert [manager.acquire().key for _ in range(3)] == [
        "key-one", "key-two", "key-three"
    ]


def test_canonical_names_take_precedence(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "canonical")
    monkeypatch.setenv("GROQ_API_KEY1", "legacy")
    monkeypatch.setenv("GROQ_API_KEY_2", "canonical-two")
    monkeypatch.setenv("GROQ_API_KEY2", "legacy-two")

    manager = GroqKeyManager.from_environment()

    assert manager.acquire().key == "canonical"
    assert manager.acquire().key == "canonical-two"
