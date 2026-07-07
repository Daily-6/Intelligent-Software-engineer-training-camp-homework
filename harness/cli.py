import sys
import argparse
from harness.config import load_config
from harness.credentials import CredentialManager


def main():
    parser = argparse.ArgumentParser(description="Coding Agent Harness")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Start WebUI server")

    key_parser = subparsers.add_parser("set-key", help="Set API key")
    key_parser.add_argument("--name", default="deepseek_api_key")

    subparsers.add_parser("status", help="Check key status")

    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn
        config = load_config("config.yaml")
        uvicorn.run("harness.webui.app:app", host="0.0.0.0", port=8000)

    elif args.command == "set-key":
        import getpass
        mgr = CredentialManager(backend="file", store_path=".credentials.json")
        value = getpass.getpass("Enter API key (input hidden): ")
        mgr.store(args.name, value)
        print(f"Key '{args.name}' stored.")

    elif args.command == "status":
        mgr = CredentialManager(backend="file", store_path=".credentials.json")
        exists = mgr.status("deepseek_api_key")
        print(f"deepseek_api_key: {'configured' if exists else 'not set'}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
