import logging
import datetime
from pytz import timezone, utc

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# from firebase_admin import firestore_async

from const_data import *

KST = timezone('Asia/Seoul')
UTC = utc


class BtDb:

    def __init__(self):
        # Use a service account.
        self.cred = credentials.Certificate('firebase.json')
        self.app = firebase_admin.initialize_app(self.cred)
        self.db = firestore.client()
        # TODO: firestore async와 sync 차이점?
        # self.asyncdb = firestore_async.client()
        # logger setting
        self.logger = logging.getLogger('bot.db')
        # master data storage
        self.serverDic: dict = {}
        self.bossDic: dict = {}
        # initialize
        self.load_server_dic()
        self.load_boss_dic()
        self.logger.info(f"BtDb init complete")

    def load_server_dic(self) -> bool:
        """
        서버 DB에서 오딘 서버 목록을 검색하여 self.serverSet에 저장
        :return: 성공여부
        """
        doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODIN_SERVER).get()
        server_dic = doc.to_dict()
        # self.logger.debug(f"오딘서버목록 로딩 완료 : {server_dic}")
        self.serverDic = server_dic
        return True

    def load_boss_dic(self) -> bool:
        """
        서버DB에서 오딘의 보스정보를 쿼리하여 self.bossDic에 저장
        :return: 성공여부
        """
        try:
            doc = self.db.collection(kCOL_ODINDATA).document(kDOC_ODIN_BOSS).get()
        except Exception as e:
            self.logger.error(e)
            return False
        boss_dic = doc.to_dict()
        # self.logger.debug(f"오딘보스목록 로딩 완료 : {boss_dic}")
        self.bossDic = boss_dic
        return True

    def check_valid_server_name(self, odin_server_name: str) -> bool:
        """
        오딘서버명 진위 여부 판단
        :param odin_server_name: 검사할 오딘 서버명
        :return: odin_server_name 과 같은 오딘서버가 있는지 여부
        """
        r = {server[1][kSERVER_NAME] for server in self.serverDic.items() if server[1][kSERVER_NAME] == odin_server_name}
        # self.logger.debug(r)
        return len(r) != 0

    def check_valid_boss_name(self, arg_boss_name: str) -> bool:
        """
        존재하는 보스명인
        :param arg_boss_name:
        :return: True, False
        """
        for key, boss in self.bossDic.items():
            boss_name = boss[kBOSS_NAME]
            boss_alias_list = boss[kBOSS_ALIAS]
            if arg_boss_name == boss_name or arg_boss_name in boss_alias_list:
                return True
        return False

    def get_odin_guild_info(self, discord_guild_id: int) -> (bool, dict):
        """
        {discord_guild_id}로 등록된 길드 정보(오딘서버명, 길드명)을 쿼리하여 리턴한다.
        :param discord_guild_id:
        :return: (성공여부, 오딘서버명, 길드명)
        """
        str_discord_guild_id = str(discord_guild_id)
        try:
            doc = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).get()
        except Exception as e:
            self.logger.error(e)
            return
        if not doc.exists:
            self.logger.warning(f"디스코드서버ID:{discord_guild_id} 로 등록된 오딘길드가 없음.")
            return False, None
        odin_guild_dic = doc.to_dict()
        # self.logger.debug(f"get_odin_guild_info : {odin_guild_dic}")
        return True, odin_guild_dic

    def get_all_odin_guilds_info(self) -> (bool, dict):
        """

        :return:
        """
        odin_guilds_dic = {}
        try:
            docs = self.db.collection(kCOL_ODINGUILD).stream()
        except Exception as e:
            self.logger.error(e)
            return False, None
        # self.logger.debug(f"{docs}")
        for doc in docs:
            odin_guilds_dic[int(doc.id)] = doc.to_dict()
        # self.logger.debug(f"{odin_guilds_dic}")
        return True, odin_guilds_dic

    def set_odin_guild_info(self,
                            discord_guild_id: int,
                            channel_id: int,
                            odin_server_name: str,
                            odin_guild_name: str) -> (bool, dict):
        """
        {discord_guild_id}를 document명으로 하여 길드정보를 서버DB에 저장한다.
        :param discord_guild_id: 명령어를 접수한 디코 서버 id
        :param channel_id: 현재 명령어를 접수한 디코 채널 id
        :param odin_server_name: 등록할 오딘서버명
        :param odin_guild_name: 등록할 오딘길드명
        :return: 성공여부
        """
        str_discord_guild_id = str(discord_guild_id)
        guild_info = {
                kFLD_SERVER_NAME: odin_server_name,
                kFLD_GUILD_NAME: odin_guild_name,
                kFLD_CHANNEL_ID: channel_id,
                kFLD_ALARMS: {},
                kFLD_ALARM_TIMERS: cLIST_DEFAULT_TIMERS
                }
        try:
            col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).set(guild_info, merge=True)
        except Exception as e:
            self.logger.error(e)
            return False, None
        return True, guild_info

    def remove_odin_guild_info(self, discord_guild_id: int):
        str_discord_guild_id = str(discord_guild_id)
        try:
            self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).delete()
        except Exception as e:
            self.logger.error(e)

    def set_odin_guild_register_alarm_channel(self, discord_guild_id: int, channel_id: int) -> bool:
        """
        {discord_guild_id}를 document명으로 하여 알람 받을 채널id를 서버DB에 저장한다.
        :param discord_guild_id: 명령어를 접수한 디코 서버 id
        :param channel_id: 명령어를 접수한 디코 채널 id
        :return: 성공여부
        """
        str_discord_guild_id = str(discord_guild_id)
        try:
            col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).set({
                kFLD_CHANNEL_ID: channel_id
            }, merge=True)
        except Exception as e:
            self.logger.error(e)
            return False
        return True

    def get_bossname_list(self) -> list:
        """
        보스명 문자열로만 되어 있는 리스트를 만들어서 리턴
        :return:
        """
        # self.logger.debug(self.bossDic)
        if len(self.bossDic) == 0:
            self.logger.warning(f"self.bossDic 이 비어있습니다.")
            return None
        bossname_list = []
        for item in self.bossDic.values():
            bossname_list.append(item[kBOSS_NAME])
        return bossname_list

    def get_boss_list(self) -> list:
        """
        보스정보를 key를 제외하고 리스트로 리턴
        :return: 보스정보 dic의 list
        """
        # self.logger.debug(self.bossDic)
        if len(self.bossDic) == 0:
            self.logger.warning(f"self.bossDic 이 비어있습니다.")
            return None
        boss_list = list(self.bossDic.values())
        return sorted(boss_list, key=lambda x: (x[kCHAP_ORDER], x[kBOSS_LEVEL], x[kBOSS_ORDER]))

    def get_boss_item_by_name(self, arg_boss_name: str) -> (str, dict):
        """
        메모리에 로딩된 정보로 보스정보 찾아주기
        :param arg_boss_name: 보스명 혹은 보스별명
        :return: 찾는 보스가 있을 경우 옵션에 따라 리턴한다.
        'key' :  key문자열
        'name' : 보스명,
        'chapter/name' : 지역명/보스명
        'item' : 보스정보dic
        """
        # self.logger.debug(self.bossDic)
        if len(self.bossDic) == 0:
            return None, None
        # self.bossDic의 보스명과 보스별명을 검사하여 해당 보스키값과 정보dict를 리턴한다.
        for key, item in self.bossDic.items():
            boss_name = item[kBOSS_NAME]
            boss_alias = item[kBOSS_ALIAS]
            if arg_boss_name == boss_name or arg_boss_name in boss_alias:
                return key, item
        return None, None

    def get_daily_fiexed_alarm_info_from_master(self) -> dict:
        """
        월보 알람 정보 dic을 만들어서 리턴한다.
        :return:
        {
          "12:00": [
            "아우둠라",
            "발두르",
            "갸름",
            "파프니르",
            "헤임달"
          ],
          "22:00": [
            "아우둠라",
            "발두르",
            "갸름",
            "파프니르",
            "헤임달"
          ]
        }
        """
        # self.logger.debug(f"{self.bossDic}")

        alarm_dic = {}  # 요기다가 만들어서 리턴한다.
        for key, boss in self.bossDic.items():  # 각 보스의 정보를 하나씩 가져와서...
            if boss[kBOSS_TYPE] != cBOSS_TYPE_DAILY_FIXED:
                continue
            boss_fixed_time_list = boss[kBOSS_FIXED_TIME]  # 보스가 뜨는 고정시간 목록
            for str_boss_fixed_time in boss_fixed_time_list:  # 각 고정시간을 key로 하고 값을 보스명 list인 dict 만든다.
                if str_boss_fixed_time not in alarm_dic:
                    alarm_dic[str_boss_fixed_time] = [boss[kBOSS_NAME]]
                else:
                    alarm_dic[str_boss_fixed_time].append(boss[kBOSS_NAME])

        # self.logger.debug(alarm_dic)
        return alarm_dic

    def get_weekday_fiexed_alarm_info_from_master(self) -> dict:
        """
        :return:
        {
            "1": {
                "21:30": [
                    "그로아의사념",
                    "헤르모드의사념",
                    "야른의사념",
                    "굴베이그의사념",
                    "파프니르의그림자"
                ]
            },
            "3": {
                "21:30": [
                    "그로아의사념",
                    "헤르모드의사념",
                    "야른의사념",
                    "굴베이그의사념",
                    "파프니르의그림자"
                ]
            }
        }
        """
        # self.logger.info(f"{self.bossDic}")

        alarm_dic = {}  # 요기다가 만들어서 리턴한다.
        for key, boss in self.bossDic.items():  # 각 보스의 정보를 하나씩 가져와서...
            if boss[kBOSS_TYPE] != cBOSS_TYPE_WEEKDAY_FIXED:
                continue
            boss_week_day_info_dic = boss[kBOSS_WEEKDAY_INFO]  # 일주일에 어떤 요일 몇시에 뜨는지 정보가 있는 dict의 리스트
            for boss_weekday_info in boss_week_day_info_dic:  # 각 요일을 key로 하고 {시간: 보스명리스트}인 dict를 만든다.
                str_boss_weekday_no = boss_weekday_info[kBOSS_WEEKDAY]  # 요일번호 문자열(firestore에서 키로 숫자가 안되서...)
                if str_boss_weekday_no not in alarm_dic:
                    alarm_dic[str_boss_weekday_no] = {}
                weekday_dic = alarm_dic[str_boss_weekday_no]
                boss_fixed_time_list = boss_weekday_info[kBOSS_APPEARANCE_TIME]
                for boss_fixed_time in boss_fixed_time_list:
                    if boss_fixed_time not in weekday_dic:
                        weekday_dic[boss_fixed_time] = [boss[kBOSS_NAME]]
                    else:
                        weekday_dic[boss_fixed_time].append(boss[kBOSS_NAME])

        self.logger.info(alarm_dic)
        return alarm_dic

    def set_guild_alarms(self, discord_guild_id: int, guild_alarm_dic: dict):
        """

        :param discord_guild_id:
        :param guild_alarm_dic:
        :return:
        """
        str_discord_guild_id = str(discord_guild_id)
        try:
            col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).update({
                kFLD_ALARMS: guild_alarm_dic
            })
        except Exception as e:
            self.logger.debug(e)

    def set_guild_alarm_timers(self, discord_guild_id: int, guild_alarm_timers: list):
        """

        :param discord_guild_id:
        :param guild_alarm_timers:
        :return:
        """
        str_discord_guild_id = str(discord_guild_id)
        try:
            col_ref = self.db.collection(kCOL_ODINGUILD).document(str_discord_guild_id).update({
                kFLD_ALARM_TIMERS: guild_alarm_timers
            })
        except Exception as e:
            self.logger.debug(e)

    def get_lastone_chulcheck(self, guild_id: int, boss_name: str) -> (str, dict):
        """

        :param guild_id:
        :param boss_name:
        :return:
        """
        try:
            query = self.db.collection(kCOL_ODINBOTAMCHULCHECK) \
                .where(kFLD_CC_GUILD, u"==", guild_id) \
                .where(kFLD_CC_BOSSNAME, u'==', boss_name) \
                .order_by(kFLD_CC_DATETIME).limit_to_last(1)
            query_snapshot = query.get()
        except Exception as e:
            self.logger.error(e)
            return None, None

        if len(query_snapshot) == 0:
            return None, None

        self.logger.debug(query_snapshot[0].to_dict())

        return query_snapshot[0].id, query_snapshot[0].to_dict()

    def add_chulcheck(self, guild_id: int, botam_datetime: datetime.datetime, boss_name: str, cc_members: list) -> (str, dict):
        """

        :param guild_id:
        :param botam_datetime:
        :param boss_name:
        :param cc_members:
        :return:
        """
        chulcheck_dic = {
            kFLD_CC_GUILD: guild_id,
            kFLD_CC_DATETIME: botam_datetime,
            kFLD_CC_BOSSNAME: boss_name,
            kFLD_CC_MEMBERS: cc_members
        }
        try:
            update_time, cc_ref = self.db.collection(kCOL_ODINBOTAMCHULCHECK).add(chulcheck_dic)
        except Exception as e:
            self.logger.error(e)
            return None, None

        return cc_ref.id, chulcheck_dic

    def add_member_to_chulcheck(self, doc_id: str, member: str):
        """

        :param doc_id:
        :param member:
        :return:
        """
        transaction = self.db.transaction()
        chulcheck_ref = self.db.collection(kCOL_ODINBOTAMCHULCHECK).document(doc_id)

        @firestore.transactional
        def update_in_transaction(tr, chulcheck_ref, m):
            try:
                snapshot = chulcheck_ref.get(transaction=tr)
                members = snapshot.get(kFLD_CC_MEMBERS)
                members.append(m)
                tr.update(chulcheck_ref, {kFLD_CC_MEMBERS: members})
            except Exception as e:
                self.logger.debug(e)
                return None
            return members

        member_list = update_in_transaction(transaction, chulcheck_ref, member)
        if member_list is None:
            return None, None

        return chulcheck_ref.id, member_list # TODO:이거 제대로 된 값으로..

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
