import logging
import asyncio
import discord
from discord.ext import commands, tasks
# from nextcord import app_commands
# from discord import Interaction
# from discord import Object
import BtBot
import BtDb
from const_key import *
from const_data import *
from common import *


class Boss(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Boss Cog loaded.")

    @commands.command(name=cCMD_BOSS_INFO)
    async def info_boss(self, ctx: commands.Context, *args) -> None:
        '''
        보스정보를 보여준다.
        :param ctx: context
        :param args: args[0] : 보스명
        :return: None
        '''
        self.logger.info(f"{cCMD_BOSS_INFO} {args}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return

        # 명령어 형식이 맞는지 검사
        if len(args) > 1:
            await send_usage_embed(ctx, cCMD_BOSS_INFO)
            return
        # self.logger.debug(f"{cCMD_BOSS_INFO} 명령어 갯수 통과")

        if len(args) == 0: # 보스명을 인자로 달지 않은 경우
            boss_list = self.db.get_boss_list() # 보스정보를 소팅해서 받는다.
            if boss_list is None:
                await send_error_message(ctx, f"보스정보가 없습니다. 관리자에게 문의하세요.")
            embed = discord.Embed(title=f"보스목록", description=f"모든 보스의 간략한 정보입니다.", color=discord.Color.purple())
            for boss in boss_list:
                str_boss_alias = ",".join(boss[kBOSS_ALIAS])
                embed.add_field(name=boss[kBOSS_NAME],
                                value=f"{boss[kCHAP_NAME]} / {boss[kBOSS_LEVEL]}\n별명 : {str_boss_alias}", inline=False)
            await ctx.send(embed=embed)
            return

        # 보스명이 인자로 넘어온 경우 : 보스명에 해당하는 보스정보 가져오기
        odin_boss_name = args[0]
        boss_key, boss_dic = self.db.get_boss_item_by_name(odin_boss_name)

        # 보스 타입에 따라 보스정보 표시 문자열을 만든다.
        boss_type = boss_dic[kBOSS_TYPE]
        str_boss_apperance = ""
        if boss_type == cBOSS_TYPE_INTERVAL:
            boss_interval = boss_dic[kBOSS_INTERVAL]
            d, h, m, s = get_separated_timedelta_ddhhmm(boss_interval)
            str_interval = ""
            if d > 0:
                str_interval += f"{d}일"
            if h > 0:
                str_interval += f"{h}시간"
            if m > 0:
                str_interval += f"{m}분"
            if s > 0:
                str_interval += f"{s}초"
            str_boss_apperance = f"컷 후 {str_interval} 뒤에 젠"
        elif boss_type == cBOSS_TYPE_DAILY_FIXED:
            boss_fiexed_time_list = boss_dic[kBOSS_FIXED_TIME]
            str_times = ', '.join(boss_fiexed_time_list)
            str_boss_apperance = f"매일 {str_times} 젠"
        elif boss_type == cBOSS_TYPE_WEEKDAY_FIXED:
            boss_weektime_list = boss_dic[kBOSS_WEEKDAY_INFO]
            str_weektime_list = []
            for boss_weektime_info in boss_weektime_list:
                weekday_index = boss_weektime_info[kBOSS_WEEKDAY]
                str_weekday = cWEEKDAYS[weekday_index]
                str_appearance_time = boss_weektime_info[kBOSS_APPEARANCE_TIME]
                str_weektime_list.append(f"{str_weekday} {str_appearance_time}")
            str_weektimes = ', '.join(str_weektime_list)
            str_boss_apperance = f"매주 {str_weektimes} 젠"

        str_boss_type = {
            cBOSS_TYPE_INTERVAL: f"인터벌",
            cBOSS_TYPE_WEEKDAY_FIXED: f"특정요일, 특정시간",
            cBOSS_TYPE_DAILY_FIXED: f"매일 같은 시간"

        }.get(boss_type, f"알 수 없는 보스타입")

        file = discord.File(f"./Images/{boss_key}.png", filename=f"{boss_key}.png")
        embed = discord.Embed(title=boss_dic[kBOSS_NAME], color=discord.Color.purple())
        embed.set_thumbnail(url=f"attachment://{boss_key}.png")
        # embed.set_image(url=f"attachment://{boss_key}.png")
        embed.add_field(name="지역", value=boss_dic[kCHAP_NAME], inline=False)
        embed.add_field(name="종류", value=boss_dic[kBOSS_LEVEL], inline=False)
        embed.add_field(name="별명", value=', '.join(boss_dic[kBOSS_ALIAS]), inline=False)
        embed.add_field(name="타입", value=str_boss_type, inline=False)
        embed.add_field(name="출현", value=str_boss_apperance, inline=False)
        await ctx.send(file=file, embed=embed)

    @commands.command(name=cCMD_BOSS_ADD_ALIAS)
    async def register_alias_boss(self, ctx: commands.Context, *args) -> None:
        '''
        TODO : 3 이 봇을 여러개의 길드가 사용할 경우 추가한 보스별명이 다른 길드에는 영향이 가지 않도록 구현해야 한다. 다시 생각해 보도록...
        :param ctx: Context
        :param args:
        :return:
        '''
        self.logger.info(f"{cCMD_BOSS_ADD_ALIAS} {args}")
        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return
        # 명령어 형식이 맞는지 검사
        if len(args) != 2:
            await send_usage_embed(ctx, cCMD_BOSS_ADD_ALIAS, additional=f"추가할 별명은 기존에 사용하고 있지 않아야 합니다.")
            return
        self.logger.debug(f"{cCMD_BOSS_ADD_ALIAS} 명령어 갯수 통과")
        # 앞의 보스명은 보스명이나 별명에 있어야 하고 뒤의 보스별명은 기존에 없어야 한다.
        # TODO: 3 마저 구현해야 한다.
        str_exist_boss_name = args[0]
        boss_key, exist_boss_dic = self.db.get_boss_item_by_name(str_exist_boss_name)

        str_new_boss_alias = args[1]

        await ctx.reply(f"{cCMD_BOSS_ADD_ALIAS} 구현중...")


async def setup(bot: BtBot) -> None:
    logging.getLogger('cog').info(f"setup Boss Cog")
    await bot.add_cog(Boss(bot))
