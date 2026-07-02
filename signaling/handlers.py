# signaling/handlers.py


class OnlineHandler:
    def __init__(self, client_id):
        self.client_id = client_id

    async def __call__(self, message):
        print("[DEBUG] Received message:", message)

        if message.get("type") != "peer-list":
            return

        peers = message.get("data", {}).get("peers", [])
        if not isinstance(peers, list):
            print("[!] Invalid peer list format received from server.")
            return

        if not peers:
            print("[+] No peers are currently online.")
        else:
            print("\n[+] Online peers:")
            for peer in peers:
                print(f"  - {peer}")

        if self.client_id in peers:
            print("[*] Your own client ID is included in the peer list.")
        else:
            print("[*] Your own client ID is not included in the peer list.")
            if peers:
                print("    The signaling server appears to exclude the requesting client from the peer list.")


class DebugHandler:
    async def __call__(self, message):
        print("[DEBUG] Incoming message:", message)