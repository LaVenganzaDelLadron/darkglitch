import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeSignalClient:
    def __init__(self, target, prompt):
        self.target = target
        self.prompt = prompt
        self.closed = False

    async def connect(self):
        return None

    async def close(self):
        self.closed = True

    async def send(self, payload):
        return None


class FakeSenderHandler:
    def __init__(self, signal):
        self.signal = signal
        self.sent_commands = []

    async def send_command(self, target, command, wait_for_result=False, timeout=None):
        self.sent_commands.append((target, command, wait_for_result, timeout))
        return {"status": "success", "output": "ok"}


def test_bash_prompt_uses_generated_command(monkeypatch):
    import command.ai_bash.bash_prompt as bash_prompt_module

    class FakeProvider:
        def generate(self, prompt, model=None):
            return "ls -la"

    recorded = {}

    def fake_signal_client(*args, **kwargs):
        recorded["signal_args"] = args
        recorded["signal_kwargs"] = kwargs
        return FakeSignalClient(args[0], args[1])

    def fake_sender_handler(signal):
        recorded["sender_signal"] = signal
        return FakeSenderHandler(signal)

    monkeypatch.setattr(bash_prompt_module, "SignalClient", fake_signal_client)
    monkeypatch.setattr(bash_prompt_module, "SenderHandler", fake_sender_handler)

    class ProviderWrapper(FakeProvider):
        pass

    asyncio.run(bash_prompt_module.bash_prompt("target-1", "show me files", provider=ProviderWrapper()))

    assert recorded["signal_args"][0] == "D4RKGLI7CH"
    assert recorded["signal_kwargs"]["username"] == "darkglitch"
    assert recorded["sender_signal"].prompt == recorded["signal_args"][1]
    assert recorded["sender_signal"].target == "D4RKGLI7CH"


def test_bash_prompt_falls_back_when_provider_times_out(monkeypatch):
    import command.ai_bash.bash_prompt as bash_prompt_module

    class TimeoutProvider:
        def generate(self, prompt, model=None):
            raise TimeoutError("timed out")

    recorded = {}

    def fake_signal_client(*args, **kwargs):
        recorded["signal_args"] = args
        recorded["signal_kwargs"] = kwargs
        return FakeSignalClient(args[0], args[1])

    def fake_sender_handler(signal):
        recorded["sender_signal"] = signal
        return FakeSenderHandler(signal)

    monkeypatch.setattr(bash_prompt_module, "SignalClient", fake_signal_client)
    monkeypatch.setattr(bash_prompt_module, "SenderHandler", fake_sender_handler)

    asyncio.run(bash_prompt_module.bash_prompt("target-1", "list all folders in root", provider=TimeoutProvider()))

    assert recorded["signal_args"][0] == "D4RKGLI7CH"
    assert recorded["sender_signal"].target == "D4RKGLI7CH"
    assert recorded["sender_signal"].prompt == recorded["signal_args"][1]


def test_extract_command_text_handles_response_objects():
    import command.ai_bash.bash_prompt as bash_prompt_module

    class ResponseObject:
        def __init__(self, text):
            self.response = text

    assert bash_prompt_module._extract_command_text(ResponseObject("```bash\nls -la /\n```")) == "ls -la /"


def test_extract_command_text_finds_command_inside_explanatory_text():
    import command.ai_bash.bash_prompt as bash_prompt_module

    text = "You can use the following command: `ls -A /` to list folders."
    assert bash_prompt_module._extract_command_text(text) == "ls -A /"
