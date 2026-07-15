from command.listener.listen_bash import listen_bash_mode


def main() -> None:
    # Importing listen_bash_mode will pull config (HOST/ROOM) from core/config.py
    # as usual.
    import asyncio

    asyncio.run(listen_bash_mode())


if __name__ == "__main__":
    main()

