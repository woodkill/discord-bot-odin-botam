import discord
import logging
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object
import btdb


class Boss(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        import btdb
        self.db: btdb.BtDb = bot.db
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info(f"Boss Cog loaded.")

    @commands.command(name=u"보스등록")
    async def register_boss(self, ctx: commands.Context, *args):
        self.logger.debug(f"보스등록 {args}")
        await self.bot.wait_until_ready()
        # 명령어 형식이 맞는지 검사
        if len(args) != 2:
            await ctx.reply(f"사용법 : .보스등록 ***보스명 남은시간***")
            return
        odin_boss_name = args[0]
        str_remain_time = args[1]

        # 보스명이 보스목록에 있는지 검사
        # 길드등록되어 있는지 검사
        success, odin_server_name, odin_guild_ame = self.db.get_odin_guild_info(ctx.guild.id)
        if not success:
            await ctx.reply(f"사용법 : .보스등록 ***보스명 남은시간***")
            return


    #     if len(args) != 2:
    #         await ctx.reply(f"사용법 : .길드등록 ***오딘서버명 길드명***")
    #         return
    #     odin_server_name = args[0]
    #     odin_guild_name = args[1]
    #     if not self.db.check_valid_server_name(odin_server_name):
    #         await ctx.reply(f"올바른 오딘서버명이 아닙니다 : '{odin_server_name}'")
    #         return
    #     success = self.db.set_odin_guild_info(ctx.guild.id, odin_server_name, odin_guild_name)
    #     if not success:
    #         await ctx.reply(f"길드등록에 실패하였습니다.")
    #         return
    #     await ctx.reply(f"길드등록 완료 : {odin_server_name}/{odin_guild_name}")
    #
    # @commands.command(name=u"길드확인")
    # async def check_guild(self, ctx: commands.Context):
    #     self.logger.debug(f"길드확인")
    #     success, odin_server_name, odin_guild_ame = self.db.get_odin_guild_info(ctx.guild.id)
    #     if success:
    #         await ctx.reply(f"{odin_server_name}/{odin_guild_ame}")
    #     else:
    #         await ctx.reply(f"등록된 길드가 없습니다.")


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup")
    await bot.add_cog(Boss(bot))