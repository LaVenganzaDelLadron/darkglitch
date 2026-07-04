# signaling/signal.py
import asyncio
import getpass
import inspect
import json
import logging
from urllib.parse import urlparse

import websockets


logger = logging.getLogger("ghostserver")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class SignalClient:
    """Manage the WebSocket-based signaling channel and dispatch incoming messages."""

    def __init__(self, room, client_id=None, host=None, username=None):
        if client_id is None and host is None and isinstance(room, str):
            parsed = urlparse(room)
            if parsed.scheme in {"ws", "wss"}:
                parts = [part for part in parsed.path.split("/") if part]
                if len(parts) >= 3 and parts[0] == "ws":
                    self.room = parts[1]
                    self.client_id = parts[2]
                    self.host = parsed.netloc
                    self.url = room
                    self.websocket = None
                    self._handlers = []
                    self.message_handlers = []
                    self.message_handler = None
                    self.username = username or getpass.getuser()
                    return

        if client_id is None or host is None:
            raise TypeError("SignalClient requires either a websocket URL or room/client_id/host")

        self.room = room
        self.client_id = str(client_id)
        self.username = username or getpass.getuser()
        self.host = host

        parsed_host = urlparse(host)
        if parsed_host.scheme in {"http", "https", "ws", "wss"}:
            ws_scheme = "wss" if parsed_host.scheme in {"https", "wss"} else "ws"
            base_path = parsed_host.path.rstrip("/")
            self.url = f"{ws_scheme}://{parsed_host.netloc}{base_path}/ws/{room}/{client_id}"
        else:
            self.url = f"ws://{host}/ws/{room}/{client_id}"
        self.websocket = None
        self._handlers = []
        self.message_handlers = []
        self.message_handler = None

    async def connect(self):
        # logger.info("Connecting to signaling bash: %s", self.url)
        try:
            self.websocket = await websockets.connect(self.url)
        except Exception:
            logger.exception("Unable to connect to signaling bash")
            raise

        await self._send_registration()
        # logger.info("Connected to signaling bash at %s", self.url)
        asyncio.create_task(self.listen())
        return self.websocket

    async def listen(self):
        if self.websocket is None:
            logger.warning("Listener started before a websocket connection existed")
            return

        # logger.info("Listening for inbound signaling messages")
        try:
            async for message in self.websocket:
                # logger.info("Incoming raw websocket message: %s", message)
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    logger.exception("Received invalid JSON from signaling bash: %s", message)
                    continue
                await self.handle_message(data)
        except websockets.ConnectionClosed as exc:
            logger.warning("Signaling connection closed: %s", exc)
            await self.connect()  # Attempt to reconnect
            logger.info("Connected to signaling bash...")
        except Exception:
            logger.exception("Unexpected error in signaling listener")

    def add_message_handler(self, handler):
        return self.add_handler(handler)

    def add_handler(self, handler):
        """Register a handler that will receive inbound signaling messages."""
        if handler is None or handler in self._handlers:
            return handler
        self._handlers.append(handler)
        return handler

    async def handle_message(self, message):
        """Dispatch a signaling message to all registered handlers."""
        if not isinstance(message, dict):
            logger.warning("Ignoring non-dict signaling message: %r", message)
            return

        for handler in list(self._handlers):
            try:
                # logger.debug("Dispatching message type %s to handler %s", message.get("type"), getattr(handler, "__name__", handler))
                result = handler(message)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Handler %s failed while processing signaling message", getattr(handler, "__name__", handler))

    async def send(self, packet):
        payload = dict(packet)
        payload.setdefault("sender", str(self.client_id))

        # logger.info("Sending signaling payload: %s", payload)

        try:
            await self.websocket.send(json.dumps(payload))
        except Exception:
            logger.exception("Failed to send signaling payload")
            raise

    async def _send_registration(self):
        if self.websocket is None:
            return

        registration = {
            "type": "register",
            "client_id": str(self.client_id),
            "username": self.username,
        }

        # logger.info("Sending registration payload: %s", registration)
        await self.send(registration)

    async def close(self):
        if self.websocket:
            logger.info("Closing signaling websocket")
            try:
                await self.websocket.close()
            except Exception:
                logger.exception("Error while closing signaling websocket")
            finally:
                self.websocket = None