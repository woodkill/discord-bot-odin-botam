import os
import logging
import BtBot

logging.config.fileConfig("logging.conf")
bot = BtBot.BtBot()
bot.run(os.getenv("DISCORD_ODIN_BOTAM_TOKEN"))

# TODO : 시간표 첨부화일 화일에서 날짜 가져오기
# TODO : 출첵
# TODO : 뽑기
# TODO : 보스알람에 이미지 넣기