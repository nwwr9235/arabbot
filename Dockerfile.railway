FROM python:3.11-slim

# تثبيت FFmpeg والأدوات الأساسية
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg git curl wget build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ✅ تحقق بسيط — بدون AudioPiped
RUN python -c "from pytgcalls import PyTgCalls; print('✅ PyTgCalls جاهز')"

COPY . .

CMD ["python", "main.py"]
