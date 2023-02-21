import discord
import logging
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object
import btdb


class Guild(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        import btdb
        self.db: btdb.BtDb = bot.db
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
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
    async def register_guild(self, ctx: commands.Context, *args) -> None:
        '''
        "길드등록" 명령어를 처리한다.
        :param ctx: context
        :param args: 오딘서버명, 길드명
        :return: 없음
        '''
        self.logger.debug(f"길드등록 {args}")
        if len(args) != 2:
            await ctx.reply(f"사용법 : .길드등록 ***오딘서버명 길드명***")
            return
        odin_server_name = args[0]
        odin_guild_name = args[1]
        if not self.db.check_valid_server_name(odin_server_name):
            await ctx.reply(f"올바른 오딘서버명이 아닙니다 : '{odin_server_name}'")
            return
        success = self.db.set_odin_guild_info(ctx.guild.id, odin_server_name, odin_guild_name)
        if not success:
            await ctx.reply(f"길드등록에 실패하였습니다.")
            return
        await ctx.reply(f"길드등록 완료 : {odin_server_name}/{odin_guild_name}")

    @commands.command(name=u"길드확인")
    async def check_guild(self, ctx: commands.Context) -> None:
        '''
        "길드확인" 명령어를 처리한다.
        :param ctx: context
        :return: 없음
        '''
        self.logger.debug(f"길드확인")
        success, odin_server_name, odin_guild_ame = self.db.get_odin_guild_info(ctx.guild.id)
        if success:
            await ctx.reply(f"{odin_server_name}/{odin_guild_ame}")
        else:
            await ctx.reply(f"등록된 길드가 없습니다.")


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup")
    await bot.add_cog(Guild(bot))
