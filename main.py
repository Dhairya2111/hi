import os, asyncio, threading, requests, time
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import MemorySession

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Awake and Running!", 200

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Using MemorySession to avoid SQLite database locks
bot = TelegramClient(MemorySession(), API_ID, API_HASH)

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.reply("<b>I am Awake!</b>\nSend me any media to get a link.", parse_mode='html')

@bot.on(events.NewMessage)
async def media_handler(event):
    if event.media and not (event.text and event.text.startswith('/')):
        msg = await event.reply("<code>🔄 Processing...</code>", parse_mode='html')
        file_path = await event.download_media()
        try:
            # Uploading to Catbox (More reliable than Telegraph)
            files = {'fileToUpload': open(file_path, 'rb')}
            data = {'reqtype': 'fileupload', 'userhash': ''}
            response = requests.post("https://catbox.moe/user/api.php", data=data, files=files)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if response.status_code == 200:
                url = response.text.strip()
                await msg.edit(f"<b>✅ Link:</b> <code>{url}</code>", parse_mode='html', link_preview=False)
            else:
                await msg.edit("❌ Upload failed.")
        except Exception as e:
            await msg.edit(f"❌ Error: {str(e)}")

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# Self-pinging function to keep Render alive
def keep_alive():
    url = os.getenv("RENDER_EXTERNAL_URL") # Render provides this automatically
    if not url:
        return
    while True:
        try:
            requests.get(url)
            print("Self-ping successful!")
        except:
            print("Self-ping failed.")
        time.sleep(600) # Ping every 10 minutes

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    print("Bot starting...")
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()