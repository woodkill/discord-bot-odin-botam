import logging
import random
import threading
import asyncio

from discord.ext import commands

import datetime
from pytz import timezone, utc

import BtBot
import BtDb

from common import *
from const_data import *

KST = timezone('Asia/Seoul')
UTC = utc

cEMOJI_CHULCHECK_ON = '✋'
cEMOJI_CHULCHECK_OFF = '❌'
cEMOJI_LOTTERY_SELECT = '📤'  # '🎁''🎬'
cEMOJI_LOTTERY_UP = '🔼'  # '🔺'
cEMOJI_LOTTERY_DOWN = '🔽'  # '🔻'


class Lottery(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot: BtBot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('bot.lottery')
        self.lock_dict = {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Lottery Cog loaded.")

    @commands.command(name=cCMD_LOTTERY_LOTTERY)
    async def lottery(self, ctx: commands.Context, *args) -> None:
        """

        :param ctx:
        :param args:
        :return:
        """
        self.logger.info(f"{cCMD_LOTTERY_LOTTERY} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) < 1:  # 인자가 최소 1개 이상
            await send_usage_embed(ctx, cCMD_LOTTERY_LOTTERY)
            return

        # 뽑기대상자 준비
        member_list = []
        for i in range(1, len(args)):
            member = args[i].rstrip(',')
            member_list.append(member)

        # 템명
        item_name = args[0].rstrip(',')
        # 템명 뒤에 숫자가 붙어 있으면 템이 여러개라는 의미
        r = extract_number_at_end_of_string(item_name)
        item_name = item_name if r is None else item_name[:-len(str(r))]
        target_count = 1 if r is None else r  # 몇명을 뽑는지

        class Buttons(discord.ui.View):
            def __init__(self, lottery_cog: Lottery, timeout=None):
                self.cog = lottery_cog
                self.bot = lottery_cog.bot
                self.logger = logging.getLogger('bot.lottery')
                super().__init__(timeout=timeout)

            def __del__(self):
                super().__del__()
                del self.cog.lock_dict[self.id]

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji=cEMOJI_CHULCHECK_ON)
            async def add(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                self.logger.info(f"buttons view id (add): {self.id}")
                self.logger.info(self.cog.lock_dict)
                with self.cog.lock_dict[self.id]:
                    if is_selected_lottery_message(interaction.message.content):
                        await interaction.response.defer()
                    else:
                        await asyncio.sleep(10)
                        l_item_name, l_target_count, l_member_list = parse_lottery_message(interaction.message.content)
                        nick = interaction.user.nick
                        name = interaction.user.name
                        click_member_name = nick if nick is not None else name  # 출석 버튼을 누른 자
                        self.logger.debug(f"{cEMOJI_CHULCHECK_ON} : {click_member_name}")
                        if click_member_name not in l_member_list:
                            l_member_list.append(click_member_name)
                        msg_add = to_before_lottery_code_block(l_item_name, l_target_count, l_member_list)
                        await interaction.response.edit_message(content=msg_add)

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji=cEMOJI_CHULCHECK_OFF)
            async def remove(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                self.logger.info(f"buttons view id (remove): {self.id}")
                self.logger.info(self.cog.lock_dict)
                with self.cog.lock_dict[self.id]:
                    if is_selected_lottery_message(interaction.message.content):
                        await interaction.response.defer()
                    else:
                        l_item_name, l_target_count, l_member_list = parse_lottery_message(interaction.message.content)
                        nick = interaction.user.nick
                        name = interaction.user.name
                        click_member_name = nick if nick is not None else name  # 빼줘 버튼을 누른 자
                        self.logger.debug(f"{cEMOJI_CHULCHECK_OFF} : {click_member_name}")
                        if click_member_name in l_member_list:
                            l_member_list.remove(click_member_name)
                        msg_remove = to_before_lottery_code_block(l_item_name, l_target_count, l_member_list)
                        await interaction.response.edit_message(content=msg_remove)

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji=cEMOJI_LOTTERY_SELECT)
            async def select(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                self.logger.info(f"buttons view id (selelct): {self.id}")
                self.logger.info(self.cog.lock_dict)
                with self.cog.lock_dict[self.id]:
                    if is_selected_lottery_message(interaction.message.content):
                        await interaction.response.defer()
                    else:
                        l_item_name, l_target_count, l_member_list = parse_lottery_message(interaction.message.content)
                        nick = interaction.user.nick
                        name = interaction.user.name
                        click_member_name = nick if nick is not None else name  # 뽑기 버튼을 누른 자
                        self.logger.debug(f"{cEMOJI_LOTTERY_SELECT} : {click_member_name}")
                        # if interaction.message.author.id == interaction.user.id:  # 뽑기를 올린 사람만 클릭 가능
                        if l_target_count <= len(l_member_list):
                            selected_member_list = random.sample(l_member_list, l_target_count)
                        else:
                            selected_member_list = random.choices(l_member_list, k=l_target_count)
                        msg_select = to_after_lottery_code_block(l_item_name, l_target_count, l_member_list, selected_member_list)
                        await interaction.response.edit_message(content=msg_select)

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji=cEMOJI_LOTTERY_UP)
            async def up(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                self.logger.info(f"buttons view id (up): {self.id}")
                self.logger.info(self.cog.lock_dict)
                with self.cog.lock_dict[self.id]:
                    if is_selected_lottery_message(interaction.message.content):
                        await interaction.response.defer()
                    else:
                        l_item_name, l_target_count, l_member_list = parse_lottery_message(interaction.message.content)
                        if l_target_count < len(l_member_list):
                            l_target_count += 1
                        msg_up = to_before_lottery_code_block(l_item_name, l_target_count, l_member_list)
                        await interaction.response.edit_message(content=msg_up)

            @discord.ui.button(label="", style=discord.ButtonStyle.gray, emoji=cEMOJI_LOTTERY_DOWN)
            async def down(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                self.logger.info(f"buttons view id (down): {self.id}")
                self.logger.info(self.cog.lock_dict)
                with self.cog.lock_dict[self.id]:
                    if is_selected_lottery_message(interaction.message.content):
                        await interaction.response.defer()
                    else:
                        l_item_name, l_target_count, l_member_list = parse_lottery_message(interaction.message.content)
                        if 1 < l_target_count:
                            l_target_count -= 1
                        msg_down = to_before_lottery_code_block(l_item_name, l_target_count, l_member_list)
                        await interaction.response.edit_message(content=msg_down)

        msg = to_before_lottery_code_block(item_name, target_count, member_list)
        view = Buttons(self)
        self.lock_dict[view.id] = threading.Lock()
        self.logger.info(self.lock_dict)
        await ctx.channel.send(msg, view=view)

    @commands.command(name=cCMD_LOTTERY_CHULCHECK)
    async def boss_chulcheck(self, ctx: commands.Context, *args) -> None:
        """
        보탐 출첵 기능
        :param ctx:
        :param args: args[0] : 보스(별)명 혹은 만든이름(예를 들면 무스펠릴레이)
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
            def __init__(self, bot: BtBot, timeout=None):
                self.bot = bot
                self.logger = logging.getLogger('bot.lottery')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="출석", style=discord.ButtonStyle.blurple)
            async def chulcheck_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                nick = interaction.user.nick
                name = interaction.user.name
                click_member_name = nick if nick is not None else name  # 출석 버튼을 누른 자
                self.logger.debug(f"출석 : {click_member_name}")
                member_list = chulcheck_dict[kFLD_CC_MEMBERS]
                if click_member_name not in member_list:
                    added_chulcheck_id, added_member_list = db.add_member_to_chulcheck(chulcheck_id, click_member_name) # FIRESTORE에 실시간 저장
                    if added_chulcheck_id is None:
                        await send_error_message(ctx, u"출석자를 업데이트하지 못했습니다.")
                        return
                    member_list = added_member_list
                chulcheck_dict[kFLD_CC_MEMBERS] = member_list
                msg_add = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", member_list)
                await interaction.response.edit_message(content=msg_add)

            @discord.ui.button(label="빼줘", style=discord.ButtonStyle.red)
            async def chulcheck_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                nick = interaction.user.nick
                name = interaction.user.name
                click_member_name = nick if nick is not None else name  # 빼줘 버튼을 누른 자
                self.logger.debug(f"빼줘 : {click_member_name}")
                member_list = chulcheck_dict[kFLD_CC_MEMBERS]
                if click_member_name in member_list:
                    removed_chulcheck_id, removed_member_list = db.remove_member_from_chulcheck(chulcheck_id, click_member_name)  # FIRESTORE에 실시간 저장
                if removed_chulcheck_id is None:
                    await send_error_message(ctx, u"출석자를 업데이트하지 못했습니다.")
                    return
                member_list = removed_member_list
                chulcheck_dict[kFLD_CC_MEMBERS] = member_list
                msg_remove = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", member_list)
                await interaction.response.edit_message(content=msg_remove)

        members = sorted(chulcheck_dict[kFLD_CC_MEMBERS])

        msg = to_chulcheck_code_block(f"{boss_name} {str_dp_chulcheck_time} - {chulcheck_id}", members)

        view = Buttons(self.bot)
        await ctx.channel.send(msg, view=view)

        # 이것은 버튼 대신 이모지로 구현해 본 것
        # msg_bot = await ctx.channel.send(msg)
        # await msg_bot.add_reaction(cEMOJI_CHULCHECK_ON)
        # await msg_bot.add_reaction(cEMOJI_CHULCHECK_OFF)

    @commands.command(name=cCMD_LOTTERY_CHULCHECK_HISTORY)
    async def boss_chulcheck_history(self, ctx: commands.Context, *args) -> None:
        """
        출첵 목록을 출력한다.
        :param ctx:
        :param args:
            args[0] : 보스(별)명 혹은 붙인이름(무스펠릴레이) 혹은 '*' - 모두 보기
            args[1] : 최근 몇개의 출첵을 보여줄 것인지
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

        if boss_name == "*":
            chulcheck_list = self.db.get_all_last_chulchecks(ctx.guild.id, history_count)
        else:
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
            msg = to_chulcheck_code_block(f"{chulcheck_dict[kFLD_CC_BOSSNAME]} {str_dp_chulcheck_time} - {chulcheck_id}", member_list)
            await ctx.channel.send(msg)

    @commands.command(name=cCMD_LOTTERY_CHULCHECK_DELETE)
    async def boss_chulcheck_delete(self, ctx: commands.Context, *args) -> None:
        """
        지정된 출첵ID에 해당하는 출첵을 삭제한다.
        :param ctx:
        :param args:
            args[0] : 출첵 ID
        :return:
        """
        self.logger.info(f"{cCMD_LOTTERY_CHULCHECK_DELETE} {args} by {ctx.message.author}")

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
            await send_usage_embed(ctx, cCMD_LOTTERY_CHULCHECK_DELETE)
            return

        # 운영진인지 검사
        role = discord.utils.get(ctx.guild.roles, name="운영진")  # Get the role
        if role not in ctx.author.roles:  # Check if the author has the role
            await send_error_message(ctx, "운영진만 사용할 수 있는 명령어입니다.")
            return

        # 인자는 출첵ID -> 즉, document id
        if not self.db.delete_chulcheck(args[0]):
            await send_error_message(ctx, "축첵ID를 잘못된 것 같습니다. 출첵정보에서 복붙하세요.")
            return

        await send_ok_message(ctx, f"출첵 {args[0]} 삭제하였습니다.")

    @commands.command(name=cCMD_LOTTERY_CHULCHECK_LOTTERY)
    async def boss_chulcheck_lottery(self, ctx: commands.Context, *args) -> None:
        """

        :param ctx:
        :param args:
        :return:
        """
        self.logger.info(f"{cCMD_LOTTERY_CHULCHECK_LOTTERY} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 첫번째 인자 출첵명, 두번째 인자부터 뽑기할 템명. 없으면 그냥 당첨 표시만...
        if len(args) < 1:  # 인자가 최소 1개이어야 함
            await send_usage_embed(ctx, cCMD_LOTTERY_CHULCHECK_LOTTERY)
            return

        boss_name = args[0]  # 변수명은 boss_name이지만 출첵명이다.
        item_list = list(args[1:])

        # 첫번째 인자는 존재하는 출첵명이어야 한다.
        chulcheck_id, chulcheck_dict = self.db.get_lastone_chulcheck(ctx.guild.id, boss_name)
        if chulcheck_id is None:
            await send_error_message(ctx, f"'{boss_name}'으로 등록된 최근 출첵이 존재하지 않습니다.")
            return

        # 생성한 출첵내의 생성시각은 UTC 이므로 출력용 KST 준비
        utc_chulcheck_time = chulcheck_dict[kFLD_CC_DATETIME]
        kst_chulcheck_time = utc_chulcheck_time.astimezone(KST)
        str_dp_chulcheck_time = kst_chulcheck_time.strftime(cTIME_FORMAT_KOREAN_MMDD)
        member_list = chulcheck_dict[kFLD_CC_MEMBERS]
        msg = to_chulcheck_code_block(f"{chulcheck_dict[kFLD_CC_BOSSNAME]} {str_dp_chulcheck_time} - {chulcheck_id}", member_list)
        await ctx.channel.send(msg)

        for item in item_list:
            # 템명 뒤에 숫자가 붙어 있으면 템이 여러개라는 의미
            r = extract_number_at_end_of_string(item)
            n = 1 if r is None else r
            member_count = len(member_list)
            item_name = item if r is None else item[:-len(str(r))]
            if n <= member_count:
                selected_member = random.sample(member_list, n)
            else:
                selected_member = random.choices(member_list, k=n)
            await send_ok_message(ctx, f"{item_name} : {', '.join(selected_member)}")


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
