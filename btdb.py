import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from functools import cmp_to_key
import logging
from const_key import *
from const_data import *

class BtDb():

    def __init__(self):
        # Use a service account.
        self.cred = credentials.Certificate('firebase.json')
        self.app = firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        # logger setting
        self.logger = logging.getLogger('db')
        # master data storage
        self.serverDic: dict = {}
        self.bossDic: dict = {}
        # initialize
        self.load_server_dic()
        self.load_boss_dic()
        self.logger.info(f"btdb init complete")

    def load_server_dic(self) -> bool:
        '''
        서버DB에서 오딘 서버목록을 쿼리하여 self.serverSet에 저장
        :return: 성공여부
        '''
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODIN_SERVER).get()
        server_dic = doc.to_dict()
        # self.logger.info(f"오딘서버목록 로딩 완료 : {server_dic}")
        self.serverDic = server_dic
        return True

    def load_boss_dic(self) -> bool:
        '''
        서버DB에서 오딘의 보스정보를 쿼리하여 self.bossDic에 저장
        :return: 성공여부
        '''
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODIN_BOSS).get()
        boss_dic = doc.to_dict()
        # self.logger.info(f"오딘보스목록 로딩 완료 : {boss_dic}")
        self.bossDic = boss_dic
        return True

    def check_valid_server_name(self, odin_server_name: str) -> bool:
        '''
        오딘서버명 진위 여부 판단
        :param odin_server_name: 검사할 오딘 서버명
        :return: odin_server_name 과 같은 오딘서버가 있는지 여부
        '''
        r = {server[1][kSERVER_NAME] for server in self.serverDic.items() if server[1][kSERVER_NAME] == odin_server_name}
        self.logger.info(r)
        return len(r) != 0

    def get_odin_guild_info(self, discord_guild_id: int) -> (bool, dict):
        '''
        {discord_guild_id}로 등록된 길드 정보(오딘서버명, 길드명)을 쿼리하여 리턴한다.
        :param discord_guild_id:
        :return: (성공여부, 오딘서버명, 길드명)
        '''
        str_discord_guild_id = str(discord_guild_id)
        doc = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).get()
        if not doc.exists:
            self.logger.info(f"디스코드서버ID:{discord_guild_id} 로 등록된 오딘길드가 없음.")
            return False, None
        odin_guild_dic = doc.to_dict()
        self.logger.info(f"get_odin_guild_info : {odin_guild_dic}")
        return True, odin_guild_dic

    def get_all_odin_guilds_info(self) -> (bool, dict):
        '''

        :return:
        '''
        odin_guilds_dic = {}
        docs = self.db.collection(kCOL_ODINGUILD).stream()
        # self.logger.info(f"{docs}")
        for doc in docs:
            odin_guilds_dic[int(doc.id)] = doc.to_dict()
        self.logger.info(f"{odin_guilds_dic}")
        return True, odin_guilds_dic

    def set_odin_guild_info(self, discord_guild_id: int, channel_id: int, odin_server_name: str, odin_guild_name: str) -> bool:
        '''
        {discord_guild_id}를 document명으로 하여 길드정보를 서버DB에 저장한다.
        :param discord_guild_id: 명령어를 접수한 디코 서버 id
        :param channel_id: 현재 명령어를 접수한 디코 채널 id
        :param odin_server_name: 등록할 오딘서버명
        :param odin_guild_name: 등록할 오딘길드명
        :return: 성공여부
        '''
        str_discord_guild_id = str(discord_guild_id)
        col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).set({
            kFLD_SERVER_NAME: odin_server_name,
            kFLD_GUILD_NAME: odin_guild_name,
            kFLD_CHANNEL_ID: channel_id
            }, merge=True)
        return True

    def remove_odin_guild_info(self, discord_guild_id: int):
        str_discord_guild_id = str(discord_guild_id)
        self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).delete()

    def set_odin_guild_register_alarm_channel(self, discord_guild_id: int, channel_id: int) -> bool:
        '''
        {discord_guild_id}를 document명으로 하여 알람 받을 채널id를 서버DB에 저장한다.
        :param discord_guild_id: 명령어를 접수한 디코 서버 id
        :param channel_id: 명령어를 접수한 디코 채널 id
        :return: 성공여부
        '''
        str_discord_guild_id = str(discord_guild_id)
        col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).set({
            kFLD_CHANNEL_ID: channel_id
        }, merge=True)
        return True

    def get_boss_list(self):
        '''
        보스정보를 key를 제외하고 리스트로 리턴
        :return: 보스정보 dic의 list
        '''
        # self.logger.info(self.bossDic)
        if len(self.bossDic) == 0:
            self.logger.debug(f"self.bossDic 이 비어있습니다.")
            return None
        boss_list = list(self.bossDic.values())
        return sorted(boss_list, key=lambda x: (x[kCHAP_ORDER], x[kBOSS_LEVEL], x[kBOSS_ORDER]))

    def get_boss_item_by_name(self, arg_boss_name: str):
        '''
        메모리에 로딩된 정보로 보스정보 찾아주기
        :param arg_boss_name: 보스명 혹은 보스별명
        :param arg_option_str: 리턴받을 값의 방식을 정하는 옵션
        :return: 찾는 보스가 있을 경우 옵션에 따라 리턴한다.
        'key' :  key문자열
        'name' : 보스명,
        'chapter/name' : 지역명/보스명
        'item' : 보스정보dic
        '''
        self.logger.info(self.bossDic)
        if len(self.bossDic) == 0:
            return None
        # self.bossDic의 보스명과 보스별명을 검사하여 해당 보스키값을 리턴한다.
        for key, item in self.bossDic.items():
            boss_name = item[kBOSS_NAME]
            boss_alias = item[kBOSS_ALIAS]
            if arg_boss_name == boss_name or arg_boss_name in boss_alias:
                return item
        return None

    def get_daily_fixed_boss_alarm_dict(self) -> dict:
        '''
        보스정보 dict에서 고정타임 보스에 해당하는 정보를 찾아서 {시각:[보스명리스트], ...} 형식의 dict로 반환해 준다.
        :return: {시각:[보스명리스트], ...}
        '''
        fixed_boss_dict = {k: v for k, v in self.bossDic.items() if v[kBOSS_TYPE] == cBOSS_TYPE_DAILY_FIXED}
        alarm_dict = {}
        for k, v in fixed_boss_dict.items():
            times = v[kBOSS_FIXED_TIME]
            for time in times:
                if time not in alarm_dict:
                    alarm_dict[time] = []
                alarm_dict[time].append(v[kBOSS_NAME])
        return alarm_dict

    def get_boss_alarm_in_master(self, option: int = cBOSS_TYPE_DAILY_FIXED) -> dict:
        # self.logger.info(f"{self.bossDic}")
        alarm_dic = {}
        for key, boss in self.bossDic.items():
            if boss[kBOSS_TYPE] == cBOSS_TYPE_DAILY_FIXED:
                boss_fixed_time_list = boss[kBOSS_FIXED_TIME]
                for boss_fixed_time in boss_fixed_time_list:
                    if boss_fixed_time not in alarm_dic:
                        alarm_dic[boss_fixed_time] = [boss[kBOSS_NAME]]
                    else:
                        alarm_dic[boss_fixed_time].append(boss[kBOSS_NAME])
        self.logger.info(alarm_dic)
        return alarm_dic

    #
    # def delete_boss_collection(self, discord_guild_id, col_ref, batch_size):
    #     docs = col_ref.list_documents(page_size=batch_size)
    #     deleted = 0
    #     for doc in docs:
    #         self.logger.info(f"Deleting doc {doc.id} => {doc.get().to_dict()}")
    #         doc.delete()
    #         deleted = deleted + 1
    #     if deleted >= batch_size:
    #         return delete_boss_collection(self, discord_guild_id, col_ref, batch_size)
    #
    # def reset_boss(self, discord_guild_id):
    #     str_discord_guild_id = str(discord_guild_id)
    #     doc = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).get()
    #     success = False
    #     message_str = f'등록된 길드가 없어서 보스 리셋을 할 수 없습니다.'
    #     if not doc.exists:
    #         return False
    #     col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).collection(kCOL_BOSS)
    #     self.delete_boss_collection(self, discord_guild_id, col_ref, 10)
    #     message_temp = f''
    #     for key in cDIC_BOSS_INFO:
    #         col_ref.document(key).set(cDIC_BOSS_INFO[key])
    #         message_temp += f'{cCHAP_NAME[cDIC_BOSS_INFO[key][kCHAP_NO]]}/{key}\n'
    #     success = True
    #     message_str = message_temp + f'\n총 {len(cDIC_BOSS_INFO)}개 보스 목록을 리셋하였습니다.'
    #     return (success, message_str)
