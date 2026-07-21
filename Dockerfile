FROM python:3.10-slim

WORKDIR /app

# ដំឡើងកម្មវិធីជំនួយរបស់ Linux ដោយប្រើឈ្មោះ Package ដែលដើរស្រួលបំផុតលើ Render
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["python", "bot.py"]
