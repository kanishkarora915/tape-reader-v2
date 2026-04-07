"""
BuyBy Trading System — WebSocket Broadcast Manager
Manages connected WebSocket clients and broadcasts data by channel.
"""

import json
import logging

from fastapi import WebSocket

logger = logging.getLogger("buyby.ws")


class WSManager:
    """Manages WebSocket client connections and broadcasts."""

    def __init__(self):
        self.clients: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        """Accept and register a new WebSocket client."""
        await ws.accept()
        self.clients.add(ws)
        logger.info(f"[WS] Client connected. Total: {self.client_count}")

    def disconnect(self, ws: WebSocket) -> None:
        """Remove a WebSocket client."""
        self.clients.discard(ws)
        logger.info(f"[WS] Client disconnected. Total: {self.client_count}")

    async def broadcast(self, channel: str, data: dict, **kwargs) -> None:
        """
        Broadcast a message to all connected clients.
        Message format: {"channel": channel, "data": data, ...kwargs}
        """
        if not self.clients:
            return

        try:
            message = json.dumps({"channel": channel, "data": data, **kwargs}, default=str)
        except (TypeError, ValueError) as e:
            logger.error(f"[WS] JSON serialize error on channel {channel}: {e}")
            return
        dead_clients = set()

        for client in self.clients.copy():
            try:
                await client.send_text(message)
            except Exception:
                dead_clients.add(client)

        # Remove dead connections
        for client in dead_clients:
            self.clients.discard(client)

    @property
    def client_count(self) -> int:
        """Number of connected clients."""
        return len(self.clients)
