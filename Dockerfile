# ប្រើប្រាស់ Python ជំនាន់ 3.10
FROM python:3.10-slim

# ដំឡើងកម្មវិធីជំនួយរបស់ Linux សម្រាប់ឱ្យ WeasyPrint អាចគូរ PDF បាន
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-cffi \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

# បង្កើតទីតាំងធ្វើការងារក្នុង Server
WORKDIR /app

# ដំឡើងកញ្ចប់កម្មវិធីពី requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ចម្លងកូដទាំងអស់ចូល
COPY . .

# បើក Port សម្រាប់ Flask (ដើម្បីឱ្យ UptimeRobot អាច Ping បាន)
EXPOSE 10000

# បញ្ជាឱ្យដំណើរការ Bot
CMD ["python", "bot.py"]