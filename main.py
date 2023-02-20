import os
# import logging
import discord
from discord.ext import commands
# from discord import Intents
# from discord import Game
# from discord import Status
# from discord import Object

# logger = logging.getLogger('OdinBotam')
# logging.basicConfig(level=logging.INFO)


class OdinBotamBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix='.',
            intents=discord.Intents.all(),
            sync_command=True,
            application_id=1074530999947493438
        )
        self.initial_extension = [
            "Cogs.Guild"
        ]

    async def setup_hook(self):
        for ext in self.initial_extension:
            await self.load_extension(ext)
        # await bot.tree.sync(guild=Object(id=))
        await bot.tree.sync()

    async def on_ready(self):
        print(f"{self.user} 준비되었습니다.")
        # logger.info(f"OdinBotam loaded")
        # game = Game("....")
        # await self.change_presence(status=Status.online, activity=game)

    # async def on_message(self, message):
    #     await self.process_commands(message)
    #     if message.content[0] == self.command_prefix:
    #         return
    #     if message.author == self.user:
    #         return
    #     await message.channel.send(f'네 듣고 있어요.')


bot = OdinBotamBot()
bot.run(os.getenv("DISCORD_ODIN_BOTAM_TOKEN"))
