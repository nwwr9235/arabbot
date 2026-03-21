FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ✅ التغيير المهم: إضافة music_bot/
COPY music_bot/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# ✅ تحديث yt-dlp لأحدث نسخة (مهم جداً لأن يوتيوب يتغير باستمرار)
RUN pip install --no-cache-dir --upgrade yt-dlp

COPY . .

# ✅ ملف الكوكيز لتجاوز قيود يوتيوب
COPY cookies.txt /app/cookies.txt

CMD ["python", "-m", "music_bot.main"]
