
import os
import uuid
import asyncio
from collections import deque

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="NITO LIVE Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

connections = {}
waiting = deque()
paired = {}
lock = asyncio.Lock()
reports = []


class Report(BaseModel):
    reporter_id: str
    reported_id: str
    reason: str


@app.get("/")
async def home():
    return {
        "app": "NITO LIVE",
        "status": "online",
        "message": "Backend iniciado"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/match")
async def create_match():
    user_id = str(uuid.uuid4())
    return {
        "user_id": user_id,
        "websocket_url": f"/ws/{user_id}"
    }


async def send_to(user_id, payload):
    socket = connections.get(user_id)
    if socket:
        try:
            await socket.send_json(payload)
        except Exception:
            pass


async def remove_user(user_id):
    async with lock:
        if user_id in waiting:
            waiting.remove(user_id)

        partner = paired.pop(user_id, None)
        if partner:
            paired.pop(partner, None)

        connections.pop(user_id, None)

    if partner:
        await send_to(partner, {"type": "peer_left"})


async def find_partner(user_id, country):
    async with lock:
        if user_id not in connections:
            return

        partner = None

        for candidate in list(waiting):
            if candidate == user_id:
                continue

            candidate_socket = connections.get(candidate)

            if not candidate_socket:
                if candidate in waiting:
                    waiting.remove(candidate)
                continue

            candidate_country = getattr(
                candidate_socket, "nito_country", "any"
            )

            if (
                country == "any"
                or candidate_country == "any"
                or country == candidate_country
            ):
                partner = candidate
                waiting.remove(candidate)
                break

        if partner is None:
            if user_id not in waiting:
                waiting.append(user_id)
            return

        paired[user_id] = partner
        paired[partner] = user_id

    await send_to(partner, {
        "type": "match_found",
        "peer_id": user_id,
        "role": "caller"
    })

    await send_to(user_id, {
        "type": "match_found",
        "peer_id": partner,
        "role": "callee"
    })


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    websocket.nito_country = "any"
    connections[user_id] = websocket

    try:
        while True:
            message = await websocket.receive_json()
            kind = message.get("type")

            if kind == "join_queue":
                country = message.get("country", "any")
                websocket.nito_country = (
                    country if isinstance(country, str) else "any"
                )
                await find_partner(user_id, websocket.nito_country)

            elif kind in ("offer", "answer", "ice_candidate"):
                partner = paired.get(user_id)
                if partner:
                    await send_to(partner, {
                        **message,
                        "peer_id": user_id
                    })

            elif kind == "leave_call":
                await remove_user(user_id)
                await websocket.send_json({
                    "type": "ready_for_next"
                })

            elif kind == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await remove_user(user_id)

    except Exception:
        await remove_user(user_id)


@app.post("/api/report")
async def submit_report(report: Report):
    if report.reporter_id == report.reported_id:
        return {
            "ok": False,
            "message": "Denúncia inválida"
        }

    reports.append({
        "reporter_id": report.reporter_id,
        "reported_id": report.reported_id,
        "reason": report.reason
    })

    return {
        "ok": True,
        "message": "Denúncia recebida para análise"
    }
