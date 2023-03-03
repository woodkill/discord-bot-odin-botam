import discord
import logging
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object
from const_key import *
from const_data import *
from common import *
import BtBot
import BtDb


class Guild(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot = bot
        self.db: BtDb.BtDb = bot.db
        self.logger = logging.getLogger('cog')

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        self.logger.info(f"Guild Cog loaded.")

    # / command를 등록하는 코드같음
    # @commands.command(name='sync')
    # async def sync(self, ctx) -> None:
    #     fmt = await ctx.bot.tree.sync(guild=ctx.guild)
    #     await ctx.send(f'Synced {len(fmt)} commands')

    # @app_commands.command(name='sample', description=u"테스트")
    # async def hello(self, interaction: discord.Interaction, hello: str):
    #     await interaction.response.send_message('Answered')

    @commands.command(name=cCMD_GUILD_HELP)
    async def help(self, ctx: commands.Context, *args) -> None:
        '''

        :param ctx:
        :param arg:
        :return:
        '''
        self.logger.info(f"{cCMD_GUILD_HELP} {args} by {ctx.message.author}")

        if len(args) == 0:
            await ctx.send(embed=get_help_list_embed())
            return
        else:
            if args[0] not in cUsageDic:
                await send_guide_message(cMSG_NO_EXISTING_CMD)
            else:
                await send_usage_embed(ctx, args[0])

    @commands.command(name=cCMD_GUILD_REGISTER)
    async def check_guild(self, ctx: commands.Context, *args) -> None:
        '''
        "길드확인" 명령어를 처리한다.
        :param ctx: context
        :param args:
        :return: 없음
        '''
        self.logger.info(f"{cCMD_GUILD_REGISTER} {args} by {ctx.message.author}")

        # 명령어 형식이 맞는지 검사
        if len(args) > 2 or len(args) == 1: # 인자가 없거나 2개이어야 함
            await send_usage_embed(ctx, cCMD_GUILD_REGISTER)
            return
        # self.logger.debug(f"{cCMD_GUILD_REGISTER} 명령어 갯수 통과")

        if len(args) == 0:  # 길드확인용으로 쓰이는 경우
            success, odin_guild_dic = self.db.get_odin_guild_info(ctx.guild.id)
            if not success:
                await send_error_message(ctx, f"등록된 길드가 없습니다.")
                return
            await send_ok_embed(ctx, f"이 디코서버는 {odin_guild_dic[kFLD_SERVER_NAME]} / {odin_guild_dic[kFLD_GUILD_NAME]} 길드로 등록되어 있습니다.")
            return

        # 여기부터 인자가 2개 들어온 경우
        odin_server_name = args[0]
        odin_guild_name = args[1]

        if not self.db.check_valid_server_name(odin_server_name):
            await send_error_message(ctx, f"'{odin_server_name}' : 올바른 오딘서버명이 아닙니다")
            return
        success, guild_info = self.db.set_odin_guild_info(ctx.guild.id, ctx.channel.id, odin_server_name, odin_guild_name)
        if not success:
            await send_error_message(ctx, f"길드등록에 실패하였습니다.")
            return
        self.bot.update_guild_info(ctx.guild.id, guild_info)
        await send_ok_message(ctx, f"길드등록 완료 : {odin_server_name} / {odin_guild_name}\n앞으로 오딘보탐의 알람은 이 채널을 이용합니다.")

    @commands.command(name=cCMD_GUILD_REGISTER_CHANNEL)
    async def register_alarm_channel(self, ctx: commands.Context) -> None:
        """

        :param ctx:
        :return:
        """
        self.logger.info(f"{cCMD_GUILD_REGISTER_CHANNEL} by {ctx.message.author}")

        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await send_guide_message(ctx, cMSG_REGISTER_GUILD_FIRST)
            return
        success = self.db.set_odin_guild_register_alarm_channel(ctx.guild.id, ctx.channel.id)
        if not success:
            await send_error_message(ctx, f"{cCMD_GUILD_REGISTER_CHANNEL} 실패하였습니다.")
            return
        await send_ok_message(ctx, f"앞으로 오딘보탐의 알람은 이 채널을 이용합니다.")


async def setup(bot: BtBot) -> None:
    logging.getLogger('cog').info(f"setup Guild Cog")
    await bot.add_cog(Guild(bot))
