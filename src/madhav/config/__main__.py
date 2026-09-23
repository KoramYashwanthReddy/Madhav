"""CLI diagnostic runner for MADHAV configuration inspection."""

import json
import sys

from madhav.config.loader import get_settings


def main() -> None:
    """Output safe, redacted configuration diagnostics as formatted JSON."""
    try:
        settings = get_settings()
        diagnostics = settings.redacted()
        print(json.dumps(diagnostics, indent=2))
        sys.exit(0)
    except Exception as exc:
        print(f"Error loading MADHAV configuration: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
