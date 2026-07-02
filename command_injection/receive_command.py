import json
import logging
import subprocess

logger = logging.getLogger("receive_command")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class RemoteCommandHandler:
    """Handle remote-command_injection requests over the existing signaling channel."""

    def __init__(self, signal=None):
        self.signal = None
        if signal is not None:
            self.attach(signal)

    def attach(self, signal):
        """Register this handler with a signaling client."""
        self.signal = signal
        signal.add_handler(self.dispatch_message)
        return self

    async def dispatch_message(self, message):
        """Route incoming signaling messages to the command_injection handler."""
        if not isinstance(message, dict):
            logger.warning("Received invalid signaling payload: %r", message)
            await self._send_error(None, None, "Invalid signaling message.")
            return

        if message.get("type") == "remote-command_injection":
            logger.debug("Dispatching remote command_injection request: %s", message)
            await self.handle_message(message)
        elif message.get("type") == "offer":
            logger.debug("Dispatching offer request: %s", message)
            await self._handle_offer(message)
        else:
            logger.debug("Ignoring signaling message of type %s", message.get("type"))

    async def handle_message(self, message):
        """Process a remote-command_injection request and respond over signaling."""
        if not isinstance(message, dict):
            logger.warning("Rejected non-dict message: %r", message)
            await self._send_error(None, None, "Invalid signaling message.")
            return

        if message.get("type") == "remote-command_injection":
            logger.debug("Dispatching direct remote-command_injection request: %s", message)
            await self._process_command_request(message)
            return

        if message.get("type") == "offer":
            logger.debug("Dispatching remote command_injection offer: %s", message)
            await self._handle_offer(message)
            return

        logger.debug("Ignoring unsupported signaling message type: %s", message.get("type"))

    async def _handle_offer(self, message):
        sdp = message.get("sdp")
        if not isinstance(sdp, str):
            logger.warning("Invalid offer SDP from %s: %r", message.get("sender"), sdp)
            return

        try:
            payload = json.loads(sdp)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in offer SDP: %r", sdp)
            return

        if payload.get("type") != "remote-command_injection":
            logger.warning("Ignoring unsupported offer payload type: %s", payload.get("type"))
            return

        request = {
            "sender": message.get("sender"),
            "command_injection": payload.get("command_injection"),
            "request_id": payload.get("request_id"),
        }
        await self._process_command_request(request)

    async def _process_command_request(self, message):
        sender = message.get("sender")
        command = message.get("command_injection")
        request_id = message.get("request_id")

        if not isinstance(command, str) or not command.strip():
            logger.warning("Rejecting invalid remote command_injection from %s: %r", sender, message)
            await self._send_error(sender, request_id, "Invalid remote command_injection request.")
            return

        logger.info("Executing command_injection from %s: %s", sender, command)
        status, output, error = await self._execute_command(sender, command)

        if status == "success":
            await self._send_answer(sender, request_id, status, output=output)
        else:
            await self._send_answer(sender, request_id, status, error=error)

    async def _execute_command(self, sender, command):
        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            logger.error("Command timed out for %s: %s", sender, command)
            return "error", None, "Command timed out."
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.exception("Command execution failed for %s: %s", sender, command)
            return "error", None, f"Command failed: {exc}"

        output = completed.stdout + completed.stderr
        if not output:
            output = "Command executed successfully."

        logger.info("Command finished for %s with exit code %s", sender, completed.returncode)
        if completed.returncode == 0:
            return "success", output, None
        return "error", None, output or "Command failed."

    async def _send_answer(self, target, request_id, status, output=None, error=None):
        if self.signal is None:
            logger.warning("Cannot send command_injection result because no signaling client is attached")
            return

        response_payload = {
            "type": "remote-command_injection-result",
            "request_id": request_id,
            "status": status,
        }
        if output is not None:
            response_payload["output"] = output
        if error is not None:
            response_payload["error"] = error

        response = {
            "type": "answer",
            "target": target,
            "sdp": json.dumps(response_payload),
        }

        logger.debug("Sending answer with remote-command_injection-result to %s: %s", target, response_payload)
        await self.signal.send(response)

    async def _send_error(self, target, request_id, error):
        await self._send_answer(target, request_id, "error", error=error)