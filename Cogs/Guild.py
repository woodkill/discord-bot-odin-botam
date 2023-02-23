import discord
import logging
from discord.ext import commands
from discord import app_commands
# from discord import Interaction
# from discord import Object
from const_key import *
from const_data import *
import BtBot
import btdb


class Guild(commands.Cog):

    def __init__(self, bot: BtBot) -> None:
        self.bot = bot
        self.db: btdb.BtDb = bot.db
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

    @commands.command(name=cGUILD_REGISTER)
    async def register_guild(self, ctx: commands.Context, *args) -> None:
        '''
        "길드등록" 명령어를 처리한다.
        :param ctx: context
        :param args: 오딘서버명, 길드명
        :return: 없음
        '''
        self.logger.info(f"{cGUILD_REGISTER} {args}")
        if len(args) != 2:
            await ctx.reply(f"사용법 : .{cGUILD_REGISTER} ***오딘서버명 길드명***")
            return
        odin_server_name = args[0]
        odin_guild_name = args[1]
        if not self.db.check_valid_server_name(odin_server_name):
            await ctx.reply(f"올바른 오딘서버명이 아닙니다 : '{odin_server_name}'")
            return
        success = self.db.set_odin_guild_info(ctx.guild.id, ctx.channel.id, odin_server_name, odin_guild_name)
        if not success:
            await ctx.reply(f"길드등록에 실패하였습니다.")
            return
        await ctx.reply(f"길드등록 완료 : {odin_server_name}/{odin_guild_name}\n"
                        f"앞으로 오딘보탐의 알람은 이 채널을 이용합니다.")
        self.bot.update_guild_info(ctx.guild.id, {
            kFLD_CHANNEL_ID: ctx.channel.id,
            kFLD_SERVER_NAME: odin_server_name,
            kFLD_GUILD_NAME: odin_guild_name
        })

    @commands.command(name=cGUILD_CONFIRM)
    async def check_guild(self, ctx: commands.Context) -> None:
        '''
        "길드확인" 명령어를 처리한다.
        :param ctx: context
        :return: 없음
        '''
        self.logger.info(f"{cGUILD_CONFIRM}")
        success, odin_guild_dic = self.db.get_odin_guild_info(ctx.guild.id)
        if success:
            await ctx.reply(f"{odin_guild_dic[kFLD_SERVER_NAME]}/{odin_guild_dic[kFLD_GUILD_NAME]}")
        else:
            await ctx.reply(f"등록된 길드가 없습니다.")

    @commands.command(name=cGUILD_REGISTER_CHANNEL)
    async def register_alarm_channel(self, ctx: commands.Context) -> None:
        self.logger.info(f"{cGUILD_REGISTER_CHANNEL}")
        # 먼저 길드등록이 되어 있는 지 검사
        if not self.bot.is_guild_registerd(ctx.guild.id):
            await ctx.reply(cMSG_REGISTER_GUILD_FIRST)
            return
        success = self.db.set_odin_guild_register_alarm_channel(ctx.guild.id, ctx.channel.id)
        if success:
            await ctx.reply(f"앞으로 오딘보탐의 알람은 이 채널을 이용합니다.")
        else:
            await ctx.reply(f"{cGUILD_REGISTER_CHANNEL} 실패하였습니다.")


async def setup(bot: commands.Bot) -> None:
    logging.getLogger('cog').info(f"setup Guild Cog")
    await bot.add_cog(Guild(bot))
