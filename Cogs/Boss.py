import logging
import discord
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object
import btdb
from const_key import *
from common import check_timedelta_format
from common import get_seperated_timedelta


class Boss(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        import btdb
        self.db: btdb.BtDb = bot.db
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Boss Cog loaded.")

    @commands.command(name=u"보스등록")
    async def register_boss(self, ctx: commands.Context, *args) -> None:
        '''
        "보스등록" 명령어를 처리한다.
        :param ctx: context
        :param args: 보스명, 남은시간
        :return: 없음
        '''
        self.logger.debug(f"보스등록 {args}")
        await self.bot.wait_until_ready()
        # 명령어 형식이 맞는지 검사
        if len(args) != 2:
            await ctx.reply(f"사용법 : .보스등록 ***보스명 남은시간***")
            return
        self.logger.debug(f"명령어 갯수 통과")
        boss_alias = args[0]
        str_remain_time = args[1]
        # 남은시간이 형식에 맞게 되어 있는 지 검사
        if not check_timedelta_format(str_remain_time):
            await ctx.reply(f"남은시간은 'x일x시간x분x초' 형식이어야 합니다.")
            return
        d, h, m, s = get_seperated_timedelta(str_remain_time.strip())
        self.logger.debug(f"timestring 통과")
        # 보스명이 보스목록에 있는지 검사
        boss_name = self.db.get_boss_item(boss_alias, 'name')
        if boss_name is None:
            await ctx.reply(f"'{boss_alias}'은 등록된 보스명 혹은 보스별명이 아닙니다.")
            return
        self.logger.debug(f"보스명 검색 통과")
        # 길드등록되어 있는지 검사
        success, odin_server_name, odin_guild_ame = self.db.get_odin_guild_info(ctx.guild.id)
        if not success:
            await ctx.reply(f"먼저 길드등록을 해야 다른 명령어를 사용할 수 있습니다.")
            return
        self.logger.info(f"나머지 구현하세요")
        # 여기에 현재시각에 남은시간을 더해서 보스타임 알람을 설정해 놓는 코드를 진행해야 한다.
        await ctx.reply(f"{boss_name}, {d}, {h}, {m}, {s} ")


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