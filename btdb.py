import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from functools import cmp_to_key
import logging
from const_key import *


class BtDb():

    def __init__(self):
        # Use a service account.
        self.cred = credentials.Certificate('firebase.json')
        self.app = firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        # logger setting
        self.logger = logging.getLogger('db')
        # data storage
        self.serverSet = {}
        self.bossDic = {}
        # initialize
        self.load_server_list()
        self.load_boss_dic()

    def load_server_list(self) -> bool:
        '''
        서버DB에서 오딘 서버목록을 쿼리하여 self.serverSet에 저장
        :return: 성공여부
        '''
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODINDATA).get()
        server_list = doc.to_dict()[kFLD_SERVER_LIST]
        self.logger.info(f"오딘서버목록 로딩 완료 : {server_list}")
        self.serverSet = set(server_list)
        return True

    def load_boss_dic(self) -> bool:
        '''
        서버DB에서 오딘의 보스정보를 쿼리하여 self.bossDic에 저장
        :return: 성공여부
        '''
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODINDATA).get()
        boss_dic = doc.to_dict()[kFLD_BOSS_DIC]
        self.logger.info(f"오딘보스목록 로딩 완료 : {boss_dic}")
        self.bossDic = boss_dic
        return True

    def check_valid_server_name(self, odin_server_name: str) -> bool:
        '''
        오딘서버명 진위 여부 판단
        :param odin_server_name: 검사할 오딘 서버명
        :return: odin_server_name 과 같은 오딘서버가 있는지 여부
        '''
        return odin_server_name in self.serverSet

    def get_odin_guild_info(self, discord_guild_id: int) -> (bool, str, str):
        '''
        {discord_guild_id}로 등록된 길드 정보(오딘서버명, 길드명)을 쿼리하여 리턴한다.
        :param discord_guild_id:
        :return: (성공여부, 오딘서버명, 길드명)
        '''
        str_discord_guild_id = str(discord_guild_id)
        doc = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).get()
        if not doc.exists:
            self.logger.info(f"디스코드서버ID:{discord_guild_id} 로 등록된 오딘길드가 없음.")
            return False, None, None
        dic = doc.to_dict()
        odin_server_name = dic[kFLD_SERVER_NAME]
        odin_guild_name = dic[kFLD_GUILD_NAME]
        self.logger.info(f"get odin guild : 디스코드서버ID:{discord_guild_id} 오딘길드:{odin_server_name}/{odin_guild_name}")
        return True, odin_server_name, odin_guild_name

    def set_odin_guild_info(self, discord_guild_id: int, odin_server_name: str, odin_guild_name: str) -> bool:
        '''
        {discord_guild_id}를 document명으로 하여 길드정보를 서버DB에 저장한다.
        :param discord_guild_id:
        :param odin_server_name:
        :param odin_guild_name:
        :return: 성공여부
        '''
        str_discord_guild_id = str(discord_guild_id)
        col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).set({
            kFLD_SERVER_NAME: odin_server_name,
            kFLD_GUILD_NAME: odin_guild_name
            }, merge=True)
        return True

    def get_boss_item(self, arg_boss_name: str, arg_option_str: str= 'name'):
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
                if arg_option_str == 'key':
                    return key
                elif arg_option_str == 'name':
                    return boss_name
                elif arg_option_str == 'chapter/name':
                    return f"/{boss_name}"
                else:
                    return item
        return None


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
