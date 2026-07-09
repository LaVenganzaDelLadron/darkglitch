# command/ai_bash/bash_prompt.py
from core.client import client_id, username
from core.config import HOST, ROOM
from signaling.signal import SignalClient
from command_injection.injector import RemoteCommandHandler as SenderHandler
from ai.ollama_provider import OllamaProvider


def _extract_command_text(response):
    if isinstance(response, str):
        return response.strip()

    if isinstance(response, dict):
        if isinstance(response.get("response"), str):
            return response["response"].strip()
        if isinstance(response.get("content"), str):
            return response["content"].strip()
        if isinstance(response.get("message"), dict):
            content = response["message"].get("content")
            if isinstance(content, str):
                return content.strip()

    return ""


async def bash_prompt(target, prompt, provider=None):
    print("[+] Bash Prompt")

    if provider is None:
        try:
            provider = OllamaProvider()
        except Exception as exc:
            print(f"[-] Unable to initialize AI provider: {exc}")
            return

    try:
        generated_command = _extract_command_text(provider.generate(prompt))
    except Exception as exc:
        print(f"[-] AI generation failed: {exc}")
        return

    if not generated_command:
        print("[-] AI did not return a valid command")
        return

    print(f"[+] Generated command: {generated_command}")

    signal = SignalClient(ROOM, client_id, HOST, username=username)
    await signal.connect()

    sender = SenderHandler(signal)

    try:
        result = await sender.send_command(
            target=target,
            command=generated_command,
            wait_for_result=True,
            timeout=300,
        )

        if result is None:
            print("[-] No response received for remote command")
            return

        if result.get("status") == "success":
            print(result.get("output", "Bash executed successfully"))
        else:
            print("[-] Bash Failed")
            print("ERROR:", result.get("error", "Unknown error"))
    finally:
        await signal.close()

