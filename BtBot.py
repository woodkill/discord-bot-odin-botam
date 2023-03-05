import os
import logging.config
import BtDb
from common import *

APP_ID_DEV = 1081829204359913542
APP_ID_REAL = 1074530999947493438

class BtBot(commands.Bot):

    def __init__(self):
        self.logger = logging.getLogger('bot')
        self.logger.info('init')
        super().__init__(
            command_prefix = cPREFIX,
            intents = discord.Intents.all(),
            sync_command = True,
            application_id = APP_ID_DEV if os.getenv("BUILD_FOR") == 'dev' else APP_ID_REAL
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
        # for test
        self.logger.info('bot init complete')

    async def setup_hook(self):
        self.logger.info("setup_hook")
        for ext in self.initial_extension:
            await self.load_extension(ext)
        # await bot.tree.sync(guild=Object(id=))
        await self.tree.sync()

    async def on_ready(self):
        # 서버 DB에서 이봇을 사용하고 있는 길드정보 및 알람정보 로딩
        success, odin_guilds_dic = self.db.get_all_odin_guilds_info()
        if success:
            self.odin_guilds_dic = odin_guilds_dic
        # self.logger.info(f"{self.odin_guilds_dic}")
        # await self.change_presence(status=Status.online, activity=game)
        self.logger.info(f"{self.user} 준비되었습니다.")

    async def on_guild_join(self, guild):
        self.logger.info(f"{guild.name} 서버에 조인하였습니다.")
        # 개발봇, 리얼봇 같은 DB를 쓰기때문에 리얼DB가 지워져서 막았음.
        # self.update_guild_info(guild.id, {})
        # self.logger.info(f"{self.odin_guilds_dic}")

    async def on_guild_remove(self, guild):
        self.logger.info(f"{guild.name} 서버에서 추방되었습니다.")
        # 개발봇, 리얼봇 같은 DB를 쓰기때문에 리얼DB가 지워져서 막았음.
        # self.db.remove_odin_guild_info(guild.id)
        # del self.odin_guilds_dic[guild.id]
        # self.logger.info(f"{self.odin_guilds_dic}")

    async def on_message(self, message: discord.Message):
        if message.author == self.user: # 이 봇이 보낸 메세지는 무시
            return
        if not message.content.startswith(self.command_prefix): # 명령어가 아닌 경우 무시
            return
        if not self.is_ready_commands(message.content, self.command_prefix): # 명령어 형식이지만 명령어 목록에 없으면...
            await message.channel.send(to_guide_code_block(f"{cMSG_NO_EXISTING_CMD}. '{self.command_prefix}{cCMD_GUILD_HELP}'로 명령어 목록을 참고하세요"))
            return
        await self.process_commands(message)

    def is_ready_commands(self, msg: str, prefix: str) -> bool:
        """

        :param msg:
        :param prefix:
        :return:
        """
        # self.logger.info(msg)
        cmd = msg.split()[0][len(prefix):]
        if cmd not in cUsageDic:
            return False
        return True

    def update_guild_info(self, dicord_guild_id: int, guild_dic: dict):
        self.odin_guilds_dic[dicord_guild_id] = guild_dic
        # self.logger.info(f"{self.odin_guilds_dic}")

    def is_guild_registerd(self, guild_id: int) -> bool:
        if guild_id not in self.odin_guilds_dic:
            return False
        if kFLD_CHANNEL_ID not in self.odin_guilds_dic[guild_id]:
            return False
        return True
