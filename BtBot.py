import logging.config
import discord
from discord.ext import commands
# from discord import Intents
# from discord import Game
# from discord import Status
# from discord import Object
import BtDb
from const_key import *


class BtBot(commands.Bot):

    def __init__(self):
        self.logger = logging.getLogger('bot')
        self.logger.info('init')
        super().__init__(
            command_prefix='.',
            intents=discord.Intents.all(),
            sync_command=True,
            application_id=1074530999947493438
        )
        self.initial_extension = [
            "Cogs.Guild",
            "Cogs.Boss",
            "Cogs.Alarm"
        ]
        # firestore access
        self.db = BtDb.BtDb()
        # working data storage
        self.odin_guilds_dic = {}
        self.logger.info('bot init complete')

    async def setup_hook(self):
        self.logger.info("setup_hook")
        for ext in self.initial_extension:
            await self.load_extension(ext)
        # await bot.tree.sync(guild=Object(id=))
        await self.tree.sync()

    async def on_ready(self):
        self.logger.info(f"{self.user} 준비되었습니다.")
        success, odin_guilds_dic = self.db.get_all_odin_guilds_info()
        if success:
            self.odin_guilds_dic = odin_guilds_dic
        # self.logger.info(f"{self.odin_guilds_dic}")

        # game = Game("....")
        # await self.change_presence(status=Status.online, activity=game)

    async def on_guild_join(self, guild):
        self.logger.info(f"{guild.name} 서버에 조인하였습니다.")
        self.update_guild_info(guild.id, {})
        # self.logger.info(f"{self.odin_guilds_dic}")

    async def on_guild_remove(self, guild):
        self.logger.info(f"{guild.name} 서버에서 추방되었습니다.")
        self.db.remove_odin_guild_info(guild.id)
        del self.odin_guilds_dic[guild.id]
        # self.logger.info(f"{self.odin_guilds_dic}")

    def update_guild_info(self, dicord_guild_id: int, guild_dic: dict):
        self.odin_guilds_dic[dicord_guild_id] = guild_dic
        # self.logger.info(f"{self.odin_guilds_dic}")

    def is_guild_registerd(self, guild_id: int) -> bool:
        if guild_id not in self.odin_guilds_dic:
            return False
        if kFLD_CHANNEL_ID not in self.odin_guilds_dic[guild_id]:
            return False
        return True

    # def check_guild(self, guild_id:int):

    # async def on_message(self, message):
    #     await self.process_commands(message)
    #     if message.content[0] == self.command_prefix:
    #         return
    #     if message.author == self.user:
    #         return
    #     await message.channel.send(f'네 듣고 있어요.')