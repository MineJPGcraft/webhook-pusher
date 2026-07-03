"""
Webhook Pusher — 服务入口   这里不放什么东西
"""

import logging
import sys

import uvicorn
from fastapi import FastAPI

from core.config import load_config
from core.server import app


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def main():
    setup_logging()
    config = load_config()
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8000)

    logging.info("启动 Webhook Pusher → %s:%d", host, port)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
