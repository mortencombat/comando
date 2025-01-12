import argparse

import uvicorn

from dotenv import load_dotenv


def main() -> None:
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Comando application")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv("dev.env" if args.reload else None)

    # Setup logging
    # setup_logging(args.debug)

    # Run app
    uvicorn.run(
        "comando.api.server:create_app",
        host="0.0.0.0",
        port=8000,
        reload=args.reload,
        factory=True,
        reload_includes=["*.py"],
    )
