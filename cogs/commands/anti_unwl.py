import discord
from discord.ext import commands
import aiosqlite
from utils.Tools import *


class Unwhitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.initialize_db())

    #@commands.Cog.listener()
    async def initialize_db(self):
        self.db = await aiosqlite.connect('db/anti.db')

    @commands.hybrid_command(name='unwhitelist', aliases=['unwl'], help="Unwhitelist a user from antinuke")
    @commands.has_permissions(administrator=True)
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.max_concurrency(1, per=commands.BucketType.default, wait=False)
    @commands.guild_only()
    async def unwhitelist(self, ctx, member: discord.Member = None):
        if ctx.guild.member_count < 2:
            embed = discord.Embed(
                color=0x000000,
                description="❌ | Your Server Doesn't Meet My 30 Member Criteria"
            )
            return await ctx.send(embed=embed)

        async with self.db.execute(
            "SELECT status FROM antinuke WHERE guild_id = ?",
            (ctx.guild.id,)
        ) as cursor:
            antinuke = await cursor.fetchone()

        if not antinuke or not antinuke[0]:
            embed = discord.Embed(
                color=0x000000,
                description=(
                    f"**{ctx.guild.name} Security Settings 🛡️\n"
                    "Ohh NO! looks like your server doesn't enabled security\n\n"
                    "Current Status : ❌\n\n"
                    "To enable use `antinuke enable` **"
                )
            )
            return await ctx.send(embed=embed)

        if not member:
            embed = discord.Embed(
                color=0x000000,
                title="__**Unwhitelist Commands**__",
                description="**Removes user from whitelisted users which means that the antinuke module will now take actions on them if they trigger it.**"
            )
            embed.add_field(name="__**Usage**__", value="🔴 `unwhitelist @user/id`\n🔴 `unwl @user`")
            return await ctx.send(embed=embed)

        async with self.db.execute(
            "SELECT * FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id)
        ) as cursor:
            data = await cursor.fetchone()

        if not data:
            embed = discord.Embed(title="❌ Error",
                color=0x000000,
                description=f"<@{member.id}> is not a whitelisted member."
            )
            return await ctx.send(embed=embed)

        await self.db.execute(
            "DELETE FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, member.id)
        )
        await self.db.commit()

        embed = discord.Embed(title="✅ Success",
            color=0x000000,
            description=f"User <@!{member.id}> has been removed from the whitelist."
        )
        await ctx.send(embed=embed)


"""
@Author: Sonu Jana
    + Discord: me.sonu
    + Community: https://discord.gg/odx (StromXDevs Development)
    + for any queries reach out Community or DM me.
"""