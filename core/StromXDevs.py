from __future__ import annotations
from discord.ext import commands
import discord
import aiohttp
import json
import asyncio
import typing
from typing import List
import aiosqlite
from utils.config import OWNER_IDS
from utils import getConfig, updateConfig
from .Context import Context
from discord.ext import commands, tasks
from colorama import Fore, Style, init
import importlib
import inspect
import time

init(autoreset=True)

extensions: List[str] = [
    "cogs"
]

class StromXDevs(commands.AutoShardedBot):

    def __init__(self, *arg, **kwargs):
        self.started_at = time.time()
        intents = discord.Intents.all()
        intents.presences = True
        intents.members = True
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            intents=intents,
            status=discord.Status.do_not_disturb,
            strip_after_prefix=True,
            owner_ids=OWNER_IDS,
            allowed_mentions=discord.AllowedMentions(
                everyone=False, replied_user=False, roles=False,
            ),
        )

    async def setup_hook(self):
        await self.load_extensions() 

    async def load_extensions(self):
        for extension in extensions:
            try:
                await self.load_extension(extension) 
                print(Fore.GREEN + Style.BRIGHT + f"Loaded extension: {extension}")
            except Exception as e:
                print(
                    f"{Fore.RED}{Style.BRIGHT}Failed to load extension {extension}. {e}"
                )
        print(Fore.GREEN + Style.BRIGHT + "*" * 20)

    
    async def on_connect(self):
        await self.change_presence(status=discord.Status.do_not_disturb,
                                   activity=discord.Activity(
                                       type=discord.ActivityType.playing,
                                       name='$help | .gg/odx'))

    async def send_raw(self, channel_id: int, content: str,
                       **kwargs) -> typing.Optional[discord.Message]:
        await self.http.send_message(channel_id, content, **kwargs)

    async def invoke_help_command(self, ctx: Context) -> None:
        """Invoke the help command or default help command if help extensions is not loaded."""
        return await ctx.send_help(ctx.command)

    async def fetch_message_by_channel(
            self, channel: discord.TextChannel,
            messageID: int) -> typing.Optional[discord.Message]:
        async for msg in channel.history(
                limit=1,
                before=discord.Object(messageID + 1),
                after=discord.Object(messageID - 1),
        ):
            return msg

    async def get_prefix(self, message: discord.Message):
        """Return the configured prefix, plus an empty prefix for approved no-prefix users."""
        # Bot owners always get no-prefix, even if they are not stored in db/np.db.
        # The database is for additional no-prefix users; OWNER_IDS is authoritative.
        is_np = message.author.id in OWNER_IDS
        try:
            async with aiosqlite.connect("db/np.db") as db:
                # The NP cog initializes this database asynchronously; make the table safe
                # to query even if a message arrives during startup.
                await db.execute(
                    "CREATE TABLE IF NOT EXISTS np (id INTEGER PRIMARY KEY, expiry_time TEXT NULL)"
                )
                if not is_np:
                    async with db.execute(
                        "SELECT 1 FROM np WHERE id = ?", (message.author.id,)
                    ) as cursor:
                        is_np = await cursor.fetchone() is not None
                await db.commit()
        except aiosqlite.Error as exc:
            print(f"[NoPrefix] Could not check no-prefix status: {exc}")

        if message.guild:
            data = await getConfig(message.guild.id)
            prefix = data.get("prefix", "$")
            if is_np:
                return commands.when_mentioned_or(prefix, "")(self, message)
            return commands.when_mentioned_or(prefix)(self, message)

        # In DMs, preserve the bot's $ prefix; only approved NP users get blank prefix.
        if is_np:
            return commands.when_mentioned_or("$", "")(self, message)
        return commands.when_mentioned_or("$")(self, message)

    async def process_commands(self, message: discord.Message) -> None:
        """Process each Discord message at most once per bot process.

        This guards against duplicate command invocation if another event handler
        accidentally routes the same message to process_commands more than once.
        """
        if not hasattr(self, "_processed_command_message_ids"):
            self._processed_command_message_ids = set()
            self._processed_command_message_order = []

        message_id = message.id
        if message_id in self._processed_command_message_ids:
            return

        self._processed_command_message_ids.add(message_id)
        self._processed_command_message_order.append(message_id)

        # Bound memory use on long-running bots.
        if len(self._processed_command_message_order) > 5000:
            old_id = self._processed_command_message_order.pop(0)
            self._processed_command_message_ids.discard(old_id)

        await super().process_commands(message)

    async def on_message_edit(self, before, after):
        # Do not invoke commands again when a command message is edited.
        # Commands are processed once by discord.py when the message is first sent.
        return



def setup_bot():
    intents = discord.Intents.all()
    bot = StromXDevs(intents=intents)
    return bot
