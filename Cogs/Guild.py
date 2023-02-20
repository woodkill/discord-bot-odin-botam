import discord
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object


class Guild(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Guild Cog loaded.")

    @commands.command(name='sync')
    async def sync(self, ctx) -> None:
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f'Synced {len(fmt)} commands')

    @app_commands.command(name='hello', description=u"테스트인사말")
    async def hello(self, interaction: discord.Interaction, hello: str):
        await interaction.response.send_message('Answered')

    # @commands.command(name="hello", description=u"테스트인사말")
    # async def hello(self, ctx):
    #     await ctx.send("hi")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Guild(bot))
