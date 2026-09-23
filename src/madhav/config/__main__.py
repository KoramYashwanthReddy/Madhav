"""Command-line configuration diagnostic entry point for MADHAV platform."""

import json
import sys

from madhav.config.settings import get_settings


def main() -> None:
    """Print redacted configuration diagnostics in formatted JSON."""
    try:
        settings = get_settings()
        redacted_data = settings.redacted()
        print(json.dumps(redacted_data, indent=2))
    except Exception as exc:
        print(f"Error loading MADHAV configuration: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
