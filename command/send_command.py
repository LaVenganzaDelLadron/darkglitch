import asyncio
import json
import logging
import subprocess
import uuid

logger = logging.getLogger("send_command")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class RemoteCommandHandler:
    def __init__(self, signal, command_runner=None):
        self.signal = signal
        self.command_runner = command_runner or self._run_command
        self._pending_results = {}

        if hasattr(signal, "add_handler"):
            signal.add_handler(self.handle_message)
        elif hasattr(signal, "add_message_handler"):
            signal.add_message_handler(self.handle_message)

    async def _run_command(self, command, timeout=None):
        return subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    async def send_command(self, target, command, request_id=None, wait_for_result=False, timeout=None):
        if not isinstance(command, str) or not command.strip():
            logger.error("Refusing to send empty command to %s", target)
            raise ValueError("command must be a non-empty string")

        if request_id is None:
            request_id = str(uuid.uuid4())

        message = {
            "type": "offer",
            "target": target,
            "sdp": json.dumps({
                "type": "remote-command",
                "command": command,
                "request_id": request_id,
            }),
        }

        logger.info("Sending remote command request_id=%s target=%s command=%r", request_id, target, command)

        if wait_for_result:
            future = asyncio.get_running_loop().create_future()
            self._pending_results[request_id] = future
            logger.debug("Waiting for reply for request_id=%s", request_id)

        await self.signal.send(message)

        if wait_for_result:
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                logger.error("Timed out waiting for remote command result request_id=%s", request_id)
                raise

        return request_id

    async def handle_message(self, message):
        if not isinstance(message, dict):
            logger.warning("Received non-dict message: %r", message)
            return

        message_type = message.get("type")
        logger.debug("Handling signaling message type=%s payload=%s", message_type, message)

        if message_type == "answer":
            sdp = message.get("sdp")
            if isinstance(sdp, str):
                try:
                    payload = json.loads(sdp)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON in answer payload: %r", sdp)
                    return
                if payload.get("type") == "remote-command-result":
                    await self._handle_command_result(payload)
                    return
            logger.warning("Ignoring unsupported answer payload: %r", sdp)
            return

        if message_type == "remote-command-result":
            await self._handle_command_result(message)
            return

    async def _handle_command_result(self, message):
        request_id = message.get("request_id")
        if request_id is None:
            logger.warning("Received remote-command-result without request_id: %s", message)
            return

        logger.debug("Received command result request_id=%s payload=%s", request_id, message)
        future = self._pending_results.pop(request_id, None)
        if future is not None and not future.done():
            future.set_result(message)

    async def _send_result(self, target, request_id, status, output=None, error=None):
        packet = {
            "type": "remote-command-result",
            "target": target,
            "request_id": request_id,
            "status": status,
        }

        if output is not None:
            packet["output"] = output
        if error is not None:
            packet["error"] = error

        logger.info("Sending command result request_id=%s target=%s status=%s", request_id, target, status)
        await self.signal.send(packet)