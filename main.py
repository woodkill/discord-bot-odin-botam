import os
import logging
import BtBot

logging.config.fileConfig("logging.conf")
bot = BtBot.BtBot()
bot.run(os.getenv("DISCORD_ODIN_BOTAM_TOKEN"))
