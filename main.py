import os
import logging
import logging.config
import discord
from discord.ext import commands
# from discord import Intents
# from discord import Game
# from discord import Status
# from discord import Object
import btdb

# logger = logging.getLogger('OdinBotam')
# logging.basicConfig(level=logging.INFO)


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
            "Cogs.Guild"
        ]
        self.db = btdb.BtDb()
        self.logger.info('bot init complete')

    async def setup_hook(self):
        self.logger.info("setup_hook")
        for ext in self.initial_extension:
            await self.load_extension(ext)
        # await bot.tree.sync(guild=Object(id=))
        await bot.tree.sync()

    async def on_ready(self):
        self.logger.info(f"{self.user} 준비되었습니다.")
        # game = Game("....")
        # await self.change_presence(status=Status.online, activity=game)

    # async def on_message(self, message):
    #     await self.process_commands(message)
    #     if message.content[0] == self.command_prefix:
    #         return
    #     if message.author == self.user:
    #         return
    #     await message.channel.send(f'네 듣고 있어요.')


logging.config.fileConfig("logging.conf")
bot = BtBot()
bot.run(os.getenv("DISCORD_ODIN_BOTAM_TOKEN"))
