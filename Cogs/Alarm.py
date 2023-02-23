import discord
import asyncio
import logging
from discord.ext import commands, tasks
from discord import app_commands
# from discord import Interaction
# from discord import Object
from const_key import *
from const_data import *
import BtBot
import btdb


class Alarm(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot = bot
        self.db: btdb.BtDb = bot.db
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

    @commands.command(name=cBOTAM_WORLDBOSS_ONOFF)
    async def onoff_world_boss_alarm(self, ctx: commands.Context) -> None:
        '''
        월드보탐 온/오프 기능
        :param ctx: Context
        :param args: args[0] "켜기" 혹은 "끄기"
        :return:
        '''
        logging.info(f"{cBOTAM_WORLDBOSS_ONOFF}")
        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await ctx.reply(cMSG_REGISTER_GUILD_FIRST)
            return

        class Buttons(discord.ui.View):
            def __init__(self, cog: commands.Cog, timeout=180):
                self.cog: Alarm = cog
                super().__init__(timeout=timeout)

            @discord.ui.button(label="켜기", style=discord.ButtonStyle.blurple)
            async def world_boss_alarm_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                # self.cog.logger.info(f"{self.cog.alarm_dic}")
                alarm_dic = self.cog.db.get_boss_alarm_in_master()
                if len(alarm_dic) > 0:
                    if ctx.guild.id not in self.cog.all_alarm_dic:
                        self.cog.all_alarm_dic[ctx.guild.id] = {}
                    guild_alarm_dic = self.cog.all_alarm_dic[ctx.guild.id]
                    for alarm_time, boss_list in alarm_dic.items():
                        guild_alarm_dic[alarm_time] = boss_list
                self.cog.logger.info(f"{self.cog.all_alarm_dic}")
                await interaction.response.send_message(f"켜기를 눌렀습니다.")

            @discord.ui.button(label="끄기", style=discord.ButtonStyle.red)
            async def world_boss_alarm_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                await interaction.response.send_message(f"끄기를 눌렀습니다.")

        view = Buttons(self)
        await ctx.reply(f"현재 월드보탐 알람은 On입니다.", view=view)

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

    @tasks.loop(seconds=2, count=100)
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
            # alarm dic에 데이타가 남아 있으면 서버에 업로드하는 과정?


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup Alarm Cog")
    await bot.add_cog(Alarm(bot))