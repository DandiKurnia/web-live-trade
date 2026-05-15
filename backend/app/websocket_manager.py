from typing import List, Dict, Set
from fastapi import WebSocket
import asyncio
import json


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        self.subscriptions.pop(websocket, None)

    def subscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(s.lower() for s in symbols)

    def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket] -= set(s.lower() for s in symbols)

    async def broadcast(self, symbol: str, data: dict):
        message = json.dumps(data)
        symbol_lower = symbol.lower()
        disconnected = []
        for ws in self.active_connections:
            if symbol_lower in self.subscriptions.get(ws, set()):
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.append(ws)
        for ws in disconnected:
            self.disconnect(ws)


ws_manager = WebSocketManager()
