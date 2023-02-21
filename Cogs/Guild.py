import discord
import logging
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object

class Guild(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Guild Cog loaded.")

    # / command를 등록하는 코드같음
    # @commands.command(name='sync')
    # async def sync(self, ctx) -> None:
    #     fmt = await ctx.bot.tree.sync(guild=ctx.guild)
    #     await ctx.send(f'Synced {len(fmt)} commands')

    # @app_commands.command(name='sample', description=u"테스트")
    # async def hello(self, interaction: discord.Interaction, hello: str):
    #     await interaction.response.send_message('Answered')

    @commands.command(name=u"길드등록")
    async def register_guild(self, ctx, *args):
        self.logger.debug(f"{args}")
        # self.logger.info(f"길드등록 command")
        # await ctx.send("hi")


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup")
    await bot.add_cog(Guild(bot))
