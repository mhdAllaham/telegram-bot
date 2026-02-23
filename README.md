# File Conversion Bot (PDF ↔ DOCX) 🤖

This bot is built with Python and coverts files from PDF to Word (DOCX) and vice versa.
The maximum supported file size is 10 MB.

## Requirements:
This project is containerized using **Docker**, making it easy to deploy on any free hosting service that supports Docker.

## Free Hosting (Using Koyeb):
The platform [Koyeb.com](https://www.koyeb.com/) provides excellent, free hosting that supports running Docker containers in the background (as a Worker). This is perfect for this bot because it uses long-polling and does not require opening any web ports.

### Steps to Deploy:
1. Upload the files in this folder (`bot.py`, `requirements.txt`, `Dockerfile`) to a new repository on **GitHub**.
2. Go to [BotFather](https://t.me/BotFather) on Telegram to create a new bot and obtain your `BOT_TOKEN`.
3. Create a free account on [Koyeb](https://www.koyeb.com/).
4. Click on **Create Web Service** (or Create App) and select the deployment source from **GitHub**.
5. Connect your GitHub account and select the repository you just uploaded.
6. In the builder settings, make sure to choose **Dockerfile**.
7. In the **Environment variables** section, add the following variable:
   - Key: `BOT_TOKEN`
   - Value: (The token you got from BotFather)
8. **CRITICAL STEP:** In the **Advanced** section, change the "Service Type" from **Web Service** to **Worker**. (This is necessary because the bot runs in the background via polling and doesn't receive HTTP requests).
9. Select the **Free** tier/instance and click **Deploy**.

The system will start building the container and installing `LibreOffice` and Python libraries. Once finished, your bot will be available 24/7 for free!

## Running Locally:
If you want to test it on your computer:
1. Install `python`.
2. Install [LibreOffice](https://www.libreoffice.org/download/download-libreoffice/) (This is required for Word to PDF conversion).
3. Install the required packages: `pip install -r requirements.txt`
4. Add the bot token as an environment variable. In your Command Prompt (CMD) run:
   `set BOT_TOKEN=your_token`
5. Run the bot: `python bot.py`
