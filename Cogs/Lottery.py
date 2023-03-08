import logging
from discord.ext import commands

import datetime
from pytz import timezone, utc

import BtBot
import BtDb

from common import *
from const_data import *

KST = timezone('Asia/Seoul')
UTC = utc


class Lottery(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot: BtBot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('bot.lottery')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Lottery Cog loaded.")

    @commands.command(name=cCMD_LOTTERY_CULCHECK)
    async def alram_timers(self, ctx: commands.Context, *args) -> None:
        """
        보탐 출첵 기능
        :param ctx:
        :param args:
            첫번째 인자는 보스(별)명, 두번째 인자는 없거나 날짜.
            두번째 인자가 없는 경우 : 보스의 24시간 이내 출첵이 있으면 그걸 다시 꺼내쓴다. 즉, 지각생용
                                     없으면 오늘 날짜로 출첵을 만든다.
            두번째 인자가 있는 경우 : 그 날짜의 출첵을 출력한다. 이 경우, 출첵은 할 수 없다.
        :return:
        """
        self.logger.info(f"{cCMD_LOTTERY_CULCHECK} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) > 2:  # 인자가 1개 혹은 2개이어야 함
            await send_usage_embed(ctx, cCMD_LOTTERY_CULCHECK)
            return

        # 첫번째 인자가 보스명인지, 보스명이라면 고정타입 보스가 아닌지 검사
        arg_boss_name = args[0]
        boss_key, boss = self.db.get_boss_item_by_name(args[0])
        if boss_key is None:
            await send_error_message(ctx, f"{arg_boss_name} : 존재하지 않는 보스명입니다.")
            return

        # 보스 타입별로 쿨타임 설정

        if boss[kBOSS_TYPE] == cBOSS_TYPE_WEEKDAY_FIXED:
            cool_dt = datetime.timedelta(days=0, hours=48, minutes=0, seconds=0)
        elif boss[kBOSS_TYPE] == cBOSS_TYPE_INTERVAL:
            d, h, m, s = get_separated_timedelta_ddhhmm(boss[kBOSS_INTERVAL])
            cool_dt = datetime.timedelta(days=d, hours=h, minutes=m, seconds=0)
        else:  # boss[kBOSS_TYPE] == cBOSS_TYPE_DAILY_FIXED:
            cool_dt = datetime.timedelta(days=0, hours=24, minutes=0, seconds=0)

        # 인자로 넘어온 보스명이 별명일 수도 있으므로 정식명을 사용한다.
        boss_name = boss[kBOSS_NAME]

        # 두번째 인자가 있으면
        if len(args) == 2:

            # #  형식 체크
            # y, m, d = get_yearmonthday_korean(args[1])
            # if d == 0:  # 형식이 안맞거나 최소한 날짜를 잘못 입력한 것
            #     await send_error_message(ctx, u"몇년몇월몇일 혹은 몇월몇일 혹은 몇일 이렇게 입력하세요.")
            #     return
            #
            # try:
            #     str_key_date = datetime.datetime.strptime("{y}-{m}-{d}", "%Y-%m-%d").date().strftime("%Y-%m-%d")
            # except ValueError:
            #     await send_error_message(ctx, u"날짜의 숫자가 잘못되었습니다.")
            #     return
            #
            # # 키를 만들어서 그 날짜의 출석자 명단을 가져온다. 키는 "날짜 보스명"
            # dic_key = f"{str_key_date} {boss_name}"
            return

        # 두번째 인자가 없으면..
        now = datetime.datetime.utcnow()  # 시간은 항상 UTC 시간으로 저장하고 표시할 때만 한국시간으로...
        utc_now = now.astimezone(UTC)
        self.logger.debug(now.strftime(cTIME_FORMAT_WITH_TIMEZONE))
        self.logger.debug(utc_now.strftime(cTIME_FORMAT_WITH_TIMEZONE))

        # 이건 pytz 기능 테스트용
        # utc_now = UTC.localize(now)
        # kst_now = KST.localize(now)
        # self.logger.debug(utc_now.strftime(cTIME_FORMAT_WITH_TIMEZONE))
        # self.logger.debug(kst_now.strftime(cTIME_FORMAT_WITH_TIMEZONE))

        guild_id = ctx.guild.id

        # 먼저 가장 최근의 해당 보스명 출첵이 있으면 받아오고 없으면 만든다.
        # 있더라도 해당 보스의 쿨타임보다 크면 새로 만든다.
        doc_id = None
        doc_id, chulcheck_dict = self.db.get_lastone_chulcheck(guild_id, boss_name)
        if chulcheck_dict is None:
            doc_id, chulcheck_dict = self.db.add_chulcheck(guild_id, utc_now, boss_name, [])
            self.logger.debug(chulcheck_dict)
        else:
            td = utc_now - chulcheck_dict[kFLD_CC_DATETIME]
            if td.total_seconds() > cool_dt.total_seconds():
                doc_id, chulcheck_dict = self.db.add_chulcheck(guild_id, utc_now, boss_name, [])
                self.logger.debug(chulcheck_dict)

        utc_chulcheck_time = chulcheck_dict[kFLD_CC_DATETIME]
        kst_chulcheck_time = utc_chulcheck_time.astimezone(KST)
        str_dp_chulcheck_time = kst_chulcheck_time.strftime(cTIME_FORMAT_KOREAN_MMDD)

        db = self.db

        class Buttons(discord.ui.View):
            def __init__(self, bot: BtBot, timeout=180):
                self.bot = bot
                self.logger = logging.getLogger('bot.lottery')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="출석", style=discord.ButtonStyle.blurple)
            async def chulcheck_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                guild_member_name = interaction.user.name
                # firestore에 넣는 루틴
                returned_doc_id, added_member_list = db.add_member_to_chulcheck(doc_id, guild_member_name)
                if returned_doc_id is None:
                    await send_error_message(ctx, u"출석자를 업데이트하지 못했습니다.")
                    return
                message = f"```ansi\n"\
                  f"\033[34;1m"\
                  f"{boss_name}  {str_dp_chulcheck_time}\n"\
                  f"\033[0m\n"\
                  f"{added_member_list}\n"\
                  f"```"
                await interaction.response.edit_message(content=message)

            @discord.ui.button(label="빼줘", style=discord.ButtonStyle.red)
            async def chulcheck_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):

                pass

        view = Buttons(self.bot)
        members = set(chulcheck_dict[kFLD_CC_MEMBERS])
        str_members = ", ".join(members)
        message = f"```ansi\n"\
                  f"\033[34;1m"\
                  f"{boss_name}  {str_dp_chulcheck_time}\n"\
                  f"\033[0m\n"\
                  f"{str_members}\n"\
                  f"```"
        await ctx.channel.send(message, view=view)


async def setup(bot: BtBot) -> None:
    logging.getLogger('bot.lottery').info(f"setup Lottery Cog")
    await bot.add_cog(Lottery(bot))
