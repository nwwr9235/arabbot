"""
music_bot/api_server.py
API مع تسجيل مفصل للأخطاء
"""

import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from music_bot.player import MusicPlayer

logger = logging.getLogger(__name__)
app = FastAPI(title="Music Bot API")

class PlayRequest(BaseModel):
    chat_id: int
    query: str
    user_id: int
    invited_by: int | None = None

class ChatActionRequest(BaseModel):
    chat_id: int
    user_id: int

player_instance: MusicPlayer | None = None

def build_app(player: MusicPlayer) -> FastAPI:
    global player_instance
    player_instance = player
    return app

# ✅ Middleware للتسجيل
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"➡️ {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"⬅️ {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ Error in {request.url.path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.post("/play")
async def play(request: PlayRequest):
    """تشغيل أغنية"""
    logger.info(f"🎵 Play request: chat={request.chat_id}, query={request.query}")
    
    if not player_instance:
        raise HTTPException(500, "Player not initialized")
    
    try:
        result = await player_instance.play(
            chat_id=request.chat_id,
            query=request.query,
            user_id=request.user_id,
            invited_by=request.invited_by,
        )
        
        if not result["ok"]:
            logger.error(f"Play failed: {result.get('error')}")
            raise HTTPException(400, result.get("error", "Unknown error"))
        
        logger.info(f"✅ Play success: {result.get('title')}")
        return result
        
    except Exception as e:
        logger.error(f"Exception in play: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(500, str(e))

@app.post("/stop")
async def stop(request: ChatActionRequest):
    """إيقاف التشغيل"""
    if not player_instance:
        raise HTTPException(500, "Player not initialized")
    return await player_instance.stop(request.chat_id)

@app.post("/skip")
async def skip(request: ChatActionRequest):
    """تخطي الأغنية"""
    if not player_instance:
        raise HTTPException(500, "Player not initialized")
    return await player_instance.skip(request.chat_id)

@app.post("/pause")
async def pause(request: ChatActionRequest):
    """إيقاف مؤقت"""
    if not player_instance:
        raise HTTPException(500, "Player not initialized")
    return await player_instance.pause(request.chat_id)

@app.post("/resume")
async def resume(request: ChatActionRequest):
    """استئناف التشغيل"""
    if not player_instance:
        raise HTTPException(500, "Player not initialized")
    return await player_instance.resume(request.chat_id)

@app.get("/queue/{chat_id}")
async def get_queue(chat_id: int):
    """الحصول على قائمة التشغيل"""
    if not player_instance:
        raise HTTPException(500, "Player not initialized")
    return player_instance.get_queue(chat_id)

@app.get("/health")
async def health():
    """فحص صحة النظام"""
    return {
        "status": "ok",
        "player": "initialized" if player_instance else "not ready",
        "tgcalls": "running" if player_instance and player_instance.calls else "not ready",
    }
