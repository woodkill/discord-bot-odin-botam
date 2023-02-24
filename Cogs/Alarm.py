import discord
import asyncio
import logging
import json
from discord.ext import commands, tasks
from discord import app_commands
# from discord import Interaction
# from discord import Object
from const_key import *
from const_data import *
from common import *
import BtBot
import BtDb


class Alarm(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('cog')
        # async task
        self.lock = asyncio.Lock()
        self.check_alarms.start()
        # 알람목록
        self.all_alarm_dic = {}
        # for test
        self.count = 0

    def cog_unload(self) -> None:
        self.check_alarms.cancel()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Alarm Cog loaded.")

    @commands.command(name=cALARM_STATUS)
    async def alarm_status(self, ctx: commands.Context) -> None:
        '''

        :param ctx:
        :return:
        '''
        logging.info(f"{cALARM_STATUS}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_error_embed(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        json_str = json.dumps(self.all_alarm_dic, indent=4, ensure_ascii=False)
        await ctx.reply(f"{json_str}")

    @commands.command(name=cALARM_WORLDBOSS_ONOFF)
    async def onoff_world_boss_alarm(self, ctx: commands.Context) -> None:
        '''
        월드보탐 온/오프 기능
        :param ctx: Context
        :return:
        '''
        logging.info(f"{cALARM_WORLDBOSS_ONOFF}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_error_embed(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # TODO:여기를 embed로 바꿔야 한다.
        # 이 길드의 월드보탐이 현재 ON상태인지 OFF상태인지 검사
        is_on = False
        view_message = u"현재 월드보탐 알람은 꺼진 상태입니다."
        if ctx.guild.id in self.all_alarm_dic:
            if cBOSS_TYPE_DAILY_FIXED in self.all_alarm_dic[ctx.guild.id]:
                is_on = True
                view_message = u"현재 월드보탐 알람은 켜진 상태입니다."

        class Buttons(discord.ui.View):
            # TODO: all_alarm_dic을 BtBot으로 옮기는 작업을 하자. 아니면
            def __init__(self, cog: Alarm, timeout=180):
                self.cog = cog
                super().__init__(timeout=timeout)

            @discord.ui.button(label="켜기", style=discord.ButtonStyle.blurple, disabled=is_on)
            async def world_boss_alarm_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                '''
                월드보탐 명령어의 reaction으로 나오는 켜기 버튼을 눌렀을 때 실행되는 함수이다.
                Alarm Cog 객체 안의 all_alarm_dic dict에 이 길드의 월드보스 alarm_dic을 만들어 넣는다.
                :param interaction:
                :param button:
                :return:
                '''
                # self.cog.logger.info(f"{self.cog.all_alarm_dic}")
                # 마스터정보에서 월드보스 정보를 가지고 알람 dict 만들어줌
                alarm_dic = self.cog.db.get_boss_alarm_in_master(option=cBOSS_TYPE_DAILY_FIXED)
                if len(alarm_dic) == 0:
                    await interaction.response.send_message(f"월드보스 정보가 없습니다.")
                    return
                # 전체 알람 dict에서 이 길드에 대한 알람 dict를 가져옴(없으면 만들어준다)
                if ctx.guild.id not in self.cog.all_alarm_dic:
                    self.cog.all_alarm_dic[ctx.guild.id] = {}
                guild_alarm_dic = self.cog.all_alarm_dic[ctx.guild.id]
                # 길드알람 dict에 cBOSS_TYPE_DAILY_FIXED를 키로 하는 dict를 가져옴.(없으면 만들어준다)
                if cBOSS_TYPE_DAILY_FIXED not in guild_alarm_dic:
                    guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED] = {}
                guild_daily_fiexed_alarm_dic = guild_alarm_dic[cBOSS_TYPE_DAILY_FIXED]
                # 시각을 key로 하고 값을 해당시간에 뜨는 보스명 list로 하는 dict을 만든다. 하루에 여러번 고정시각이 있을 수 있음.
                for alarm_time, boss_list in alarm_dic.items():
                    guild_daily_fiexed_alarm_dic[alarm_time] = boss_list
                self.cog.logger.info(f"{self.cog.all_alarm_dic}")
                self.cog.logger.info(f"{json.dumps(self.cog.all_alarm_dic, indent=4, ensure_ascii=False)}")
                # TODO: 여기에 이 길드의 월드보탐 상태를 firestore에 저장하는 코드 넣어야 함.(이 앱이 종료되었다가 다시 실행되어도 유지될 수 있도록)
                message = u"월드보탐 알람을 등록하였습니다.\n"
                for time, bosslist in guild_daily_fiexed_alarm_dic.items():
                    message += f"{time} : {', '.join(bosslist)}\n"
                message = message[:-1]
                await interaction.response.send_message(f"{message}")

            @discord.ui.button(label="끄기", style=discord.ButtonStyle.red, disabled=not is_on)
            async def world_boss_alarm_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                '''
                월드보탐 명령어의 reaction으로 나오는 끄기 버튼을 눌렀을 때 실행되는 함수이다.
                Alarm Cog 객체 안의 all_alarm_dic dict에 이 길드의 월드보스 alarm_dic을 지운다.
                :param interaction:
                :param button:
                :return:
                '''
                # self.cog.logger.info(f"{self.cog.all_alarm_dic}")
                # # 전체 알람 dict에서 이 길드에 대한 알람 dict를 가져옴
                if ctx.guild.id not in self.cog.all_alarm_dic:
                    await interaction.response.send_message(f"설정된 알람이 없습니다.")
                    return
                guild_alarm_dic = self.cog.all_alarm_dic[ctx.guild.id]
                # 길드알람 dict에 cBOSS_TYPE_DAILY_FIXED를 키로 하는 dict를 지운다.
                guild_alarm_dic.pop(cBOSS_TYPE_DAILY_FIXED)
                self.cog.logger.info(f"{self.cog.all_alarm_dic}")
                self.cog.logger.info(f"{json.dumps(self.cog.all_alarm_dic, indent=4, ensure_ascii=False)}")
                # TODO: 여기에 이 길드의 월드보탐 상태를 firestore에 저장하는 코드 넣어야 함.(이 앱이 종료되었다가 다시 실행되어도 유지될 수 있도록)
                await interaction.response.send_message(u"월드보탐 알람을 삭제하였습니다.")

        view = Buttons(self)
        await ctx.reply(view_message, view=view)

        # 명령어 형식이 맞는지 검사
        # if len(args) != 1 or args[0].lower() not in {'on', 'off', u"켜기", u"끄기"}:
        #     await ctx.reply(f"사용법 : .{cBOTAM_WORLDBOSS_ONOFF} on/off\n"
        #                     f"사용법 : .{cBOTAM_WORLDBOSS_ONOFF} 켜기/끄기\n")
        #     return
        # self.logger.debug(f"{cBOTAM_WORLDBOSS_ONOFF} : 명령어 갯수 통과")
        # if args[0].lower() in {"on", u"켜기"}:
        #     pass
        # elif args[0].lower() in {"off", u"끄기"}:
        #     pass
        # else:
        #     await ctx.reply(f"사용법 : .{cBOTAM_WORLDBOSS_ONOFF} on/off\n"
        #                     f"사용법 : .{cBOTAM_WORLDBOSS_ONOFF} 켜기/끄기\n")
        #     return
        # alarm_dict = self.db.get_daily_fixed_boss_alarm_dict()
        # self.logger.info(alarm_dict)
        # await ctx.reply(f"{alarm_dict} 이것을 처리할 것입니다....")

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

    async def do_check_alarm(self):
        # self.logger.info(f"do_check_alram")
        # self.count += 1
        # ch = self.bot.get_channel(1074532061223845951)
        # await ch.send(f'{self.count} : test')
        pass

    @tasks.loop(seconds=10, count=100)
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
        # self.logger.info(f"after_send_messag")
        if self.check_alarms.is_being_cancelled() and True:
            pass
            # TODO: alarm dic에 데이타가 남아 있으면 서버에 업로드하는 과정?


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup Alarm Cog")
    await bot.add_cog(Alarm(bot))
