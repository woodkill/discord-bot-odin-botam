from const_key import *

'''
봇
'''
cPREFIX = ".."

'''
보스타입
'''
cBOSS_TYPE_DAILY_FIXED = "0"
cBOSS_TYPE_INTERVAL = "1"
cBOSS_TYPE_WEEKDAY_FIXED = "2"
cKEY_TODAY_SCHDULE_ALARM = "3"  # 이건 보스타입은 아니지만, alarms dict에 보스타입과 유니크하게 자리잡고 들어가야 함.

'''
요일
'''
cWEEKDAYS = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']

'''
명령어
'''
cCMD_GUILD_HELP = u"도움말"
cCMD_GUILD_REGISTER = u"길드등록"
cCMD_GUILD_REGISTER_CHANNEL = u"채널등록"
cCMD_BOSS_INFO = u"보스정보"
cCMD_ALARM_LIST = u"알람목록"
cCMD_ALARM_RESET = u"알람리셋"
cCMD_ALARM_TIMER = u"알람간격"
cCMD_ALARM_DAILY_FIXED_ONOFF = u"월보"
cCMD_ALARM_WEEKDAY_FIXED_ONOFF = u"성채"
cCMD_ALARM_REGISTER = u"필보"
cCMD_ALARM_TIMETABLE = u"시간표"
cCMD_ALARM_TODAY = u"오늘"
cCMD_LOTTERY_CULCHECK = u"출첵"

cCMD_PARAM_OFF = u"끄기"

cUsageDic = {
    cCMD_GUILD_HELP:                {kCMD_USAGE: f"{cCMD_GUILD_HELP}  ***[ 명령어(옵션) ]***", kCMD_EXPLANATION: u"명령어의 간략한 사용법"},
    cCMD_GUILD_REGISTER:            {kCMD_USAGE: f"{cCMD_GUILD_REGISTER}  ***[ 오딘서버명  길드명 ]***", kCMD_EXPLANATION: u"이 디코가 어떤 길드용인지 등록/확인"},
    cCMD_GUILD_REGISTER_CHANNEL:    {kCMD_USAGE: f"{cCMD_GUILD_REGISTER_CHANNEL}", kCMD_EXPLANATION: u"이 채널을 봇이 주는 알람용 채널로 설정"},
    cCMD_BOSS_INFO:                 {kCMD_USAGE: f"{cCMD_BOSS_INFO}  ***[ 보스(별)명 ]***", kCMD_EXPLANATION: u"지목한 보스의 정보 또는 전체 목록을 보여줌"},
    cCMD_ALARM_LIST:                {kCMD_USAGE: f"{cCMD_ALARM_LIST}", kCMD_EXPLANATION: u"현재 설정되어 있는 알람 목록을 보여줌"},
    cCMD_ALARM_RESET:               {kCMD_USAGE: f"{cCMD_ALARM_RESET}", kCMD_EXPLANATION: u"설정되어 모든 알람을 지움"},
    cCMD_ALARM_TIMER:               {kCMD_USAGE: f"{cCMD_ALARM_TIMER}  ***[ 분  분  분  ... ]***", kCMD_EXPLANATION: u"보스출현 몇분 전에 알람을 받을지 지정(여러개 가능)"},
    cCMD_ALARM_DAILY_FIXED_ONOFF:   {kCMD_USAGE: f"{cCMD_ALARM_DAILY_FIXED_ONOFF}", kCMD_EXPLANATION: f"{cCMD_ALARM_DAILY_FIXED_ONOFF} 알람 ON / OFF"},
    cCMD_ALARM_WEEKDAY_FIXED_ONOFF: {kCMD_USAGE: f"{cCMD_ALARM_WEEKDAY_FIXED_ONOFF}", kCMD_EXPLANATION: f"{cCMD_ALARM_WEEKDAY_FIXED_ONOFF} 알람 ON / OFF"},
    cCMD_ALARM_REGISTER:            {kCMD_USAGE: f"{cCMD_ALARM_REGISTER}  ***보스명  [ 남은시간  |  끄기 ]***", kCMD_EXPLANATION: f"{cCMD_ALARM_REGISTER} 알람 추가/삭제"},
    cCMD_ALARM_TIMETABLE:           {kCMD_USAGE: f"{cCMD_ALARM_TIMETABLE}", kCMD_EXPLANATION: f"보스 시간표 이미지 첨부로 알람시간 자동인식"},
    cCMD_ALARM_TODAY:               {kCMD_USAGE: f"{cCMD_ALARM_TODAY}  ***알람명  [ 시각:분  |  끄기 ]***", kCMD_EXPLANATION: f"원하는 이름의 알람을 설정(금일스케쥴용)"},
    cCMD_LOTTERY_CULCHECK:          {kCMD_USAGE: f"{cCMD_LOTTERY_CULCHECK}  ***보스명***", kCMD_EXPLANATION: f"보탐 참여자 출석체크. 지각생도 추가 가능"},
}

'''
메세지
'''
cMSG_REGISTER_GUILD_FIRST = u"먼저 길드등록을 하여야 합니다."
cMSG_NO_GUILD_INFO = u"길드정보가 없습니다."
cMSG_NO_EXISTING_CMD = "그런 명령어는 없습니다."

cLIST_DEFAULT_TIMERS = [15, 5, 1]

'''
'''
cOCR_IGNORE_NAMES = ['현재 시간', '노른의 시간표', '미드가르드', '요툰하임', '니다벨리르', '던전', '거점 지배자', '절대자', '대륙 침략자', '발할라 대전']

