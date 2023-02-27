import asyncio
import json
import datetime
from discord.ext import tasks
# from discord import Interaction
# from discord import Object
from common import *
from const_data import *
from const_key import *
import BtBot
import BtDb

cCHECK_ALARM_INTERVAL_SECONDS = 5

cTIME_FORMAT_FIXED_TYPE = "%H:%M"


class Alarm(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot: BtBot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('cog')
        # async task
        self.lock = asyncio.Lock()
        self.check_alarms.start()
        # # 알람목록
        # self.all_alarm_dic = {}
        # for test
        self.count = 0

    def cog_unload(self) -> None:
        self.check_alarms.cancel()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Alarm Cog loaded.")

    @commands.command(name=cCMD_ALARM_LIST)
    async def alarm_list(self, ctx: commands.Context) -> None:
        """

        :param ctx:
        :return:
        """
        logging.info(f"{cCMD_ALARM_LIST}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 중첩된 dict를 쓰기 좋게 꺼내 놓는다.
        guild_dic = self.bot.odin_guilds_dic[ctx.guild.id]
        try:
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        except KeyError:
            guild_dic[kFLD_ALARMS] = {}
            await send_error_message(ctx, f"등록된 보스 알람이 없습니다.")
            return

        embed_list = []

        # 1. 월보 알람 검사
        try:
            guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED] = {}
            guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]

        if len(guild_daily_fixed_alarm_dic) > 0:

            daily_fixed_embed = discord.Embed(
                title=cCMD_ALARM_DAILY_FIXED_ONOFF,
                description=u"매일",
                color=discord.Color.blue())

            for str_time, boss_list in sorted(guild_daily_fixed_alarm_dic.items()):
                daily_fixed_embed.add_field(name=str_time, value=', '.join(boss_list), inline=False)

            embed_list.append(daily_fixed_embed)

        # 2. 성채 알람 검사
        try:
            guild_weekday_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED] = {}
            guild_weekday_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]

        if len(guild_weekday_fixed_alarm_dic) > 0:

            weekday_fixed_embed = discord.Embed(
                title=cCMD_ALARM_WEEKDAY_FIXED_ONOFF,
                description=u"",
                color=discord.Color.yellow())

            for str_weekday_no, time_alarm_dic in guild_weekday_fixed_alarm_dic.items():
                str_weekday = cWEEKDAYS[int(str_weekday_no)]
                message = ""
                for t, b in time_alarm_dic.items():
                    message += f"{t} : {', '.join(b)}\n"
                    weekday_fixed_embed.add_field(name=str_weekday, value=message, inline=False)

            embed_list.append(weekday_fixed_embed)

        # 3.

        await ctx.send(embeds=embed_list)

    @commands.command(name=cCMD_ALARM_REGISTER)
    async def register_boss_alarm(self, ctx: commands.Context) -> None:
        """

        :param ctx:
        :return:
        """
        pass

    @commands.command(name=cCMD_ALARM_DAILY_FIXED_ONOFF)
    async def onoff_daily_fixed_alarm(self, ctx: commands.Context) -> None:
        """
        월보 온/오프 기능
        :param ctx: Context
        :return:
        """
        logging.info(f"{cCMD_ALARM_DAILY_FIXED_ONOFF}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 중첩된 dict를 쓰기 좋게 꺼내 놓는다.
        guild_dic = self.bot.odin_guilds_dic[ctx.guild.id]
        try:
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        except KeyError:
            guild_dic[kFLD_ALARMS] = {}
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        try:
            guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED] = {}
            guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]

        # self.logger.info(guild_dic)

        # guild_daily_fixed_alarm_dic에 데이타가 있으면 월드보탐 ON 상태 없으면 OFF 상태
        is_on = False
        view_message = f"현재 {cCMD_ALARM_DAILY_FIXED_ONOFF} 알람은 꺼진 상태입니다."
        if len(guild_daily_fixed_alarm_dic) > 0:
            is_on = True
            view_message = f"현재 {cCMD_ALARM_DAILY_FIXED_ONOFF} 알람은 켜진 상태입니다.\n"
            for time, boss_list in guild_daily_fixed_alarm_dic.items():
                view_message += f"{time} : {', '.join(boss_list)}\n"
            view_message = view_message[:-1]

        class Buttons(discord.ui.View):
            def __init__(self, bot: BtBot, timeout=180):
                self.bot = bot
                self.logger = logging.getLogger('cog')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="켜기", style=discord.ButtonStyle.blurple)
            async def daily_fixed_alarm_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                """
                월드보탐 명령어의 reaction으로 나오는 켜기 버튼을 눌렀을 때 실행되는 함수이다.
                :param interaction:
                :param button:
                :return:
                """

                # self.logger.info(f"{self.bot.odin_guilds_dic}")

                # 마스터정보에서 월드보스 정보를 가지고 알람 dict 만들어 줌
                # 시각을 key로 하고 값을 해당시간에 뜨는 보스명 list로 하는 dict. 하루에 여러번 고정시각이 있을 수 있음.
                alarm_dic = self.bot.db.get_daily_fiexed_alarm_info_from_master()
                # self.logger.info(f"{json.dumps( alarm_dic, indent=2, ensure_ascii=False)}")
                if len(alarm_dic) == 0:
                    await response_error_message(interaction.response, f"월드보스 정보가 없습니다.")
                    return

                # 모든 길드의 알람 dict안의 현재 길드의 월보 dict에 넣어준다.
                self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARMS][cBOSS_TYPE_DAILY_FIXED] = alarm_dic

                # 길드전체 알람 dict에 제대로 들어가 있는지 검사
                # self.logger.info(f"{self.bot.odin_guilds_dic}")
                self.logger.info(f"{json.dumps(self.bot.odin_guilds_dic, indent=4, ensure_ascii=False)}")

                # 서버 DB에 길드의 알람설정 상태 덮어쓰기
                self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

                edited_message = f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 알람을 켰습니다.\n"
                for t, b in self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARMS][cBOSS_TYPE_DAILY_FIXED].items():
                    edited_message += f"{t} : {', '.join(b)}\n"
                edited_message = edited_message[:-1]

                await interaction.response.edit_message(content=edited_message, view=None)

            @discord.ui.button(label="끄기", style=discord.ButtonStyle.red)
            async def weekday_fixed_alarm_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                """
                월드보탐 명령어의 reaction으로 나오는 끄기 버튼을 눌렀을 때 실행되는 함수이다.
                Alarm Cog 객체 안의 all_alarm_dic dict에 이 길드의 월드보스 alarm_dic을 지운다.
                :param interaction:
                :param button:
                :return:
                """
                # self.logger.info(f"{self.bot.odin_guilds_dic}")

                # 길드알람 dict에 cBOSS_TYPE_DAILY_FIXED를 키로 하는 dict를 지운다.
                # 이 dict이 비어 있다는 것이 고정보스 알람을 껐다는 뜻
                guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED] = {}

                # 길드전체 알람 dict에 제대로 들어가 있는지?
                # self.logger.info(f"{self.bot.odin_guilds_dic}")
                self.logger.info(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

                # 서버 DB에 길드의 알람설정 상태 덮어쓰기
                self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

                await interaction.response.edit_message(content=f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 알람을 껐습니다.", view=None)

        view = Buttons(self.bot)
        await ctx.channel.send(view_message, view=view)

    @commands.command(name=cCMD_ALARM_WEEKDAY_FIXED_ONOFF)
    async def onoff_weekday_fixed_alarm(self, ctx: commands.Context) -> None:
        """
        성채 온/오프 기능
        :param ctx: Context
        :return:
        """
        logging.info(f"{cCMD_ALARM_WEEKDAY_FIXED_ONOFF}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 중첩된 dict를 쓰기 좋게 꺼내 놓는다.
        guild_dic = self.bot.odin_guilds_dic[ctx.guild.id]
        try:
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        except KeyError:
            guild_dic[kFLD_ALARMS] = {}
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        try:
            guild_weekly_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED] = {}
            guild_weekly_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]

        # self.logger.info(guild_dic)

        # guild_weekly_fixed_alarm_dic 데이타가 있으면 월드보탐 ON 상태 없으면 OFF 상태
        is_on = False
        view_message = f"현재 {cCMD_ALARM_WEEKDAY_FIXED_ONOFF} 알람은 꺼진 상태입니다."
        if len(guild_weekly_fixed_alarm_dic) > 0:
            is_on = True
            view_message = f"현재 {cCMD_ALARM_WEEKDAY_FIXED_ONOFF} 알람은 켜진 상태입니다.\n"
            # for time, boss_list in guild_weekly_fixed_alarm_dic.items():
            #     view_message += f"{time} : {', '.join(boss_list)}\n"
            view_message = view_message[:-1]

        class Buttons(discord.ui.View):
            def __init__(self, bot: BtBot, timeout=180):
                self.bot = bot
                self.logger = logging.getLogger('cog')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="켜기", style=discord.ButtonStyle.blurple)
            async def weekday_fixed_alarm_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                """
                성채 명령어의 reaction으로 나오는 켜기 버튼을 눌렀을 때 실행되는 함수이다.
                :param interaction:
                :param button:
                :return:
                """

                # self.logger.info(f"{self.bot.odin_guilds_dic}")

                # 마스터정보에서 성채보스 정보를 가지고 알람 dict 만들어줌
                alarm_dic = self.bot.db.get_weekday_fiexed_alarm_info_from_master()
                if len(alarm_dic) == 0:
                    await response_error_message(interaction.response, f"성채보스 정보가 없습니다.")
                    return

                # 요일번호 문자열을 Key 하고 값을 {시간문자열:[보스명리스트]}로 하는 dict을 만든다.
                self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARMS][cBOSS_TYPE_WEEKDAY_FIXED] = alarm_dic
                # for weekday, time_alarm_dic in alarm_dic.items():
                #     guild_weekly_fixed_alarm_dic[weekday] = time_alarm_dic

                # 길드전체 알람 dict에 제대로 들어가 있는지 검사
                # self.logger.info(f"{self.bot.odin_guilds_dic}")
                self.logger.info(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

                # 서버 DB에 길드의 알람설정 상태 덮어쓰기
                self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

                edited_message = f"{cCMD_ALARM_WEEKDAY_FIXED_ONOFF} 알람을 켰습니다.\n"
                for str_weekday_no, time_alarm_dic \
                        in self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARMS][cBOSS_TYPE_WEEKDAY_FIXED].items():
                    str_weekday = cWEEKDAYS[int(str_weekday_no)]
                    edited_message += f"{str_weekday}\n"
                    for t, b in time_alarm_dic.items():
                        edited_message += f"{t} : {', '.join(b)}\n"
                edited_message = edited_message[:-1]

                await interaction.response.edit_message(content=edited_message, view=None)

            @discord.ui.button(label="끄기", style=discord.ButtonStyle.red)
            async def weekday_fixed_alarm_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                """
                성채 명령어의 reaction으로 나오는 끄기 버튼을 눌렀을 때 실행되는 함수이다.
                Alarm Cog 객체 안의 all_alarm_dic dict에 이 길드의 성채보스 alarm_dic을 지운다.
                :param interaction:
                :param button:
                :return:
                """
                # self.logger.info(f"{self.bot.odin_guilds_dic}")

                # 길드알람 dict에 cBOSS_TYPE_WEEKDAY_FIXED를 키로 하는 dict를 지운다.
                # 이 dict이 비어 있다는 것이 성채보스 알람을 껐다는 뜻
                guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED] = {}

                # 길드전체 알람 dict에 제대로 들어가 있는지?
                # self.logger.info(f"{self.bot.odin_guilds_dic}")
                self.logger.info(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

                # 서버 DB에 길드의 알람설정 상태 덮어쓰기
                self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

                await interaction.response.edit_message(
                    content=f"{cCMD_ALARM_WEEKDAY_FIXED_ONOFF} 알람을 껐습니다.",
                    view=None)

        view = Buttons(self.bot)
        await ctx.channel.send(view_message, view=view)

    async def do_check_alarm(self):
        """

        :return:
        """
        # self.logger.debug(self.bot.odin_guilds_dic)

        # 현재 시각, 요일, 요일번호 등
        now = datetime.datetime.now()
        now_date = now.date()
        now_weekday_no = now.weekday()
        # str_now_weekday_no = str(now_weekday_no)

        # 각 길드에 대해서 돌아가면서...
        for guild_id, guild_dic in self.bot.odin_guilds_dic.items():

            # 이 길드의 알람을 보낼 채널
            channel_id = guild_dic[kFLD_CHANNEL_ID]
            channel = self.bot.get_channel(channel_id)

            # 전체 알람 목록
            try:
                guild_alarm_dic = guild_dic[kFLD_ALARMS]
            except KeyError:
                guild_alarm_dic = {}

            # 1. 월보 알람
            try:
                guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]
            except KeyError:
                guild_daily_fixed_alarm_dic = {}

            for str_alarm_time, boss_list in guild_daily_fixed_alarm_dic.items():

                # 시각:분 형태로 저장되어 있음. 오늘 보스타임으로 변환
                alarm_time = datetime.datetime.strptime(str_alarm_time, cTIME_FORMAT_FIXED_TYPE).time()
                alarm_datetime = datetime.datetime.combine(now_date, alarm_time)
                # self.logger.info(f"alarm_datetime: {alarm_datetime}")

                # 현재 시각과 보스가 뜨는 시각의 차이
                time_diff_seconds = (alarm_datetime - now).total_seconds()
                # self.logger.info(f"{time_diff_seconds}")

                if time_diff_seconds < 0:  # 이 얘기는 이미 보스가 뜨는 시간이 지나갔다는 얘기
                    # self.logger.info(f"보스가 이미 잡혔습니다.")
                    pass

                elif time_diff_seconds <= cCHECK_ALARM_INTERVAL_SECONDS:
                    # str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 고정타임 보스목록
                    self.logger.info(f"{now} : 보스알람을 울려야 합니다.")
                    await channel.send(f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 출현 시간입니다.", tts=True)

                else:  # time_diff_seconds > cCHECK_ALARM_INTERVAL_SECONDS
                    # str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 고정타임 보스목록
                    rh = round(time_diff_seconds // 3600)
                    rm = round((time_diff_seconds // 60) % 60)
                    rs = round(time_diff_seconds % 60)
                    # self.logger.info(f"보탐시간과의 차이 : {rh:02}:{rm:02}:{rs:02}")
                    self.logger.info(f"{rh:02}:{rm:02}:{rs:02} - {cCMD_ALARM_DAILY_FIXED_ONOFF}")  # {str_alarm_time}

            # 2. 성채 알람
            try:
                guild_weekday_fixed_alram_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]
            except KeyError:
                guild_weekday_fixed_alram_dic = {}

            for str_weekday_no, weekday_alarm_dic in guild_weekday_fixed_alram_dic.items():

                # 오늘이 성채 날짜가 아니면 통과
                weekday_no = int(str_weekday_no)
                if now_weekday_no != weekday_no:
                    self.logger.info(f"오늘은 {cWEEKDAYS[weekday_no]}이 아님.")
                    continue

                for str_alarm_time, boss_list in weekday_alarm_dic.items():

                    # 시각:분 형태로 저장되어 있음. 오늘 보스타임으로 변환
                    alarm_time = datetime.datetime.strptime(str_alarm_time, cTIME_FORMAT_FIXED_TYPE).time()
                    alarm_datetime = datetime.datetime.combine(now_date, alarm_time)
                    # self.logger.info(f"alarm_datetime: {alarm_datetime}")

                    # 현재 시각과 보스가 뜨는 시각의 차이
                    time_diff_seconds = (alarm_datetime - now).total_seconds()
                    # self.logger.info(f"{time_diff_seconds}")

                    if time_diff_seconds < 0:  # 이 얘기는 이미 보스가 뜨는 시간이 지나갔다는 얘기
                        # self.logger.info(f"보스가 이미 잡혔습니다.")
                        pass

                    elif time_diff_seconds <= cCHECK_ALARM_INTERVAL_SECONDS:
                        # str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 고정타임 보스목록
                        self.logger.info(f"{now} : 보스알람을 울려야 합니다.")
                        await channel.send(f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 출현 시간입니다.", tts=True)

                    else:  # time_diff_seconds > cCHECK_ALARM_INTERVAL_SECONDS
                        # str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 고정타임 보스목록
                        rh = round(time_diff_seconds // 3600)
                        rm = round((time_diff_seconds // 60) % 60)
                        rs = round(time_diff_seconds % 60)
                        # self.logger.info(f"보탐시간과의 차이 : {rh:02}:{rm:02}:{rs:02}")
                        self.logger.info(
                            f"{rh:02}:{rm:02}:{rs:02} - {cCMD_ALARM_WEEKDAY_FIXED_ONOFF}")  # {str_alarm_time}

            # 3. 인터벌 보스

    # ------------ End of : async def do_check_alarm(self) ------------

    @tasks.loop(seconds=cCHECK_ALARM_INTERVAL_SECONDS)
    async def check_alarms(self):
        # self.logger.info(f"check_alarms")
        await self.bot.wait_until_ready()
        async with self.lock:
            await self.do_check_alarm()

    @check_alarms.before_loop
    async def before_check_alarms(self):
        # self.logger.info(f"before_check_alarm")
        await self.bot.wait_until_ready()

    @check_alarms.after_loop
    async def after_check_alarms(self):
        # self.logger.info(f"after_send_message")
        if self.check_alarms.is_being_cancelled() and True:
            pass
            # TODO: alarm dic에 데이타가 남아 있으면 서버에 업로드하는 과정?


async def setup(bot: BtBot) -> None:
    logging.getLogger('cog').info(f"setup Alarm Cog")
    await bot.add_cog(Alarm(bot))
