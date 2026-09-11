from app.core.ai.pipeline import AICommandPipeline


class StubProvider:
    def __init__(self):
        self.prompt = ""

    def generate(self, prompt):
        self.prompt = prompt
        return "echo grounded"


def test_command_pipeline_uses_indexed_evidence():
    provider = StubProvider()
    pipeline = AICommandPipeline(provider=provider)

    pipeline.ingest_evidence(
        {"finding": "Missing CSP", "url": "https://example.test"},
        source="nuclei",
        metadata={"target_host": "example.test", "severity": "medium"},
    )

    assert pipeline.generate_command("Explain the CSP finding", {"target_host": "example.test"}) == "echo grounded"
    assert "Missing CSP" in provider.prompt
    assert "Retrieved Security Evidence" in provider.prompt


def test_rag_can_be_disabled_without_changing_command_interface():
    provider = StubProvider()
    pipeline = AICommandPipeline(provider=provider, rag_enabled=False)
    pipeline.ingest_evidence("secret evidence", source="test")

    pipeline.generate_command("generate a command")

    assert "Retrieved Security Evidence" not in provider.prompt
