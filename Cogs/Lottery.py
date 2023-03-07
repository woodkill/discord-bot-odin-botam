import logging
from discord.ext import commands

import datetime

import BtBot
import BtDb

from common import *
from const_data import *

cTIME_FORMAT_CHULCHECK_KEY = "%Y-%m-%d"


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

        # 첫번째 인자가 보스명인지 검사
        arg_boss_name = args[0]
        boss_key, boss = self.db.get_boss_item_by_name(args[0])
        if boss_key is None:
            await send_error_message(ctx, f"{arg_boss_name} : 존재하지 않는 보스명입니다.")
            return
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
        str_now_date = datetime.datetime.now().date().strftime(cTIME_FORMAT_CHULCHECK_KEY)
        guild_id = ctx.guild.id

        # 먼저 오늘 날짜의 해당 보스명 출첵이 있으면 받아오고 없으면 만든다.
        chulcheck_dict = self.db.get_chulcheck(guild_id, str_now_date, boss_name)
        if chulcheck_dict is None:
            chulcheck_dict = self.db.add_chulcheck(guild_id, str_now_date, boss_name, [])

        self.logger.debug(chulcheck_dict)

        class Buttons(discord.ui.View):
            def __init__(self, bot: BtBot, timeout=180):
                self.bot = bot
                self.logger = logging.getLogger('bot.lottery')
                super().__init__(timeout=timeout)

            @discord.ui.button(label="출석", style=discord.ButtonStyle.blurple)
            async def chulcheck_on(self, interaction: discord.Interaction, button: discord.ui.Button, ):
                guild_member_name = interaction.user.name
                chulcheck_dict[kFLD_CC_MEMBERS].append(guild_member_name)
                on_members = set(chulcheck_dict[kFLD_CC_MEMBERS])
                str_on_members = ", ".join(on_members)
                await interaction.response.Ï(content=f"```{on_members}```")

            @discord.ui.button(label="빼줘", style=discord.ButtonStyle.red)
            async def chulcheck_off(self, interaction: discord.Interaction, button: discord.ui.Button, ):

                pass

        view = Buttons(self.bot)
        members = set(chulcheck_dict[kFLD_CC_MEMBERS])
        str_members = ", ".join(members)
        await ctx.channel.send(f"```{str_members}```", view=view)


async def setup(bot: BtBot) -> None:
    logging.getLogger('bot.lottery').info(f"setup Lottery Cog")
    await bot.add_cog(Lottery(bot))
