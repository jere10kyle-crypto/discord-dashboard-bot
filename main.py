import discord
from discord.ext import commands
import json
import os
import asyncio
from threading import Thread
from collections import defaultdict
import time
import web  # your web.py dashboard

# ---------------------
# Bot setup
# ---------------------
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------
# Files and storage
# ---------------------
user_message_history = defaultdict(list)  # for spam tracking

def load_banned_words():
    if not os.path.exists("banned_words.json"):
        with open("banned_words.json", "w") as f:
            json.dump({"words": []}, f)
    with open("banned_words.json", "r") as f:
        return json.load(f)["words"]

def load_strikes():
    if not os.path.exists("strikes.json"):
        with open("strikes.json", "w") as f:
            json.dump({}, f)
    with open("strikes.json", "r") as f:
        return json.load(f)

def save_strikes(strikes):
    with open("strikes.json", "w") as f:
        json.dump(strikes, f)

# ---------------------
# Bot events
# ---------------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    user_id = str(message.author.id)
    content = message.content.lower()
    current_time = time.time()

    # ---------------------
    # Spam detection
    # ---------------------
    user_message_history[user_id].append((content, current_time))
    # keep only last 10 seconds
    user_message_history[user_id] = [
        (msg, t) for msg, t in user_message_history[user_id] if current_time - t < 10
    ]
    repeated = [msg for msg, t in user_message_history[user_id] if msg == content]
    if len(repeated) >= 3:
        await message.delete()
        strikes = load_strikes()
        strikes[user_id] = strikes.get(user_id, 0) + 1
        save_strikes(strikes)
        await message.channel.send(
            f"{message.author.mention} stop spamming! Strike {strikes[user_id]}/3"
        )
        # Log it
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f:
                logs = json.load(f)
        else:
            logs = []
        logs.append({"user": message.author.name, "message": message.content, "type": "spam"})
        with open("logs.json", "w") as f:
            json.dump(logs, f)
        # Mute 10 min
        mute_role = discord.utils.get(message.guild.roles, name="Muted")
        if mute_role:
            await message.author.add_roles(mute_role)
            await message.channel.send(f"{message.author.mention} muted for 10 minutes for spamming.")
            await asyncio.sleep(600)  # 10 min
            await message.author.remove_roles(mute_role)
        return

    # ---------------------
    # Banned words
    # ---------------------
    banned_words = load_banned_words()
    if any(word in content for word in banned_words):
        await message.delete()
        strikes = load_strikes()
        strikes[user_id] = strikes.get(user_id, 0) + 1
        save_strikes(strikes)
        await message.channel.send(f"{message.author.mention} used a banned word! Strike {strikes[user_id]}/3")
        # Log it
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f:
                logs = json.load(f)
        else:
            logs = []
        logs.append({"user": message.author.name, "message": message.content, "type": "banned_word"})
        with open("logs.json", "w") as f:
            json.dump(logs, f)
        # Mute 10 min
        mute_role = discord.utils.get(message.guild.roles, name="Muted")
        if mute_role:
            await message.author.add_roles(mute_role)
            await message.channel.send(f"{message.author.mention} muted for 10 minutes.")
            await asyncio.sleep(600)
            await message.author.remove_roles(mute_role)
        return

    await bot.process_commands(message)

# ---------------------
# Web dashboard (basic)
# ---------------------
def run_web():
    web.app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# ---------------------
# Run bot
# ---------------------
bot.run(os.environ["BOT_TOKEN"])
