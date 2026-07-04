# signaling/handlers.py


class OnlineHandler:
    def __init__(self, client_id):
        self.client_id = client_id

    async def __call__(self, message):
        print("[DEBUG] Received message:", message)

        if message.get("type") != "peer-list":
            return

        peers_data = message.get("data", {}).get("peers", [])
        if not isinstance(peers_data, list):
            print("[!] Invalid peer list format received from bash.")
            return

        peers = []
        for peer in peers_data:
            if isinstance(peer, str):
                peers.append({"id": peer, "username": None})
            elif isinstance(peer, dict):
                peers.append({
                    "id": peer.get("id"),
                    "username": peer.get("username"),
                })
            else:
                continue

        if not peers:
            print("[+] No peers are currently online.")
        else:
            print("\n[+] Online peers:")
            for peer in peers:
                peer_id = peer.get("id") or "unknown"
                peer_name = peer.get("username") or "unknown"
                print(f"  - {peer_name} ({peer_id})")

        peer_ids = {peer.get("id") for peer in peers if peer.get("id")}
        if self.client_id in peer_ids:
            print("[*] Your own listener ID is included in the peer list.")
        else:
            print("[*] Your own listener ID is not included in the peer list.")
            if peer_ids:
                print("    The signaling bash appears to exclude the requesting listener from the peer list.")


class DebugHandler:
    async def __call__(self, message):
        print("[DEBUG] Incoming message:", message)