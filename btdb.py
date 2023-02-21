import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from functools import cmp_to_key
import logging

"""
 collection key
"""
kROOT_COL_ODINDATA = "OdinData"
kROOT_COL_ODINGUILD = u'OdinGuild'

"""
 document key
"""
kDOC_ODINDATA = u'OdinData'

"""
 field name
"""
kFIELD_SERVER_LIST = u'serverList'

"""
 오딘서버목록을 원격DB에서 로딩
"""


class BtDb():

    def __init__(self):
        # Use a service account.
        self.cred = credentials.Certificate('firebase.json')
        self.app = firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        # logger setting
        self.logger = logging.getLogger('db')
        # data storage
        self.gServerSet = self.get_server_info()

    def get_server_info(self):
        doc = self.db.collection(kROOT_COL_ODINDATA).document(kDOC_ODINDATA).get()
        serverList = doc.to_dict()[kFIELD_SERVER_LIST]
        self.logger.info(f"오딘서버 로딩 완료 : {serverList}")
        return set(serverList)







