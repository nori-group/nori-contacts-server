import asyncio
import aiohttp
import json
from typing import Any
from core.config import settings
from fastapi import HTTPException
from enum import StrEnum


class TokenType(StrEnum):
    BOT = "bot"
    OAUTH = "oauth"
    USER = "user"


class BridgeDiscordService:
    def __init__(self):
        self.base_url = settings.BRIDGE_DISCORD_URL
        self.shared_secret = settings.BRIDGE_DISCORD_SHARED_SECRET
        self.headers = {
            "Authorization": f"Bearer {self.shared_secret}",
            "Content-Type": "application/json",
        }
        self.active_ws_sessions: dict[str, dict] = {}

    async def _make_request(
        self,
        method: str | None = None,
        endpoint: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], int]:
        url = f"{self.base_url}/_matrix/provision/v1{endpoint}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method, url=url, headers=self.headers, json=data
                ) as response:
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_text = await response.text()
                        response_data = {"message": response_text}
                    return response_data, response.status
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}, 500
    
    async def login_with_qr(self, user_id: str) -> tuple[dict[str, Any], int]:
        websocket_url = f"{self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')}/_matrix/provision/v1/login/qr?user_id={user_id}"
        try:
            old_session = self.active_ws_sessions.pop(user_id, None)
            if old_session:
                old_task = old_session['task']
                old_task.cancel()
                await asyncio.gather(old_task, return_exceptions=True)
                print(f"[QR] Cancelled previous session for {user_id}")
            
            qr_ready_event = asyncio.Event()

            task = asyncio.create_task(
                self._manage_qr_session(websocket_url, user_id , qr_ready_event)
            )
            self.active_ws_sessions[user_id] = {
                'task': task,
                'qr_code': None
            }

            # for _ in range(50):
            #     await asyncio.sleep(0.1)
            #     if self.active_ws_sessions[user_id]['qr_code']:
            #         qr_data = self.active_ws_sessions[user_id]['qr_code']
            #         return qr_data, 200
            try:
                await asyncio.wait_for(qr_ready_event.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                raise Exception("Failed to get QR code within 5 seconds")
            session = self.active_ws_sessions.get(user_id)
            if session and session['qr_code']:
                return session['qr_code'], 200
            
            raise Exception("Failed to get QR code within 5 seconds")   
        except Exception as e:
            session = self.active_ws_sessions.pop(user_id, None)
            if session:
                task = session['task']
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
            raise HTTPException(status_code=500, detail=f"internal server error: {e}")
    
    async def _manage_qr_session(self, websocket_url: str, user_id: str , qr_ready_event: asyncio.Event):
        print(f"[QR] Started session for {user_id}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    websocket_url, headers=self.headers
                ) as ws:
                    message = await ws.receive()
                    message_data = json.loads(message.data)
                    if user_id in self.active_ws_sessions:
                        self.active_ws_sessions[user_id]['qr_code'] = message_data
                        qr_ready_event.set()
                    timeout = 120
                    start_time = asyncio.get_event_loop().time()
                    while True:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        remaining = timeout - elapsed
                        if remaining <= 0:
                            print(f"[QR] Timeout (2 min) for {user_id}")
                            break
                        try:
                            message = await asyncio.wait_for(
                                ws.receive(),
                                timeout=remaining
                            )
                            if message.type == aiohttp.WSMsgType.TEXT:
                                data = json.loads(message.data)
                                print(f"[QR] Message for {user_id}: {data}")
                                if data.get('success'):
                                    print(f"[QR] Login successful for {user_id}")
                                    break
                            elif message.type == aiohttp.WSMsgType.CLOSED:
                                print(f"[QR] WebSocket closed for {user_id}")
                                break
                        except asyncio.TimeoutError:
                            print(f"[QR] Timeout for {user_id}")
                            break
                    
        except asyncio.CancelledError:
            print(f"[QR] Cancelled for {user_id}")
            raise
        except Exception as e:
            print(f"[QR] Error for {user_id}: {e}")
        finally:
            if user_id in self.active_ws_sessions:
                del self.active_ws_sessions[user_id]
            print(f"[QR] Session ended for {user_id}")


    async def logout(self, user_id: str) -> tuple[dict[str, Any], int]:
        return await self._make_request("POST", f"/logout?user_id={user_id}")

    async def ping(self, user_id: str) -> tuple[dict[str, Any], int]:
        return await self._make_request("GET", f"/ping?user_id={user_id}")

    async def login_with_token(
        self, token: str, user_id: str, token_type: str
    ) -> tuple[dict[str, Any], int]:
        match token_type:
            case TokenType.BOT:
                data = {"token": f"Bot {token}"}
            case TokenType.OAUTH:
                data = {"token": f"Bearer {token}"}
            case TokenType.USER:
                data = {"token": f"{token}"}
            case _:
                return {"error": "Invalid token type"}, 400
        return await self._make_request("POST", f"/login/token?user_id={user_id}", data)


bridge_discord_service = BridgeDiscordService()
