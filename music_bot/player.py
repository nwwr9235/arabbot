"""
music_bot/player.py
محرك التشغيل الصوتي — يستخدم yt-dlp كأساسي مع دعم pytube احتياطي
"""

import asyncio
import logging
import os
import traceback
import random
import time
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream, AudioQuality, StreamEnded

# ✅ استيراد yt-dlp كأساسي
try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False
    logging.warning("yt-dlp not available")

# ✅ pytube كاحتياطي فقط
try:
    from pytube import YouTube
    from youtubesearchpython import VideosSearch
    PYTUBE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"pytube not available: {e}")
    PYTUBE_AVAILABLE = False

logger = logging.getLogger(__name__)


class MusicPlayer:

    def __init__(self, tgcalls: PyTgCalls, assistant_client=None):
        self.calls = tgcalls
        self.assistant = assistant_client
        self._register_callbacks()
        
        # ✅ إعدادات yt-dlp المحسنة لتجنب الحظر
        self.ydl_opts_base = {
            "format": "bestaudio/best[acodec!=none]/best",
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "socket_timeout": 30,
            "source_address": "0.0.0.0",
            
            # ✅ محاكاة متصفح حقيقي
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "referer": "https://www.youtube.com/",
            "headers": {
                "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            
            # ✅ تغيير العميل لتجنب كشف البوت
            "extractor_args": {
                "youtube": {
                    "player_client": "android_vr,web_safari",
                    "player_skip": "configs,webpage",
                    "webpage_client": "web_safari",
                }
            },
            
            # ✅ تأخيرات عشوائية لتجنب الكشف
            "sleep_requests": 0.5,
            "sleep_interval": 1,
            "max_sleep_interval": 3,
        }
        
        # ✅ إضافة الكوكيز إذا وجدت
        self.cookie_file = "cookies.txt"
        if os.path.exists(self.cookie_file):
            self.ydl_opts_base["cookiefile"] = self.cookie_file
            logger.info("✅ Cookies file found and will be used")
        else:
            logger.warning("⚠️ No cookies.txt found - YouTube may block requests")
        
        logger.info(f"✅ MusicPlayer initialized (yt-dlp: {YTDLP_AVAILABLE}, pytube: {PYTUBE_AVAILABLE})")

    async def play(self, chat_id: int, query: str, user_id: int, invited_by: int = None) -> dict:
        logger.info(f"{'='*50}")
        logger.info(f"🎵 PLAY REQUEST: chat_id={chat_id}, query='{query}', user_id={user_id}")
        
        # التحقق من البوت في المجموعة
        if self.assistant:
            try:
                me = await self.assistant.get_me()
                member = await self.assistant.get_chat_member(chat_id, "me")
                logger.info(f"✅ Bot status: {member.status}")
            except Exception as e:
                logger.error(f"❌ Bot not in group: {e}")
                return {"ok": False, "error": f"البوت ليس في المجموعة: {str(e)}"}

        # ✅ جلب رابط الأغنية مع إعادة المحاولة
        try:
            logger.info(f"🔍 Searching for: {query}")
            title, stream_url = await self._get_stream_url_with_retry(query)
            logger.info(f"✅ Found: {title}")
        except Exception as e:
            logger.error(f"❌ SEARCH ERROR: {e}")
            logger.error(traceback.format_exc())
            return {"ok": False, "error": f"فشل جلب الأغنية: {str(e)}"}

        # إضافة للقائمة والتشغيل
        track = Track(title=title, url=stream_url, query=query, user_id=user_id)
        gq = queue_manager.get(chat_id)
        pos = gq.add(track)

        if not gq.is_playing:
            result = await self._start_playback(chat_id)
            if not result["ok"]:
                return result

        return {"ok": True, "title": title, "position": pos}

    async def _get_stream_url_with_retry(self, query: str, max_retries: int = 3) -> tuple[str, str]:
        """الحصول على الرابط مع إعادة المحاولة"""
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Attempt {attempt + 1}/{max_retries}")
                
                # ✅ تدوير العملاء عند إعادة المحاولة
                result = await self._get_stream_url(query, attempt)
                
                if result and result[0] and result[1]:
                    return result
                    
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ Attempt {attempt + 1} failed: {e}")
                
                # تأخير عشوائي قبل إعادة المحاولة
                if attempt < max_retries - 1:
                    delay = random.uniform(1, 3)
                    logger.info(f"⏳ Waiting {delay:.1f}s before retry...")
                    await asyncio.sleep(delay)
        
        raise Exception(f"فشل بعد {max_retries} محاولات: {last_error}")

    async def _get_stream_url(self, query: str, attempt: int = 0) -> tuple[str, str]:
        """الحصول على رابط مباشر - yt-dlp أساسي، pytube احتياطي"""
        
        loop = asyncio.get_event_loop()
        
        # ✅ المحاولة 1: yt-dlp (الأساسي الآن)
        if YTDLP_AVAILABLE:
            try:
                # تغيير الإعدادات حسب المحاولة
                opts = self._get_ytdlp_opts_for_attempt(attempt)
                return await loop.run_in_executor(None, self._get_ytdlp_url, query, opts)
            except Exception as e:
                logger.warning(f"⚠️ yt-dlp failed (attempt {attempt}): {e}")
        
        # ✅ المحاولة 2: pytube (احتياطي)
        if PYTUBE_AVAILABLE:
            try:
                return await loop.run_in_executor(None, self._get_pytube_url, query)
            except Exception as e:
                logger.warning(f"⚠️ pytube failed: {e}")
        
        raise Exception("جميع المصادر فشلت")

    def _get_ytdlp_opts_for_attempt(self, attempt: int) -> dict:
        """تعديل الإعدادات حسب المحاولة"""
        
        opts = self.ydl_opts_base.copy()
        
        # ✅ تدوير العملاء عند الفشل
        clients = [
            "android_vr,web_safari",
            "web_safari",
            "android_vr",
            "tv",
        ]
        
        if attempt < len(clients):
            opts["extractor_args"]["youtube"]["player_client"] = clients[attempt]
            logger.info(f"🔄 Using client: {clients[attempt]}")
        
        # ✅ إزالة الكوكيز في المحاولة الأخيرة إذا فشلت
        if attempt == 2 and "cookiefile" in opts:
            del opts["cookiefile"]
            logger.info("🔄 Retrying without cookies")
        
        return opts

    def _get_ytdlp_url(self, query: str, opts: dict = None) -> tuple[str, str]:
        """استخدام yt-dlp للحصول على رابط مباشر - المحسن"""
        
        if opts is None:
            opts = self.ydl_opts_base
        
        search = query if query.startswith("http") else f"ytsearch1:{query}"
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                # ✅ إضافة معلومات التصحيح في وضع التطوير
                logger.info(f"🔍 Extracting with yt-dlp: {search[:50]}...")
                
                info = ydl.extract_info(search, download=False)
                
                if info is None:
                    raise Exception("لم يتم استلام معلومات")
                
                if "entries" in info:
                    entries = info["entries"]
                    if not entries or len(entries) == 0:
                        raise Exception("لا توجد نتائج")
                    info = entries[0]
                
                title = info.get('title', query)
                
                # ✅ البحث عن أفضل رابط صوتي
                url = None
                formats = info.get('formats', [])
                
                # تفضيل الصوت فقط
                audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                if audio_formats:
                    # ترتيب حسب الجودة
                    audio_formats.sort(key=lambda x: x.get('abr', 0), reverse=True)
                    url = audio_formats[0].get('url')
                    logger.info(f"✅ Selected audio format: {audio_formats[0].get('abr')}k")
                
                # إذا لم يوجد صوت فقط، استخدم أي تنسيق
                if not url and formats:
                    formats.sort(key=lambda x: (x.get('tbr', 0) or 0), reverse=True)
                    url = formats[0].get('url')
                
                # رابط مباشر من المعلومات
                if not url:
                    url = info.get('url')
                
                if not url:
                    raise Exception("لا يوجد رابط مباشر متاح")
                
                # ✅ التحقق من صحة الرابط
                if not url.startswith('http'):
                    raise Exception(f"رابط غير صالح: {url[:50]}")
                
                logger.info(f"✅ yt-dlp success: {title}")
                return title, url
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ yt-dlp error: {error_msg}")
            
            # ✅ معالجة أخطاء معروفة
            if "Sign in to confirm" in error_msg:
                raise Exception("YouTube يتطلب تسجيل الدخول - حاول إضافة ملف cookies.txt")
            elif "bot" in error_msg.lower():
                raise Exception("تم كشف البوت - جرب تشغيل البوت محلياً بدلاً من Render")
            elif "unavailable" in error_msg.lower():
                raise Exception("الفيديو غير متاح")
            else:
                raise

    def _get_pytube_url(self, query: str) -> tuple[str, str]:
        """استخدام pytube كاحتياطي - بدون بروكسي"""
        
        # إذا كان الرابط مباشر
        if query.startswith("http"):
            video_url = query
            try:
                yt = YouTube(video_url)
                title = yt.title
                
                # ✅ بدون استخدام البروكسي (يسبب الأخطاء)
                audio_stream = yt.streams.filter(only_audio=True).first()
                if not audio_stream:
                    audio_stream = yt.streams.get_audio_only()
                
                if not audio_stream:
                    raise Exception("لا يوجد تدفق صوتي")
                
                direct_url = audio_stream.url
                logger.info(f"✅ pytube success (direct URL): {title}")
                return title, direct_url
                
            except Exception as e:
                raise Exception(f"pytube failed: {e}")
        
        # ✅ البحث بدون بروكسي
        logger.info(f"🔍 youtube-search: {query}")
        search = VideosSearch(query, limit=3)
        results = search.result()
        
        if not results or not results.get('result'):
            raise Exception("لا توجد نتائج بحث")
        
        # تجربة النتائج
        for video in results['result']:
            try:
                video_url = video['link']
                title = video['title']
                logger.info(f"🎬 Trying pytube: {title}")
                
                yt = YouTube(video_url)
                real_title = yt.title  # العنوان الحقيقي من YouTube
                
                audio_stream = yt.streams.filter(only_audio=True).first()
                if not audio_stream:
                    audio_stream = yt.streams.get_audio_only()
                
                if audio_stream:
                    direct_url = audio_stream.url
                    logger.info(f"✅ pytube success: {real_title}")
                    return real_title, direct_url
                    
            except Exception as e:
                logger.warning(f"⚠️ فشلت {video.get('title', 'unknown')}: {e}")
                continue
        
        raise Exception("جميع نتائج pytube فشلت")

    async def _start_playback(self, chat_id: int) -> dict:
        """بدء التشغيل"""
        gq = queue_manager.get(chat_id)
        track = gq.current()
        
        if not track:
            gq.is_playing = False
            return {"ok": False, "error": "لا يوجد أغنية في القائمة"}

        gq.is_playing = True
        gq.is_paused = False

        try:
            logger.info(f"▶️ Starting playback: {track.title}")
            
            # ✅ إضافة معاملات FFmpeg للاستقرار
            stream = MediaStream(
                track.url,
                audio_parameters=AudioQuality.HIGH,
            )
            
            await self.calls.play(chat_id, stream)
            logger.info(f"✅ Playing: {track.title}")
            return {"ok": True}

        except Exception as e:
            logger.error(f"❌ Playback error: {e}")
            logger.error(traceback.format_exc())
            gq.is_playing = False
            return {"ok": False, "error": f"فشل التشغيل: {str(e)}"}

    # ... بقية الدوال (stop, skip, pause, resume, get_queue) كما هي ...

    def _register_callbacks(self):
        @self.calls.on_update()
        async def on_stream_ended(_, update):
            if isinstance(update, StreamEnded):
                chat_id = update.chat_id
                logger.info(f"🔴 Stream ended: {chat_id}")
                
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


# ✅ الكلاسات المساعدة (بدون تغيير)
class Track:
    def __init__(self, title: str, url: str, query: str, user_id: int):
        self.title = title
        self.url = url
        self.query = query
        self.user_id = user_id

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

