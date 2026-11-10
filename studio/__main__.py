"""Start the studio: ``python -m studio``. Local only, by design."""

from __future__ import annotations

import uvicorn

from studio.server.app import create_app
from studio.settings import HOST, PORT


def main() -> None:
    print(f"ShapeSense Studio: http://localhost:{PORT}")
    uvicorn.run(create_app(), host=HOST, port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
