import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from functools import cmp_to_key
import logging

"""
 collection key
"""
kCOL_ODINDATA = "OdinData"
kCOL_ODINGUILD = u'OdinGuild'
kCOL_BOSS = u'Boss'

"""
 document key
"""
kDOC_ODINDATA = u'OdinData'

"""
 field name
"""
kFLD_SERVER_LIST = u'serverList'
kFLD_BOSS_DIC = u'bossDictionary'
kFLD_SERVER_NAME = u'serverName'
kFLD_GUILD_NAME = u'guildName'

"""
 dictionary key
"""
kCHAP_NO = u'chapNumber'
kBOSS_LEVEL = u'bossLevel'
kBOSS_ORDER = u'bossOrder'
kBOSS_NAME = u'bossName'
kBOSS_ALIAS = u'bossAlias'
kBOSS_INTERVAL = u'interval'

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

    def load_server_list(self):
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODINDATA).get()
        server_list = doc.to_dict()[kFLD_SERVER_LIST]
        self.logger.info(f"오딘서버목록 로딩 완료 : {server_list}")
        self.serverSet = set(server_list)
        return True

    def load_boss_dic(self):
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODINDATA).get()
        boss_dic = doc.to_dict()[kFLD_BOSS_DIC]
        self.logger.info(f"오딘보스목록 로딩 완료 : {boss_dic}")
        self.bossDic = set(boss_dic)
        return True

    def check_valid_server_name(self, odin_server_name):
        return odin_server_name in self.serverSet

    def get_odin_guild_info(self, discord_guild_id):
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

    def set_odin_guild_info(self, discord_guild_id, odin_server_name, odin_guild_name):
        str_discord_guild_id = str(discord_guild_id)
        col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).set({
            kFLD_SERVER_NAME: odin_server_name,
            kFLD_GUILD_NAME: odin_guild_name
        }, merge=True)
        return True
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









