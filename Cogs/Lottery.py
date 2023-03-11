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

# cEMOJI_CHULCHECK_ON = '⭕'
# cEMOJI_CHULCHECK_OFF = '❌'


class Lottery(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot: BtBot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('bot.lottery')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Lottery Cog loaded.")

    @commands.command(name=cCMD_LOTTERY_CHULCHECK)
    async def boss_chulcheck(self, ctx: commands.Context, *args) -> None:
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
        self.logger.info(f"{cCMD_LOTTERY_CHULCHECK} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) != 1:  # 인자가 1개이어야 함
            await send_usage_embed(ctx, cCMD_LOTTERY_CHULCHECK)
            return

        # TODO : 이거 하다가 말았음.
        # 운영진인지 검사
        role = discord.utils.get(ctx.guild.roles, name="운영진")  # Get the role
        if role not in ctx.author.roles:  # Check if the author has the role
            await send_error_message(ctx, "운영진만?")
            return

        # 첫번째 인자가 보스명인지, 보스명이라면 고정타입 보스가 아닌지 검사
        # 보스명이면 쿨타임을 가져오고, 보스명이 아니면 쿨타임을 12시간으로...
        arg_boss_name = args[0]
        boss_key, boss = self.db.get_boss_item_by_name(arg_boss_name)
        if boss_key:
            # 인자로 넘어온 보스명이 별명일 수도 있으므로 정식명을 사용한다.
            boss_name = boss[kBOSS_NAME]
            # 보스 타입별로 쿨타임 설정
            if boss[kBOSS_TYPE] == cBOSS_TYPE_WEEKDAY_FIXED:
                cool_dt = datetime.timedelta(days=0, hours=23, minutes=59, seconds=59)
            elif boss[kBOSS_TYPE] == cBOSS_TYPE_INTERVAL:
                d, h, m, s = get_separated_timedelta_ddhhmm(boss[kBOSS_INTERVAL])
                cool_dt = datetime.timedelta(days=d, hours=h, minutes=m, seconds=0)
            else:  # boss[kBOSS_TYPE] == cBOSS_TYPE_DAILY_FIXED:
                cool_dt = datetime.timedelta(days=0, hours=23, minutes=59, seconds=59)
        else:
            boss_name = arg_boss_name
            cool_dt = datetime.timedelta(days=0, hours=11, minutes=59, seconds=59)

        # 공통으로 사용하는 값 준비
        now = datetime.datetime.utcnow()  # 시간은 항상 UTC 시간으로 저장하고 표시할 때만 한국시간으로...
        utc_now = now.astimezone(UTC)
        self.logger.debug(now.strftime(cTIME_FORMAT_WITH_TIMEZONE))
        self.logger.debug(utc_now.strftime(cTIME_FORMAT_WITH_TIMEZONE))

        guild_id = ctx.guild.id

        # 이건 pytz 기능 테스트용
        # utc_now = UTC.localize(now)
        # kst_now = KST.localize(now)
        # self.logger.debug(utc_now.strftime(cTIME_FORMAT_WITH_TIMEZONE))
        # self.logger.debug(kst_now.strftime(cTIME_FORMAT_WITH_TIMEZONE))

        # 두번째 인자가 없으면..
        # 출첵 정보를 찾는다. 없거나 주어진 쿨타임보다 오래된것이 마지막 것이면 새로 만든다.
        chulcheck_id, chulcheck_dict = self.db.check_and_create_chulcheck(guild_id, boss_name, utc_now, cool_dt)
        if chulcheck_id is None:
            await send_error_message(ctx, "무엇인가 잘못되었군요.")
            return

        # 생성한 출첵내의 생성시각은 UTC 이므로 출력용 KST 준비
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
                click_member_name = interaction.user.name  # 출석 버튼을 누른 자
                member_list = chulcheck_dict[kFLD_CC_MEMBERS]
                if click_member_name not in member_list:
                    added_chulcheck_id, added_member_list = db.add_member_to_chulcheck(chulcheck_id, click_member_name) # FIRESTORE에 실시간 저장
                    if added_chulcheck_id is None:
                        await send_error_message(ctx, u"출석자를 업데이트하지 못했습니다.")
                        return
                    member_list = added_member_list
                chulcheck_dict[kFLD_CC_MEMBERS] = member_list
                msg_add = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", f"{', '.join(member_list)}")
                await interaction.response.edit_message(content=msg_add)

            @discord.ui.button(label="빼줘", style=discord.ButtonStyle.red)
            async def chulcheck_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                click_member_name = interaction.user.name  # 빼줘 버튼을 누른 자
                member_list = chulcheck_dict[kFLD_CC_MEMBERS]
                if click_member_name in member_list:
                    removed_chulcheck_id, removed_member_list = db.remove_member_from_chulcheck(chulcheck_id, click_member_name)  # FIRESTORE에 실시간 저장
                if removed_chulcheck_id is None:
                    await send_error_message(ctx, u"출석자를 업데이트하지 못했습니다.")
                    return
                member_list = removed_member_list
                chulcheck_dict[kFLD_CC_MEMBERS] = member_list
                msg_remove = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", f"{', '.join(member_list)}")
                await interaction.response.edit_message(content=msg_remove)

        members = sorted(chulcheck_dict[kFLD_CC_MEMBERS])
        str_members = ", ".join(members)

        msg = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", str_members)

        view = Buttons(self.bot)
        await ctx.channel.send(msg, view=view)

        # msg_bot = await ctx.channel.send(msg)
        # await msg_bot.add_reaction(cEMOJI_CHULCHECK_ON)
        # await msg_bot.add_reaction(cEMOJI_CHULCHECK_OFF)

    @commands.command(name=cCMD_LOTTERY_CHULCHECK_HISTORY)
    async def boss_chulcheck_history(self, ctx: commands.Context, *args) -> None:
        """

        :param ctx:
        :param args:
        :return:
        """
        self.logger.info(f"{cCMD_LOTTERY_CHULCHECK_HISTORY} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) != 1 and len(args) != 2:  # 인자가 1개 혹은 2개이어야 함
            await send_usage_embed(ctx, cCMD_LOTTERY_CHULCHECK_HISTORY)
            return

        # TODO: 보스명이 아닌 출첵명 테스트 해야 함.

        # 첫번째 인자가 보스명인지, 보스명이라면 고정타입 보스가 아닌지 검사
        arg_boss_name = args[0]
        boss_key, boss = self.db.get_boss_item_by_name(arg_boss_name)
        if boss_key:
            # 인자로 넘어온 보스명이 별명이어도 정식 보스명으로 DB에 저장하므로 여기서도 전환해줘야 함.
            boss_name = boss[kBOSS_NAME]
        else:
            boss_name = arg_boss_name

        # 역순으로 몇 개까지의 출첵을 보여줄 지 숫자 저장
        if len(args) == 1:
            history_count = 5
        else:
            try:
                history_count = int(args[1])
            except ValueError as e:
                history_count = 5

        chulcheck_list = self.db.get_last_chulchecks(ctx.guild.id, boss_name, history_count)

        if len(chulcheck_list) == 0:
            await send_error_message(ctx, f"[{boss_name}] 보탐 출첵 이력이 없습니다.")
            return

        for chulcheck in chulcheck_list:
            chulcheck_id = chulcheck[0]
            chulcheck_dict = chulcheck[1]
            # 생성한 출첵내의 생성시각은 UTC 이므로 출력용 KST 준비
            utc_chulcheck_time = chulcheck_dict[kFLD_CC_DATETIME]
            kst_chulcheck_time = utc_chulcheck_time.astimezone(KST)
            str_dp_chulcheck_time = kst_chulcheck_time.strftime(cTIME_FORMAT_KOREAN_MMDD)
            member_list = chulcheck_dict[kFLD_CC_MEMBERS]
            msg = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", f"{', '.join(member_list)}")
            await ctx.channel.send(msg)



    # @commands.Cog.listener()
    # async def on_raw_reaction_add(self, payload):
    #
    #     channel = self.bot.get_channel(payload.channel_id)
    #     message = await channel.fetch_message(payload.message_id)
    #
    #     msg = discord.utils.remove_markdown(message.content)
    #     msg = msg.removeprefix(cPREFIX_ANSI).removeprefix(cPREFIX_CODEBLOCK_OK).removesuffix(cPOSTFIX_CODEBLOCK).strip()
    #
    #     if not (msg.startswith(cMSG_HEAD_CHULCHECK) or msg.startswith(cMSG_HEAD_LOTTERY)):
    #         return
    #
    #     lines = msg.split()
    #     check_type = lines[0]  # 출석체크,
    #
    #     if check_type == cMSG_HEAD_CHULCHECK:
    #         boss_name = lines[2]
    #         str_botam_day = lines[3]
    #         chulcheck_id = lines[5]
    #         guild_id = payload.guild_id
    #         event_type = payload.event_type
    #         user_info = await self.bot.fetch_user(payload.user_id)
    #
    #         for reaction in message.reactions:
    #             async for user in reaction.users():
    #                 pass

    # @commands.Cog.listener()
    # async def on_raw_reaction_remove(self, payload):
    #     self.logger.debug(payload)
    #     pass


async def setup(bot: BtBot) -> None:
    logging.getLogger('bot.lottery').info(f"setup Lottery Cog")
    await bot.add_cog(Lottery(bot))
