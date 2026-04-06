import discord
from discord.ext import commands
import json
import os
from threading import Thread
import web  # dashboard

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def load_banned_words():
    with open("banned_words.json", "r") as f:
        return json.load(f)["words"]

def load_strikes():
    with open("strikes.json", "r") as f:
        return json.load(f)

def save_strikes(strikes):
    with open("strikes.json", "w") as f:
        json.dump(strikes, f)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    banned_words = load_banned_words()
    strikes = load_strikes()

    if any(word in message.content.lower() for word in banned_words):
        user_id = str(message.author.id)
        strikes[user_id] = strikes.get(user_id, 0) + 1
        save_strikes(strikes)

        await message.delete()
        await message.channel.send(f"{message.author.mention} strike! ({strikes[user_id]}/3)")

        if strikes[user_id] >= 3:
            mute_role = discord.utils.get(message.guild.roles, name="Muted")
            if mute_role:
                await message.author.add_roles(mute_role)
                await message.channel.send(f"{message.author.mention} muted for 1 minute!")
                await discord.utils.sleep_until(60)
                await message.author.remove_roles(mute_role)
                strikes[user_id] = 0
                save_strikes(strikes)

    # log messages
    with open("logs.json", "r") as f:
        logs = json.load(f)

    logs.append({"user": message.author.name, "message": message.content})

    with open("logs.json", "w") as f:
        json.dump(logs, f)

    await bot.process_commands(message)

def run_web():
    web.app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

bot.run(os.environ["BOT_TOKEN"])
