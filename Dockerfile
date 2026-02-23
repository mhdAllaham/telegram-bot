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

# Expose port (default for mostly Cloud Services)
EXPOSE 8000

# Run the bot using Gunicorn Webhook server
CMD ["gunicorn", "bot:app", "-b", "0.0.0.0:8000"]
