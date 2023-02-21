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
kFLD_SERVER_NAME = u'serverName'
kFLD_GUILD_NAME = u'guildName'


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
        # initialize
        self.load_server_list()

    def load_server_list(self):
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODINDATA).get()
        server_list = doc.to_dict()[kFLD_SERVER_LIST]
        self.logger.info(f"오딘서버목록 로딩 완료 : {server_list}")
        self.serverSet = set(server_list)
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









