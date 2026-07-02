async def online_handler(message):
    print("[DEBUG]", message)

    if message.get("type") == "online_list":
        print("\n[+] Online Users")

        for user in message.get("clients", []):
            print(f"  - {user}")