FROM python:3.9-slim

# Install LibreOffice and required fonts for DOCX to PDF conversion
RUN apt-get update && \
    apt-get install -y libreoffice --no-install-recommends && \
    apt-get install -y fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run the bot
CMD ["python", "bot.py"]
