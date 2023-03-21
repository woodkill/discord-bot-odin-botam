import asyncio
import json
import humanize
import datetime
from discord.ext import commands
from discord.ext import tasks
from discord.utils import format_dt

# from discord import Interaction
# from discord import Object
from common import *
from const_data import *
from const_key import *
from gcpocr import get_ocr_boss_time_list_by_bytes
import BtBot
import BtDb

cCHECK_ALARM_INTERVAL_SECONDS = 1


class Alarm(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot: BtBot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('bot.alarm')
        humanize.i18n.activate('ko_KR')
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

    @commands.command(name=cCMD_ALARM_TIMER)
    async def alarm_timers(self, ctx: commands.Context, *args) -> None:
        """
        보스 출현 몇 분 전마다 알람을 받을 지 설정합니다.
        :param ctx:
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_TIMER} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 인자가 없으면 현재 설정되어 있는 간격을 보여준다.
        if len(args) == 0:
            guild_min_list = self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARM_TIMERS]
            str_min_list = [str(v) for v in guild_min_list]
            str_min_message = f"분, ".join(str_min_list)
            message = f"보스출현 {str_min_message}분전에 알람을 보내드립니다."
            await send_ok_message(ctx, message)
            return

        # 분은 모두 숫자 이어야 하고 60 이하이어야 한다.
        # 모두 숫자라도 60 초과하는건 걸러낸다.
        try:
            min_list = [int(k) for k in args if int(k) <= 60]
        except ValueError:
            await send_error_message(ctx, u"숫자만 입력하세요.")
            return

        # 중복된게 있으면 제거하고 역순으로 소팅
        min_list = sorted(list(set(min_list)), reverse=True)

        # 메모리에도 적용하고 서버DB에도 적용한다.
        self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARM_TIMERS] = min_list
        self.db.set_guild_alarm_timers(ctx.guild.id, min_list)

        # 채널에 안내
        str_min_list = [str(v) for v in min_list]
        str_min_message = f"분, ".join(str_min_list)
        message = f"보스출현 {str_min_message}분전에 알람을 보내드립니다."
        await send_ok_message(ctx, message)

    @commands.command(name=cCMD_ALARM_LIST)
    async def alarm_list(self, ctx: commands.Context) -> None:
        """
        현재 설정되어 있는 알람 목록을 보여줍니다.
        :param ctx:
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_LIST} by {ctx.message.author}")

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
            await send_error_message(ctx, f"등록된 알람이 없습니다.")
            return

        embed_list = []  # 1111
        message = u""  # 2222
        prefix = "-" * 3 + " "
        postfix = " " + "-" * 20

        # 1. 월보 알람 검사
        try:
            guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED] = {}
            guild_daily_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]

        if len(guild_daily_fixed_alarm_dic) > 0:

            # 1111
            daily_fixed_embed = discord.Embed(
                title=cCMD_ALARM_DAILY_FIXED_ONOFF,
                description=u"매일",
                color=discord.Color.blue())
            # 2222
            message += f"{prefix}{cCMD_ALARM_DAILY_FIXED_ONOFF}{postfix}\n"

            for str_time, boss_list in sorted(guild_daily_fixed_alarm_dic.items()):
                # daily_fixed_embed.add_field(name=str_time, value=', '.join(boss_list), inline=True)
                daily_fixed_embed.add_field(name=str_time, value='', inline=True)
                message += f"매일 {str_time}\n"

            embed_list.append(daily_fixed_embed)  # 1111

        # 2. 성채 알람 검사
        try:
            guild_weekday_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED] = {}
            guild_weekday_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]

        if len(guild_weekday_fixed_alarm_dic) > 0:

            # 1111
            weekday_fixed_embed = discord.Embed(
                title=cCMD_ALARM_WEEKDAY_FIXED_ONOFF,
                description=u"",
                color=discord.Color.yellow())

            # 2222
            message += f"{prefix}{cCMD_ALARM_WEEKDAY_FIXED_ONOFF}{postfix}\n"

            for str_weekday_no, time_alarm_dic in guild_weekday_fixed_alarm_dic.items():
                str_weekday = cWEEKDAYS[int(str_weekday_no)]
                tempmsg = ""
                for t, b in time_alarm_dic.items():
                    # 이 아래 두 줄은 성채보스명까지 보여주는 방식
                    # tempmsg += f"{', '.join(b)}\n"
                    # weekday_fixed_embed.add_field(name=f"{str_weekday} {t}", value=tempmsg, inline=True)
                    # 이 아래 한 줄은 보스명 안 보여주는 방식
                    weekday_fixed_embed.add_field(name=f"{str_weekday} {t}", value="", inline=True) # 1111
                    message += f"{str_weekday} {t}\n" # 2222

            embed_list.append(weekday_fixed_embed) # 1111

        # 3. 필보 알람 검사
        """
        {
            "'2023-02-28 01:24:27'": [
                "굴베이그"
                ]
        }
        """
        try:
            guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_INTERVAL] = {}
            guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]

        if len(guild_interval_alarm_dic) > 0:

            # 1111
            interval_boss_embed = discord.Embed(
                title=cCMD_ALARM_REGISTER,
                description=u"",
                color=discord.Color.red())

            # 2222
            message += f"{prefix}{cCMD_ALARM_REGISTER}{postfix}\n"

            # self.logger.debug(dict(sorted(guild_interval_alarm_dic.items())))

            for str_interval_boss_time, interval_boss_name_list in dict(sorted(guild_interval_alarm_dic.items())).items():
                interval_boss_time = datetime.datetime.strptime(str_interval_boss_time, cTIME_FORMAT_INTERVAL_TYPE)
                util_str = format_dt(interval_boss_time, style='R')
                nd = humanize.naturalday(interval_boss_time, format='%m월%d일')
                nt = str_interval_boss_time[11:]
                for today_alarm_name in interval_boss_name_list:
                    # 이건 이름 보여주는 방식
                    # interval_boss_embed.add_field(name=boss_name, value=str_interval_boss_time, inline=True)
                    # 이건 이름 안 보여주는 방식
                    # interval_boss_embed.add_field(name=boss_name, value=f"{nd} {nt}", inline=True)
                    # 이건 구어체 방식 마우스 위로 대면 날짜 나옴
                    interval_boss_embed.add_field(name=today_alarm_name, value=f"{util_str}", inline=True) # 1111
                    message += f"{today_alarm_name} : {nd} {nt}\n" # 2222

            embed_list.append(interval_boss_embed)

        # 4. 오늘 알람 검사

        try:
            guild_today_alarm_dic = guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM]
        except KeyError:
            guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM] = {}
            guild_today_alarm_dic = guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM]

        if len(guild_today_alarm_dic) > 0:

            # 1111
            today_alarm_embed = discord.Embed(
                title=cCMD_ALARM_TODAY,
                description=u"",
                color=discord.Color.purple())

            # 2222
            message += f"{prefix}{cCMD_ALARM_TODAY}{postfix}\n"

            # self.logger.debug(dict(sorted(guild_today_alarm_dic.items())))

            for str_today_schedule_time, today_schedule_name_list in dict(
                    sorted(guild_today_alarm_dic.items())).items():
                today_alarm_datetime = datetime.datetime.strptime(str_today_schedule_time, cTIME_FORMAT_INTERVAL_TYPE)
                util_str = format_dt(today_alarm_datetime, style='R')
                nd = humanize.naturalday(today_alarm_datetime, format='%m월%d일')
                nt = str_today_schedule_time[11:]
                for today_alarm_name in today_schedule_name_list:
                    # 이건 이름 보여주는 방식
                    # today_alarm_embed.add_field(name=today_alarm_name, value=str_today_schedule_time, inline=True)
                    # 이건 이름 안 보여주는 방식
                    # interval_boss_embed.add_field(name=today_alarm_name, value=f"{nd} {nt}", inline=True)
                    # 이건 구어체 방식 마우스 위로 대면 날짜 나옴
                    today_alarm_embed.add_field(name=today_alarm_name, value=f"{util_str}", inline=True)  # 1111
                    message += f"{today_alarm_name} : {nd} {nt}\n"  # 2222

            embed_list.append(today_alarm_embed)

        # 여기서 1111, 2222 중에 하나만 살린다.
        if len(embed_list) > 0:
            # 1111
            # await ctx.send(embeds=embed_list)
            # 2222
            message = message[:-1]
            await send_common_message(ctx, message)
        else:
            await send_error_message(ctx, u"현재 켜져 있는 알람이 없습니다.")

    @commands.command(name=cCMD_ALARM_RESET)
    async def alarm_reset(self, ctx: commands.Context) -> None:
        """
        이 길드의 모든 알람을 지운다.
        :param ctx:
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_RESET} by {ctx.message.author}")

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
            await send_error_message(ctx, f"등록된 알람이 없습니다.")
            return

        guild_dic[kFLD_ALARMS] = {"0": {}, "1": {}, "2": {}, "3": {}}
        self.db.set_guild_alarms(ctx.guild.id, guild_dic[kFLD_ALARMS])
        await send_ok_message(ctx, u"모든 알람을 지웠습니다.")

    @commands.command(name=cCMD_ALARM_TODAY)
    async def today_alarm(self, ctx: commands.Context, *args) -> None:
        """
        금일스케쥴 맘대로 이름 등록용
        :param ctx:
        :param args:
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_TODAY} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) != 2:  # 인자가 2개이어야 함
            await send_usage_embed(ctx, cCMD_ALARM_TODAY)
            return

        # 두번째 인자가 남은시간 형식에 맞는 지 검사
        str_wanted_time = args[1]
        if str_wanted_time != cCMD_PARAM_OFF and not is_hh_mm_timedelta_format(str_wanted_time):
            await send_error_message(ctx, f"{str_wanted_time} : 알람시각이 형식에 맞지 않습니다.")
            return

        str_wanted_name = args[0]

        # 중첩된 dict를 쓰기 좋게 꺼내 놓는다.
        guild_dic = self.bot.odin_guilds_dic[ctx.guild.id]
        try:
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        except KeyError:
            guild_dic[kFLD_ALARMS] = {}
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        try:
            guild_today_alarm_dic = guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM]
        except KeyError:
            guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM] = {}
            guild_today_alarm_dic = guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM]

        # 먼저 모든 알람을 뒤져서 같은 이름의 알람이 등록되어 있으면 지운다.
        for str_today_schedule_time, today_schedule_name_list in guild_today_alarm_dic.items():
            # 알람명이 있는데... 알람명 리스트에 알람명이 하나만 있으면 알람 자체를 지우고
            # 알람명이 여러개 있으면 이 알람명만 지워야 한다.
            if str_wanted_name in today_schedule_name_list:
                guild_today_alarm_dic[str_today_schedule_time] \
                    = [v for v in today_schedule_name_list if v != str_wanted_name]
        # 알람명 리스트가 비어있는 알람은 지운다.
        guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM] = {k: v for k, v in guild_today_alarm_dic.items() if len(v) != 0}
        guild_today_alarm_dic = guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM]  # 밑에서 쓰려면

        # 알람을 지우는 명령어인 경우..
        if str_wanted_time == cCMD_PARAM_OFF:
            # 서버에 기록하고 메세지 보내고 종료
            self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)
            await send_ok_message(ctx, f"{str_wanted_name} 알람을 취소했습니다.")
            return

        # 키로 : 알람 시각, 값으로 : 알람명 리스트인 dict를 만들어 넣는다.
        # 알람명을 "리스트"로 넣는 이유는 만에 하나 같은 시각의 알람을 중복해서 넣을 수 있으므로...

        # 먼저 오늘의 원하는 시각 알람 만들어 낸다.
        now_date = datetime.datetime.now().date()
        # d, h, m, s = get_separated_time_hhmm(str_wanted_time)
        time = datetime.datetime.strptime(str_wanted_time, cTIME_FORMAT_FIXED_TYPE).time()
        # td = datetime.timedelta(days=d, hours=h, minutes=m, seconds=s)
        wanted_alarm_time = datetime.datetime.combine(now_date, time)
        alarm_key = wanted_alarm_time.strftime(cTIME_FORMAT_INTERVAL_TYPE)

        if alarm_key not in guild_today_alarm_dic:
            guild_today_alarm_dic[alarm_key] = [str_wanted_name]
        else:
            guild_today_alarm_dic[alarm_key].append(str_wanted_name)

        # 잘 들어갔나 전체길드목록 검사
        # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

        # 서버 DB에 길드의 알람설정 상태 덮어쓰기
        self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

        await send_ok_message(ctx, f"{str_wanted_name} : {alarm_key} 알람 설정되었습니다.")

    @commands.command(name=cCMD_ALARM_REGISTER)
    async def register_boss_alarm(self, ctx: commands.Context, *args) -> None:
        """
        필보 보탐 등록 기능
        :param ctx:
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_REGISTER} {args} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) != 2:  # 인자가 2개이어야 함
            await send_usage_embed(ctx, cCMD_ALARM_REGISTER)
            return

        # 첫번째 인자가 보스명인지 검사
        arg_boss_name = args[0]
        boss_key, boss = self.db.get_boss_item_by_name(args[0])
        if boss_key is None:
            await send_error_message(ctx, f"{arg_boss_name} : 존재하지 않는 보스명입니다.")
            return

        # 두번째 인자가 남은시간 형식에 맞는 지 검사
        str_remained_time = args[1]
        if str_remained_time != cCMD_PARAM_OFF and not is_korean_timedelta_format(str_remained_time):
            await send_error_message(ctx, f"{str_remained_time} : 남은시간이 형식에 맞지 않습니다.")
            return

        str_boss_name = boss[kBOSS_NAME]

        # 중첩된 dict를 쓰기 좋게 꺼내 놓는다.
        guild_dic = self.bot.odin_guilds_dic[ctx.guild.id]
        try:
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        except KeyError:
            guild_dic[kFLD_ALARMS] = {}
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        try:
            guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_INTERVAL] = {}
            guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]

        # 먼저 모든 알람을 뒤져서 같은 보스 알람이 등록되어 있으면 지운다.
        for str_interval_boss_time, interval_boss_name_list in guild_interval_alarm_dic.items():
            # 보스명이 있는데... 보스명 리스트에 보스명이 하나만 있으면 알람 자체를 지우고
            # 보스명이 여러개 있으면 이 보스명만 지워야 한다.
            if str_boss_name in interval_boss_name_list:
                guild_interval_alarm_dic[str_interval_boss_time] \
                    = [v for v in interval_boss_name_list if v != str_boss_name]
        # 보스명 리스트가 비어있는 알람은 지운다.
        guild_alarm_dic[cBOSS_TYPE_INTERVAL] = {k: v for k, v in guild_interval_alarm_dic.items() if len(v) != 0}
        guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]  # 밑에서 쓰려면

        # 알람을 지우는 명령어인 경우..
        if str_remained_time == cCMD_PARAM_OFF:
            # 서버에 기록하고 메세지 보내고 종료
            self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)
            await send_ok_message(ctx, f"{str_boss_name} 알람을 취소했습니다.")
            return

        # 키로 : 보스가 뜨는 날짜 시간, 값으로 : 보스명 리스트인 dict를 만들어 넣는다.
        # 보스명을 리스트로 넣는 이유는 만에 하나 초까지 같은 시간에 보스가 중복해서 뜰 수 있으므로...

        # 먼저 현재시간과 남은시간을 더해서 보스가 뜨는 시각을 만들어 낸다.
        now = datetime.datetime.now()
        d, h, m, s = get_separated_timedelta_korean(str_remained_time)
        td = datetime.timedelta(days=d, hours=h, minutes=m, seconds=s)
        boss_time = now + td
        alarm_key = boss_time.strftime(cTIME_FORMAT_INTERVAL_TYPE)

        if alarm_key not in guild_interval_alarm_dic:
            guild_interval_alarm_dic[alarm_key] = [str_boss_name]
        else:
            guild_interval_alarm_dic[alarm_key].append(str_boss_name)

        # 잘 들어갔나 전체길드목록 검사
        # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

        # 서버 DB에 길드의 알람설정 상태 덮어쓰기
        self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

        await send_ok_message(ctx, f"{str_boss_name} : {alarm_key} 알람 설정되었습니다.")

    @commands.command(name=cCMD_ALARM_TIMETABLE)
    async def time_table_image(self, ctx: commands.Context) -> None:
        """
        시간표 이미지로 보탐 알람 자동등록
        :param ctx:
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_TIMETABLE} by {ctx.message.author}")

        # TODO : 첨부화일 여러개 올리면 한꺼번에 처리하도록 수정

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 비정상 상태 체크
        if ctx.guild.id not in self.bot.odin_guilds_dic:
            await send_error_message(ctx, cMSG_NO_GUILD_INFO)
            return

        # 이미지가 첨부되었는지 검사
        if len(ctx.message.attachments) < 1:  # 이미지가 1개만 첨부되어야 함.
            await send_usage_embed(ctx, cCMD_ALARM_TIMETABLE, additional="보스시간표 영역을 캡쳐해서 첨부해주시기 바랍니다.")
            return

        # 첨부 파일 검사
        for attachment in ctx.message.attachments:
            if attachment.content_type not in ('image/jpeg', 'image/jpg', 'image/png'):
                await send_error_message(ctx, u"JPG나 PNG로 저장해서 첨부해 주세요")
                return

        # 중첩된 dict를 쓰기 좋게 꺼내 놓는다.
        guild_dic = self.bot.odin_guilds_dic[ctx.guild.id]
        try:
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        except KeyError:
            guild_dic[kFLD_ALARMS] = {}
            guild_alarm_dic = guild_dic[kFLD_ALARMS]
        try:
            guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]
        except KeyError:
            guild_alarm_dic[cBOSS_TYPE_INTERVAL] = {}
            guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]

        # 오딘 보스명 리스트
        odin_bossname_list = self.db.get_bossname_list()

        # 스크린샷 찍은 날짜를 오늘로 가정하기 위해..
        now = datetime.datetime.now()
        now_date = now.date()

        # 각각의 첨부화일에 대해서...
        for attachment in ctx.message.attachments:

            # self.logger.debug(attachment.content_type)
            # self.logger.debug(attachment.url)
            # self.logger.debug(attachment.description)
            # self.logger.debug(attachment.filename)

            # 이미지를 분석해서 스샷시간과 인식된 보스리스트 및 시간 리스트 받아온다.
            image_bytes = await attachment.read()
            str_screenshot_time, boss_delta_time_list = get_ocr_boss_time_list_by_bytes(image_bytes, odin_bossname_list)
            '''
            233915
            '''
            '''
            [['혼돈의마수굴베이그', '2시간 16분 남음'], ['분노의모네가름', '3시간 50분 남음'], ['혼돈의사제강글로티', '1일 0시간 남음'], ['나태의드라우그', '19시간 31분 남음']]
            '''
            self.logger.debug(str_screenshot_time)
            self.logger.debug(boss_delta_time_list)

            # 스크린샷이 찍힌 시각을 알아냄
            # 스크린 샷에는 날짜가 나오지 않기 때문에 날짜는 현재로 가정한다.
            screenshot_time = datetime.datetime.strptime(str_screenshot_time, cTIME_FORMAT_TIME6DIGIT).time()
            screen_shot_datetime = datetime.datetime.combine(now_date, screenshot_time)

            message = u""

            # 인식된 [[보스명, 보스남은시간], ...] 리스트 순회하면서...
            for boss_delta_time_pair in  boss_delta_time_list:

                ocr_boss_name = boss_delta_time_pair[0]
                str_ocr_boss_delta_time = boss_delta_time_pair[1]

                # 출현중인 보스 처리
                if str_ocr_boss_delta_time == u"출현중":
                    message += f"{ocr_boss_name} : {str_ocr_boss_delta_time}\n"
                    continue

                # 인식된 남은 시간이 형식에 안맞으면 패쓰, 맞으면 OCR timedelta 객체 생성
                if not is_korean_timedelta_format(str_ocr_boss_delta_time):
                    continue
                ocr_d, ocr_h, ocr_m, ocr_s = get_separated_timedelta_korean(str_ocr_boss_delta_time)
                ocr_td = datetime.timedelta(days=ocr_d, hours=ocr_h, minutes=ocr_m, seconds=ocr_s)

                # 인식된 보스명이 보스목록에 있는 이름이 아니면 패쓰
                boss_key, boss_dict = self.db.get_boss_item_by_name(ocr_boss_name)
                if boss_key is None:
                    continue

                # 인식한 보스가 인터벌 타입이 아니면 패쓰
                if boss_dict[kBOSS_TYPE] != cBOSS_TYPE_INTERVAL:
                    continue

                # 남은시간이 보스의 인터벌 시간보다 길면 말이 안되므로 패쓰
                try:
                    str_boss_interval = boss_dict[kBOSS_INTERVAL]
                except KeyError:
                    continue
                boss_d, boss_h, boss_m, boss_s = get_separated_timedelta_ddhhmm(str_boss_interval)
                boss_td = datetime.timedelta(days=boss_d, hours=boss_h, minutes=boss_m, seconds=boss_s)
                if ocr_td > boss_td:
                    continue

                # 먼저 모든 알람을 뒤져서 같은 보스 알람이 등록되어 있으면 지운다.
                for str_interval_boss_time, interval_boss_name_list in guild_interval_alarm_dic.items():
                    # 보스명이 있는데... 보스명 리스트에 보스명이 하나만 있으면 알람 자체를 지우고
                    # 보스명이 여러개 있으면 이 보스명만 지워야 한다.
                    if ocr_boss_name in interval_boss_name_list:
                        guild_interval_alarm_dic[str_interval_boss_time] \
                            = [v for v in interval_boss_name_list if v != ocr_boss_name]
                # 보스명 리스트가 비어있는 알람은 지운다.
                guild_alarm_dic[cBOSS_TYPE_INTERVAL] = {k: v for k, v in guild_interval_alarm_dic.items() if len(v) != 0}
                guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]  # 밑에서 쓰려면

                # 키로 : 보스가 뜨는 날짜 시간, 값으로 : 보스명 리스트인 dict를 만들어 넣는다.
                # 보스명을 리스트로 넣는 이유는 만에 하나 초까지 같은 시간에 보스가 중복해서 뜰 수 있으므로...

                # 인식된 보스가 뜨는 시각
                ocr_boss_time = screen_shot_datetime + ocr_td
                # 이게 현재보다 앞이면 패쓰
                if ocr_boss_time < now:
                    continue

                # dd:hh:mm 이 알람키
                alarm_key = ocr_boss_time.strftime(cTIME_FORMAT_INTERVAL_TYPE)

                # 길드 알람 목록에 넣는다.
                if alarm_key not in guild_interval_alarm_dic:
                    guild_interval_alarm_dic[alarm_key] = [ocr_boss_name]
                else:
                    guild_interval_alarm_dic[alarm_key].append(ocr_boss_name)

                # 잘 들어갔나 전체길드목록 검사
                # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

                # 메세지 이어 붙이기
                message += f"{ocr_boss_name} : {str_ocr_boss_delta_time} : {alarm_key} 알람\n"

            # -------- End of ---- for boss_delta_time_pair in  boss_delta_time_list:

            if len(message) > 0:
                message = message[:-1]

            # 서버 DB에 길드의 알람설정 상태 덮어쓰기
            self.bot.db.set_guild_alarms(ctx.guild.id, guild_alarm_dic)

            await send_ok_message(ctx, message)

            # test_message = f"이미지 캡쳐 시간 : {str_screenshot_time}\n"
            # for boss_delta_time_item in boss_delta_time_list:
            #     boss_name = boss_delta_time_item[0]
            #     boss_time = boss_delta_time_item[1]
            #     test_message += f"{boss_name} : {boss_time}\n"
            # test_message = test_message[:-1]
            #
            # await send_ok_message(ctx, test_message)

    @commands.command(name=cCMD_ALARM_DAILY_FIXED_ONOFF)
    async def onoff_daily_fixed_alarm(self, ctx: commands.Context) -> None:
        """
        월보 온/오프 기능
        :param ctx: Context
        :return:
        """
        self.logger.info(f"{cCMD_ALARM_DAILY_FIXED_ONOFF} by {ctx.message.author}")

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

        # self.logger.debug(guild_dic)

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
            def __init__(self, bot: BtBot, timeout=None):
                self.bot = bot
                self.logger = logging.getLogger('bot.alarm')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="켜기", style=discord.ButtonStyle.blurple)
            async def daily_fixed_alarm_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                """
                월드보탐 명령어의 reaction으로 나오는 켜기 버튼을 눌렀을 때 실행되는 함수이다.
                :param interaction:
                :param button:
                :return:
                """

                # self.logger.debug(f"{self.bot.odin_guilds_dic}")

                # 마스터정보에서 월드보스 정보를 가지고 알람 dict 만들어 줌
                # 시각을 key로 하고 값을 해당시간에 뜨는 보스명 list로 하는 dict. 하루에 여러번 고정시각이 있을 수 있음.
                alarm_dic = self.bot.db.get_daily_fiexed_alarm_info_from_master()
                # self.logger.debug(f"{json.dumps( alarm_dic, indent=2, ensure_ascii=False)}")
                if len(alarm_dic) == 0:
                    await response_error_message(interaction.response, f"월보 정보가 없습니다.")
                    return

                # 모든 길드의 알람 dict안의 현재 길드의 월보 dict에 넣어준다.
                self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARMS][cBOSS_TYPE_DAILY_FIXED] = alarm_dic

                # 길드전체 알람 dict에 제대로 들어가 있는지 검사
                # self.logger.debug(f"{self.bot.odin_guilds_dic}")
                # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=4, ensure_ascii=False)}")

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
                # self.logger.debug(f"{self.bot.odin_guilds_dic}")

                # 길드알람 dict에 cBOSS_TYPE_DAILY_FIXED를 키로 하는 dict를 지운다.
                # 이 dict이 비어 있다는 것이 고정보스 알람을 껐다는 뜻
                guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED] = {}

                # 길드전체 알람 dict에 제대로 들어가 있는지?
                # self.logger.debug(f"{self.bot.odin_guilds_dic}")
                # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

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
        self.logger.info(f"{cCMD_ALARM_WEEKDAY_FIXED_ONOFF} by {ctx.message.author}")

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

        # self.logger.debug(guild_dic)

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
            def __init__(self, bot: BtBot, timeout=None):
                self.bot = bot
                self.logger = logging.getLogger('bot.alarm')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="켜기", style=discord.ButtonStyle.blurple)
            async def weekday_fixed_alarm_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                """
                성채 명령어의 reaction으로 나오는 켜기 버튼을 눌렀을 때 실행되는 함수이다.
                :param interaction:
                :param button:
                :return:
                """

                # self.logger.debug(f"{self.bot.odin_guilds_dic}")

                # 마스터정보에서 성채보스 정보를 가지고 알람 dict 만들어줌
                alarm_dic = self.bot.db.get_weekday_fiexed_alarm_info_from_master()
                if len(alarm_dic) == 0:
                    await response_error_message(interaction.response, f"성채 정보가 없습니다.")
                    return

                # 요일번호 문자열을 Key 하고 값을 {시간문자열:[보스명리스트]}로 하는 dict을 만든다.
                self.bot.odin_guilds_dic[ctx.guild.id][kFLD_ALARMS][cBOSS_TYPE_WEEKDAY_FIXED] = alarm_dic
                # for weekday, time_alarm_dic in alarm_dic.items():
                #     guild_weekly_fixed_alarm_dic[weekday] = time_alarm_dic

                # 길드전체 알람 dict에 제대로 들어가 있는지 검사
                # self.logger.debug(f"{self.bot.odin_guilds_dic}")
                # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

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
                # self.logger.debug(f"{self.bot.odin_guilds_dic}")

                # 길드알람 dict에 cBOSS_TYPE_WEEKDAY_FIXED를 키로 하는 dict를 지운다.
                # 이 dict이 비어 있다는 것이 성채보스 알람을 껐다는 뜻
                guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED] = {}

                # 길드전체 알람 dict에 제대로 들어가 있는지?
                # self.logger.debug(f"{self.bot.odin_guilds_dic}")
                # self.logger.debug(f"{json.dumps(self.bot.odin_guilds_dic, indent=2, ensure_ascii=False)}")

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

            if channel is None:
                continue

            # 이 길드의 알람 간격
            try:
                guild_timer_list = guild_dic[kFLD_ALARM_TIMERS]
            except KeyError:
                guild_timer_list = []

            # 초로 바꾼 리스트로 변환
            guild_timer_seconds_list = [v * 60 for v in guild_timer_list]

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
                today_alarm_datetime = datetime.datetime.combine(now_date, alarm_time)
                # self.logger.debug(f"alarm_datetime: {alarm_datetime}")

                # 현재 시각과 보스가 뜨는 시각의 차이
                time_diff_seconds = (today_alarm_datetime - now).total_seconds()
                # self.logger.debug(f"{time_diff_seconds}")

                # str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 월보 보스목록

                if time_diff_seconds < 0:  # 이 얘기는 이미 보스가 뜨는 시간이 지나갔다는 얘기
                    # self.logger.debug(f"보스가 이미 잡혔습니다.")
                    continue

                # 알람간격 중에 하나로 알려야 하는 상황 체크
                i = -1
                for j in range(len(guild_timer_seconds_list)):
                    # 알람 간격 중에 하나가 체크시간 이내 범위에 있다.
                    diff_timer = time_diff_seconds - guild_timer_seconds_list[j]
                    if cCHECK_ALARM_INTERVAL_SECONDS - 1 < diff_timer <= cCHECK_ALARM_INTERVAL_SECONDS:
                        i = j
                        break
                if i != -1:
                    message = f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 출현 {guild_timer_list[i]}분 전입니다."
                    await channel.send(message, tts=True)
                    continue

                # 보스 출현 시간
                if time_diff_seconds <= cCHECK_ALARM_INTERVAL_SECONDS:
                    message = f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 출현 시간입니다."
                    await channel.send(message, tts=True)
                    continue

                # log용 : time_diff_seconds > cCHECK_ALARM_INTERVAL_SECONDS
                rh = round(time_diff_seconds // 3600)
                rm = round((time_diff_seconds // 60) % 60)
                rs = round(time_diff_seconds % 60)
                # self.logger.debug(f"보탐시간과의 차이 : {rh:02}:{rm:02}:{rs:02}")
                # self.logger.debug(f"{rh:02}:{rm:02}:{rs:02} 전 - {cCMD_ALARM_DAILY_FIXED_ONOFF}")  # {str_alarm_time}

            # 2. 성채 알람
            try:
                guild_weekday_fixed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_WEEKDAY_FIXED]
            except KeyError:
                guild_weekday_fixed_alarm_dic = {}

            for str_weekday_no, weekday_alarm_dic in guild_weekday_fixed_alarm_dic.items():

                # 오늘이 성채 날짜가 아니면 통과
                weekday_no = int(str_weekday_no)
                if now_weekday_no != weekday_no:
                    # self.logger.debug(f"오늘은 {cWEEKDAYS[weekday_no]}이 아님.")
                    continue

                for str_alarm_time, boss_list in weekday_alarm_dic.items():

                    # 시각:분 형태로 저장되어 있음. 오늘 보스타임으로 변환
                    alarm_time = datetime.datetime.strptime(str_alarm_time, cTIME_FORMAT_FIXED_TYPE).time()
                    today_alarm_datetime = datetime.datetime.combine(now_date, alarm_time)
                    # self.logger.debug(f"alarm_datetime: {alarm_datetime}")

                    # 현재 시각과 보스가 뜨는 시각의 차이
                    time_diff_seconds = (today_alarm_datetime - now).total_seconds()
                    # self.logger.debug(f"{time_diff_seconds}")

                    # str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 성채 보스목록

                    if time_diff_seconds < 0:  # 이 얘기는 이미 보스가 뜨는 시간이 지나갔다는 얘기
                        # self.logger.debug(f"보스가 이미 잡혔습니다.")
                        continue

                    # 알람간격 중에 하나로 알려야 하는 상황 체크
                    i = -1
                    for j in range(len(guild_timer_seconds_list)):
                        # 알람 간격 중에 하나가 체크시간 이내 범위에 있다.
                        diff_timer = time_diff_seconds - guild_timer_seconds_list[j]
                        if cCHECK_ALARM_INTERVAL_SECONDS - 1 < diff_timer <= cCHECK_ALARM_INTERVAL_SECONDS:
                            i = j
                            break
                    if i != -1:
                        message = f"{cBOSS_TYPE_WEEKDAY_FIXED} 출현 {guild_timer_list[i]}분 전입니다."
                        await channel.send(message, tts=True)
                        continue

                    # 보스 출현 시간
                    if time_diff_seconds <= cCHECK_ALARM_INTERVAL_SECONDS:
                        message = f"{cBOSS_TYPE_WEEKDAY_FIXED} 출현 시간입니다."
                        await channel.send(message, tts=True)
                        continue

                    # log용 : time_diff_seconds > cCHECK_ALARM_INTERVAL_SECONDS
                    rh = round(time_diff_seconds // 3600)
                    rm = round((time_diff_seconds // 60) % 60)
                    rs = round(time_diff_seconds % 60)
                    # self.logger.debug(f"보탐시간과의 차이 : {rh:02}:{rm:02}:{rs:02}")
                    # self.logger.debug(f"{rh:02}:{rm:02}:{rs:02} 전 - {cCMD_ALARM_WEEKDAY_FIXED_ONOFF}")

            # 3. 인터벌 보스
            """
                    {
                        "'2023-02-28 01:24:27'": [
                            "굴베이그"
                            ]
                    }
            """
            try:
                guild_interval_alarm_dic = guild_alarm_dic[cBOSS_TYPE_INTERVAL]
            except KeyError:
                guild_interval_alarm_dic = {}

            # 이미 지나갔거나 알람문자를 보낸 알람 시간은 지워야 하므로 for문이 다 지난 다음 지운다.
            # 그 지울 알람 키를 저장해 둘 리스트
            to_remove = []

            for str_alarm_time, boss_list in guild_interval_alarm_dic.items():

                # '2023-02-28 01:24:27' 형태로 저장되어 있음.
                today_alarm_datetime = datetime.datetime.strptime(str_alarm_time, cTIME_FORMAT_INTERVAL_TYPE)
                # self.logger.debug(f"alarm_datetime: {alarm_datetime}")

                # 현재 시각과 보스가 뜨는 시각의 차이
                time_diff_seconds = (today_alarm_datetime - now).total_seconds()
                # self.logger.debug(f"{time_diff_seconds}")

                str_boss_list = ", ".join(boss_list)  # 이 시간에 뜨는 보스목록

                if time_diff_seconds < 0:  # 이 얘기는 이미 보스가 뜨는 시간이 지나갔다는 얘기
                    # self.logger.debug(f"보스출현 시간이 이미 지나갔습니다.")
                    to_remove.append(str_alarm_time)
                    continue

                # 알람간격 중에 하나로 알려야 하는 상황 체크
                i = -1
                for j in range(len(guild_timer_seconds_list)):
                    # 알람 간격 중에 하나가 체크시간 이내 범위에 있다.
                    diff_timer = time_diff_seconds - guild_timer_seconds_list[j]
                    if cCHECK_ALARM_INTERVAL_SECONDS - 1 < diff_timer <= cCHECK_ALARM_INTERVAL_SECONDS:
                        i = j
                        break
                if i != -1:
                    message = f"{str_boss_list} 출현 {guild_timer_list[i]}분 전입니다."
                    await channel.send(message, tts=True)
                    continue

                # 보스 출현 시간
                if time_diff_seconds <= cCHECK_ALARM_INTERVAL_SECONDS:
                    message = f"{str_boss_list} 출현 시간입니다."
                    await channel.send(message, tts=True)
                    to_remove.append(str_alarm_time)
                    continue

                # log용 : time_diff_seconds > cCHECK_ALARM_INTERVAL_SECONDS
                rh = round(time_diff_seconds // 3600)
                rm = round((time_diff_seconds // 60) % 60)
                rs = round(time_diff_seconds % 60)
                # self.logger.debug(f"보탐시간과의 차이 : {rh:02}:{rm:02}:{rs:02}")
                # self.logger.debug(f"{rh:02}:{rm:02}:{rs:02} - {str_boss_list}")  # {str_alarm_time}

            # 인터벌 타입 보스는 알람 목록에서 지워야 한다.
            for alarm_key in to_remove:
                guild_interval_alarm_dic.pop(alarm_key)
                self.db.set_guild_alarms(guild_id, guild_alarm_dic)

            # 4 "오늘" 명령어용
            '''
            {
                "2023-03-03 21:47:00": [
                    "알브릴레이"
                ]
            }
            '''

            try:
                guild_today_alarm_dic = guild_alarm_dic[cKEY_TODAY_SCHDULE_ALARM]
            except KeyError:
                guild_today_alarm_dic = {}

            # 이미 지나갔거나 알람문자를 보낸 알람 시간은 지워야 하므로 for문이 다 지난 다음 지운다.
            # 그 지울 알람 키를 저장해 둘 리스트
            to_remove = []

            for str_today_schedule_time, today_schedule_name_list in guild_today_alarm_dic.items():

                # '2023-02-28 01:24:27' 형태로 저장되어 있음.
                today_alarm_datetime = datetime.datetime.strptime(str_today_schedule_time, cTIME_FORMAT_INTERVAL_TYPE)
                # self.logger.debug(f"alarm_datetime: {today_alarm_datetime}")

                # 현재 시각과 보스가 뜨는 시각의 차이
                time_diff_seconds = (today_alarm_datetime - now).total_seconds()
                # self.logger.debug(f"{time_diff_seconds}")

                str_today_schedule_name_list = ", ".join(today_schedule_name_list)  # 이 시간에 등록되어 있는 알람명목록

                if time_diff_seconds < 0:  # 이 얘기는 이미 알람 시간이 지나갔다는 얘기
                    # self.logger.debug(f"알람 시간이 이미 지나갔습니다.")
                    to_remove.append(str_today_schedule_time)
                    continue

                # 알람간격 중에 하나로 알려야 하는 상황 체크
                i = -1
                for j in range(len(guild_timer_seconds_list)):
                    # 알람 간격 중에 하나가 체크시간 이내 범위에 있다.
                    diff_timer = time_diff_seconds - guild_timer_seconds_list[j]
                    if cCHECK_ALARM_INTERVAL_SECONDS - 1 < diff_timer <= cCHECK_ALARM_INTERVAL_SECONDS:
                        i = j
                        break
                if i != -1:
                    message = f"{str_today_schedule_name_list} {guild_timer_list[i]}분 전입니다."
                    await channel.send(message, tts=True)
                    continue

                # 알람 시간
                if time_diff_seconds <= cCHECK_ALARM_INTERVAL_SECONDS:
                    message = f"{str_today_schedule_name_list} 시간입니다."
                    await channel.send(message, tts=True)
                    to_remove.append(str_today_schedule_time)
                    continue

                # log용 : time_diff_seconds > cCHECK_ALARM_INTERVAL_SECONDS
                rh = round(time_diff_seconds // 3600)
                rm = round((time_diff_seconds // 60) % 60)
                rs = round(time_diff_seconds % 60)
                # self.logger.debug(f"알람시간과의 차이 : {rh:02}:{rm:02}:{rs:02}")
                # self.logger.debug(f"{rh:02}:{rm:02}:{rs:02} - {str_today_schedule_name_list}")  # {str_alarm_time}

            # 알람 목록에서 지워야 한다.
            for alarm_key in to_remove:
                guild_today_alarm_dic.pop(alarm_key)
                self.db.set_guild_alarms(guild_id, guild_alarm_dic)

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


async def setup(bot: BtBot) -> None:
    logging.getLogger('bot.alarm').info(f"setup Alarm Cog")
    await bot.add_cog(Alarm(bot))
