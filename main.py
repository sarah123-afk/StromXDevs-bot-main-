import os

import asyncio
import traceback
from threading import Thread
from datetime import datetime

import aiohttp
import discord
from discord.ext import commands


from core import Context
from core.Cog import Cog
from core.StromXDevs import StromXDevs
from utils.Tools import *
from utils.config import *
from utils.stromx_emojis import emoji as stromx_emoji, load_application_emojis

import cogs 



from utils.config import OWNER_IDS
client = StromXDevs()
tree = client.tree
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN is not set. In Termux run: export TOKEN=YOUR_BOT_TOKEN")




@client.event
async def on_ready():
    await client.wait_until_ready()
    loaded_emoji_count = await load_application_emojis(client)
    print(f"Loaded {loaded_emoji_count} StromXDevs application emojis")
    
    print(r"""
[1;35m        ____   ___  _   _ _   _
       / ___| / _ \| \ | | | | |
       \___ \| | | |  \| | | | |
        ___) | |_| | |\  | |_| |
       |____/ \___/|_| \_| \___/
[0m""")
    print("Loaded & Online!")
    print(f"Logged in as: {client.user}")
    print(f"Connected to: {len(client.guilds)} guilds")
    print(f"Connected to: {len(client.users)} users")
    try:
        synced = await client.tree.sync()
        all_commands = list(client.commands)
        print(f"Synced Total {len(all_commands)} Client Commands and {len(synced)} Slash Commands")
    except Exception as e:
        print(e)


@client.event
async def on_command_completion(context: commands.Context) -> None:
    if context.author.id in OWNER_IDS:
        return

    full_command_name = context.command.qualified_name
    split = full_command_name.split("\n")
    executed_command = str(split[0])
    STROMX_RIGHT = stromx_emoji("1000445529", "➜")
    webhook_url = os.getenv("LOG_WEBHOOK_URL")
    if not webhook_url:
        return
    async with aiohttp.ClientSession() as session:
        webhook = discord.Webhook.from_url(webhook_url, session=session)

        if context.guild is not None:
            try:
                embed = discord.Embed(color=0x000000)
                avatar_url = context.author.avatar.url if context.author.avatar else context.author.default_avatar.url
                embed.set_author(
                    name=f"Executed {executed_command} Command By : {context.author}",
                    icon_url=avatar_url
                )
                embed.set_thumbnail(url=avatar_url)
                embed.add_field(name=f"{STROMX_RIGHT} Command Name :",
                                value=f"{executed_command}",
                                inline=False)
                embed.add_field(
                    name=f"{STROMX_RIGHT} Command Executed By :",
                    value=f"{context.author} | ID: [{context.author.id}](https://discord.com/users/{context.author.id})",
                    inline=False)
                embed.add_field(
                    name=f"{STROMX_RIGHT} Command Executed In :",
                    value=f"{context.guild.name} | ID: [{context.guild.id}](https://discord.com/guilds/{context.guild.id})",
                    inline=False)
                embed.add_field(
                    name=f"{STROMX_RIGHT} Command Executed In Channel :",
                    value=f"{context.channel.name} | ID: [{context.channel.id}](https://discord.com/channels/{context.guild.id}/{context.channel.id})",
                    inline=False)

                embed.timestamp = discord.utils.utcnow()
                embed.set_footer(text="StromXDevs Development™ ❤️",
                                 icon_url=client.user.display_avatar.url)

                
                await webhook.send(embed=embed)
            except Exception as e:
                print(f'Command failed: {e}')
                traceback.print_exc()
        else:
            try:
                embed1 = discord.Embed(color=0x000000)
                avatar_url = context.author.avatar.url if context.author.avatar else context.author.default_avatar.url
                embed1.set_author(
                    name=f"Executed {executed_command} Command By : {context.author}",
                    icon_url=avatar_url
                )
                embed1.set_thumbnail(url=avatar_url)
                embed1.add_field(name=f"{STROMX_RIGHT} Command Name :",
                                 value=f"{executed_command}",
                                 inline=False)
                embed1.add_field(
                    name=f"{STROMX_RIGHT} Command Executed By :",
                    value=f"{context.author} | ID: [{context.author.id}](https://discord.com/users/{context.author.id})",
                    inline=False)
                embed1.set_footer(text=f"Powered by StromXDevs Development™",
                                  icon_url=client.user.display_avatar.url)
                print("Sending embed1 to webhook...")
                await webhook.send(embed=embed1)
                print("Embed1 sent successfully.")
            except Exception as e:
                print(f'Command failed: {e}')
                traceback.print_exc()


from flask import Flask
from threading import Thread

app = Flask(__name__)


@app.route('/')
def home():
    return f"© StromXDevs Development 2024"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    server = Thread(target=run, daemon=True)
    server.start()


keep_alive()


async def main():
    async with client:
        os.system("clear")
        #await client.load_extension("cogs")
        await client.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
