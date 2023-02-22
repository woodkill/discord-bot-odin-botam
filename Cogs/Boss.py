import logging
import discord
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object
import btdb
from const_key import *
from const_data import *
from common import *

class Boss(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db: btdb.BtDb = bot.db
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Boss Cog loaded.")

    @commands.command(name=cBOSS_LIST)
    async def list_boss(self, ctx: commands.Context) -> None:
        '''
        등록되어 있는 보스목록을 보여준다.
        TODO: 현재는 마스터 보스리스트에서 보여준다. 디버깅용. 실제로는 보스알림등록한 보스를 보여줘야 함. 아니면 그쪽은 "보탐어쩌구.."로 명령을 만든다.
        :param ctx: context
        :return: None
        '''
        self.logger.info(f"{cBOSS_LIST}")
        boss_list = self.db.get_boss_list()
        if boss_list is None:
            await ctx.reply(f"보스정보가 없습니다. 관리자에게 문의하세요.")
        # sl = sorted(boss_list, key=lambda x: (x[kCHAP_NAME], x[kBOSS_LEVEL], x[kBOSS_ORDER]))
        # self.logger.info(sl)
        msg = ""
        for boss in boss_list:
            str_boss_alias = ",".join(boss[kBOSS_ALIAS])
            msg += f"{boss[kCHAP_NAME]}/{boss[kBOSS_LEVEL]}/{boss[kBOSS_NAME]} : {str_boss_alias}\n"
        await ctx.reply(msg)

    @commands.command(name=cBOSS_INFO)
    async def info_boss(self, ctx: commands.Context, *args) -> None:
        '''
        보스정보를 보여준다.
        :param ctx: context
        :param args: args[0] : 보스명
        :return: None
        '''
        self.logger.info(f"{cBOSS_INFO} {args}")
        # 명령어 형식이 맞는지 검사
        if len(args) != 1:
            await ctx.reply(f"사용법 : .{cBOSS_INFO} ***보스명***")
            return
        self.logger.debug(f"명령어 갯수 통과")
        odin_boss_name = args[0]
        boss_dic = self.db.get_boss_item_by_name(odin_boss_name)

        boss_type = boss_dic[kBOSS_TYPE]
        boss_apperance = ""
        if boss_type == cBOSS_TYPE_INTERVAL:
            boss_interval = boss_dic[kBOSS_INTERVAL]
            d, h, m, s = get_seperated_timedlta_ddhhmm(boss_interval)
            str_interval = ""
            if d > 0:
                str_interval += f"{d}일"
            if h > 0:
                str_interval += f"{h}시간"
            if m > 0:
                str_interval += f"{m}분"
            if s > 0:
                str_interval += f"{s}초"
            boss_apperance = f"컷 후 {str_interval} 뒤에 젠"
        elif boss_type == cBOSS_TYPE_DAILY_FIXED:
            boss_fiexed_time_list = boss_dic[kBOSS_FIXED_TIME]
            str_times = ', '.join(boss_fiexed_time_list)
            boss_apperance = f"매일 {str_times} 젠"
        elif boss_type == cBOSS_TYPE_WEEKDAY_FIXED:
            boss_weektime_list = boss_dic[kBOSS_WEEKDAY_INFO]
            str_weektime_list = []
            for boss_weektime_info in boss_weektime_list:
                weekday_index = boss_weektime_info[kBOSS_WEEKDAY]
                str_weekday = cWEEKDAYS[weekday_index]
                str_appearance_time = boss_weektime_info[kBOSS_APPEARANCE_TIME]
                str_weektime_list.append(f"{str_weekday} {str_appearance_time}")
            str_weektimes = ', '.join(str_weektime_list)
            boss_apperance = f"매주 {str_weektimes} 젠"

        str_boss_type = {
            cBOSS_TYPE_INTERVAL : f"인터벌",
            cBOSS_TYPE_WEEKDAY_FIXED : f"특정요일, 특정시간",
            cBOSS_TYPE_DAILY_FIXED : f"매일 같은 시간"

        }.get(boss_type, f"알 수 없는 보스타입")
        msg = f"보스명 : {boss_dic[kBOSS_NAME]}\n" \
              f"지역 : {boss_dic[kCHAP_NAME]}\n" \
              f"종류 : {boss_dic[kBOSS_LEVEL]}\n" \
              f"별명 : {', '.join(boss_dic[kBOSS_ALIAS])}\n" \
              f"타입 : {str_boss_type}\n" \
              f"출현 : {boss_apperance}"

        await ctx.reply(msg)

    @commands.command(name=cBOSS_REGISTER_ALIAS)
    async def register_alias_boss(self, ctx: commands.Context, *args):
        self.logger.info(f"{cBOSS_REGISTER_ALIAS} {args}")
        await ctx.reply(f"{cBOSS_REGISTER_ALIAS} 등록 구현중...")

    # @commands.command(name=u"보스등록")
    # async def register_boss(self, ctx: commands.Context, *args) -> None:
    #     '''
    #     "보스등록" 명령어를 처리한다.
    #     :param ctx: context
    #     :param args: 보스명, 남은시간
    #     :return: 없음
    #     '''
    #     self.logger.debug(f"보스등록 {args}")
    #     # 명령어 형식이 맞는지 검사
    #     if len(args) != 2:
    #         await ctx.reply(f"사용법 : .보스등록 ***보스명 남은시간***")
    #         return
    #     self.logger.debug(f"명령어 갯수 통과")
    #     boss_alias = args[0]
    #     str_remain_time = args[1]
    #     # 남은시간이 형식에 맞게 되어 있는 지 검사
    #     if not check_timedelta_format(str_remain_time):
    #         await ctx.reply(f"남은시간은 'x일x시간x분x초' 형식이어야 합니다.")
    #         return
    #     d, h, m, s = get_seperated_timedelta_korean(str_remain_time.strip())
    #     self.logger.debug(f"timestring 통과")
    #     # 보스명이 보스목록에 있는지 검사
    #     boss_name = self.db.get_boss_item(boss_alias, 'name')
    #     if boss_name is None:
    #         await ctx.reply(f"'{boss_alias}'은 등록된 보스명 혹은 보스별명이 아닙니다.")
    #         return
    #     self.logger.debug(f"보스명 검색 통과")
    #     # 길드등록되어 있는지 검사
    #     success, odin_server_name, odin_guild_ame = self.db.get_odin_guild_info(ctx.guild.id)
    #     if not success:
    #         await ctx.reply(f"먼저 길드등록을 해야 다른 명령어를 사용할 수 있습니다.")
    #         return
    #     self.logger.info(f"나머지 구현하세요")
    #     # 여기에 현재시각에 남은시간을 더해서 보스타임 알람을 설정해 놓는 코드를 진행해야 한다.
    #     await ctx.reply(f"{boss_name}, {d}, {h}, {m}, {s} ")


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup Boss Cog")
    await bot.add_cog(Boss(bot))