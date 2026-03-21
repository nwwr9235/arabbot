"""
music_bot/player.py
محرك التشغيل الصوتي مع دعم البوت المساعد
"""

import asyncio
import logging
import os
import yt_dlp
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import AudioPiped, AudioParameters
from pytgcalls.types.stream import StreamEnded

logger = logging.getLogger(__name__)

YDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "outtmpl": "/tmp/music/%(id)s.%(ext)s",
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }],
}

os.makedirs("/tmp/music", exist_ok=True)


class MusicPlayer:

    def __init__(self, tgcalls: PyTgCalls, assistant_client: Client = None):
        self.calls = tgcalls
        self.assistant = assistant_client  # البوت المساعد
        self._register_callbacks()

    async def play(self, chat_id: int, query: str, user_id: int, invited_by: int = None) -> dict:
        """
        تشغيل الأغنية في المجموعة
        
        Parameters:
            chat_id: معرف المجموعة
            query: رابط أو اسم الأغنية
            user_id: معرف المستخدم الذي طلب التشغيل
            invited_by: معرف المستخدم الذي دعا البوت (إذا لم يكن مشرفاً)
        """
        
        # ✅ 1. التأكد من أن البوت المساعد في المجموعة
        try:
            member = await self.assistant.get_chat_member(chat_id, "me")
            if not member:
                return {
                    "ok": False, 
                    "error": "البوت المساعد ليس في المجموعة. أضفه أولاً!"
                }
        except Exception as e:
            logger.warning(f"البوت ليس في المجموعة {chat_id}: {e}")
            return {
                "ok": False,
                "error": "البوت المساعد ليس في المجموعة. أضفه كمشرف!"
            }

        # ✅ 2. تنزيل الأغنية
        try:
            title, file_path = await self._fetch(query)
        except Exception as e:
            logger.error(f"yt-dlp error: {e}")
            return {"ok": False, "error": f"فشل التنزيل: {e}"}

        if not os.path.exists(file_path):
            return {"ok": False, "error": "الملف غير موجود بعد التنزيل"}

        # ✅ 3. إضافة للقائمة
        track = Track(title=title, url=file_path, query=query, user_id=user_id)
        gq = queue_manager.get(chat_id)
        pos = gq.add(track)

        # ✅ 4. بدء التشغيل إذا لم يكن هناك شيء يعمل
        if not gq.is_playing:
            result = await self._start_playback(chat_id, invited_by)
            if not result["ok"]:
                return result

        return {"ok": True, "title": title, "position": pos}

    async def _start_playback(self, chat_id: int, invited_by: int = None) -> dict:
        """
        بدء التشغيل الفعلي في المكالمة
        """
        gq = queue_manager.get(chat_id)
        track = gq.current()
        
        if not track:
            gq.is_playing = False
            return {"ok": False, "error": "لا يوجد أغنية في القائمة"}

        gq.is_playing = True
        gq.is_paused = False

        try:
            # ✅ التحقق من وجود مكالمة صوتية نشطة
            # إذا لم تكن هناك مكالمة، نحتاج لإنشائها أو الانضمام إليها
            
            # محاولة الانضمام للمكالمة
            try:
                await self.calls.join_group_call(
                    chat_id,
                    AudioPiped(
                        track.url,
                        AudioParameters(bitrate=48000, channels=2),
                    ),
                    join_as=self.assistant.me.id if self.assistant else None,
                    invite_hash=None,
                )
            except Exception as join_error:
                # ربما المكالمة غير موجودة، نحاول إنشاءها
                logger.warning(f"لا يمكن الانضمام للمكالمة: {join_error}")
                
                # ✅ استدعاء البوت للمكالمة عبر دعوة
                if invited_by:
                    try:
                        await self.assistant.invoke(
                            raw.functions.phone.JoinGroupCall(
                                call=await self._get_group_call(chat_id),
                                join_as=types.InputPeerSelf(),
                                invite_hash=invited_by if invited_by else None,
                            )
                        )
                    except Exception as e:
                        logger.error(f"فشل في دعوة البوت: {e}")
                
                # محاولة أخرى للتشغيل
                await self.calls.play(
                    chat_id,
                    AudioPiped(
                        track.url,
                        AudioParameters(bitrate=48000, channels=2),
                    ),
                )

            logger.info(f"▶️ تشغيل في {chat_id}: {track.title}")
            return {"ok": True}

        except Exception as e:
            logger.error(f"❌ خطأ في التشغيل: {e}")
            logger.exception(e)
            gq.is_playing = False
            return {"ok": False, "error": str(e)}

    async def _get_group_call(self, chat_id: int):
        """الحصول على معلومات المكالمة الجماعية"""
        try:
            chat = await self.assistant.get_chat(chat_id)
            return chat.call
        except:
            return None

    # ... بقية الدوال (stop, skip, pause, resume, get_queue) كما هي ...

    def _register_callbacks(self):
        @self.calls.on_update()
        async def on_stream_ended(_, update):
            if isinstance(update, StreamEnded):
                chat_id = update.chat_id
                logger.info(f"🔴 انتهى البث في {chat_id}")

                gq = queue_manager.get(chat_id)
                next_track = gq.skip()

                if next_track:
                    await self._start_playback(chat_id)
                else:
                    gq.is_playing = False
                    try:
                        await self.calls.leave_call(chat_id)
                    except Exception:
                        pass
                    logger.info(f"✅ انتهت القائمة في {chat_id}")

    @staticmethod
    async def _fetch(query: str) -> tuple[str, str]:
        search = query if query.startswith("http") else f"ytsearch1:{query}"
        loop = asyncio.get_event_loop()

        def _download():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(search, download=True)
                if "entries" in info:
                    info = info["entries"][0]
                title = info.get("title", query)
                file_path = ydl.prepare_filename(info)
                
                if file_path.endswith(('.webm', '.m4a', '.mp4', '.weba')):
                    file_path = file_path.rsplit('.', 1)[0] + '.mp3'
                
                return title, file_path

        return await loop.run_in_executor(None, _download)


# ✅ كلاس Track (إذا لم يكن معرفاً)
class Track:
    def __init__(self, title: str, url: str, query: str, user_id: int):
        self.title = title
        self.url = url
        self.query = query
        self.user_id = user_id


# ✅ مدير القوائم (مبسط)
class QueueManager:
    def __init__(self):
        self._queues = {}
    
    def get(self, chat_id: int):
        if chat_id not in self._queues:
            self._queues[chat_id] = GroupQueue()
        return self._queues[chat_id]

queue_manager = QueueManager()


class GroupQueue:
    def __init__(self):
        self.tracks = []
        self.is_playing = False
        self.is_paused = False
        self.current_index = -1
    
    def add(self, track: Track) -> int:
        self.tracks.append(track)
        return len(self.tracks)
    
    def current(self) -> Track | None:
        if 0 <= self.current_index < len(self.tracks):
            return self.tracks[self.current_index]
        return None
    
    def skip(self) -> Track | None:
        self.current_index += 1
        return self.current()
    
    def clear(self):
        self.tracks = []
        self.current_index = -1
        self.is_playing = False
    
    def to_list(self):
        return [{"title": t.title, "user_id": t.user_id} for t in self.tracks]
