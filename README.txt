╔══════════════════════════════════════════════════════════╗
   🔥 FREE 24/7 TELEGRAM BOT HOSTING - COMPLETE GUIDE 🔥
   📢 Channel: @ajaymodsv1
   👨‍💻 Owner: @AJAY_MODS
╚══════════════════════════════════════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INSIDE THIS ZIP FILE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. bot.py           → Main bot code
  2. requirements.txt → Package list
  3. README.txt       → This guide

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 1 — Create a Webhostmost Account
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🌐 Website: https://webhostmost.com
  → Sign up for Free Hosting
  → Verify your Email
  → Log in to cPanel

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 2 — Get Your Telegram Bot Token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → Go to @BotFather on Telegram
  → Type /newbot
  → Give your bot a name and username
  → Copy the Token

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 3 — Put the Token in bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → Open the bot.py file
  → BOT_TOKEN = "put your token here"
  → Save the file

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 4 — Create a Python App
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → cPanel → Setup Python App
  → Create Application
  → Python Version: 3.11
  → Application Root: Pybot
  → Click the Create button

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 5 — Upload bot.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → cPanel → File Manager
  → Open the Pybot/Bot/ folder
  → Upload bot.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 6 — Install Packages
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → cPanel → Open Terminal
  → First, find the pip path:

    find /home/$(whoami)/virtualenv -name "pip" 2>/dev/null

  → Install using the path shown:

    /home/USERNAME/virtualenv/Pybot/3.11/bin/pip install pyTelegramBotAPI psutil requests

  ⚠️ Replace USERNAME with your actual username
  ⚠️ To find your username: echo $HOME

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 7 — Run the Bot for the First Time
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → In Terminal, run:

    /home/USERNAME/virtualenv/Pybot/3.11/bin/python3 /home/USERNAME/Pybot/Bot/bot.py

  → Send /start on Telegram — if it works, move to the next step

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ STEP 8 — Set Up a Cron Job (to keep it running 24/7)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  → cPanel → Cron Jobs
  → Put * in every field (Every Minute)
  → In the Command box, enter:

    /usr/bin/flock -n /tmp/bot.lock /home/USERNAME/virtualenv/Pybot/3.11/bin/python3 /home/USERNAME/Pybot/Bot/bot.py > /dev/null 2>&1

  → Click Add New Cron Job ✅

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛠️ USEFUL COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Find username:        echo $HOME
  Stop the bot:         pkill -f bot.py
  Check if bot runs:    pgrep -f bot.py
  Delete lock file:     rm -f /tmp/bot.lock
  Find bot.py:          find /home/$(whoami) -name "bot.py" 2>/dev/null

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BOT FEATURES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Upload .py / .js / .zip files
  ✅ Auto package install
  ✅ Start / Stop / Restart
  ✅ Real-time Logs
  ✅ CPU & RAM monitoring
  ✅ 10 files per user
  ✅ Runs 24/7

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢 Channel: @ajaymodsv1
👨‍💻 Owner: @AJAY_MODS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━