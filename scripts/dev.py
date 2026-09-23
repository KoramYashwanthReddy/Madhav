"""Developer server runner script for MAX platform foundation."""

import subprocess
import sys


def main() -> None:
    """Launch local development Uvicorn server with hot reload."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "max.main:app",
        "--reload",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]
    print(f"Starting MAX dev server: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nDev server stopped by user.")
    except subprocess.CalledProcessError as err:
        sys.exit(err.returncode)


if __name__ == "__main__":
    main()
