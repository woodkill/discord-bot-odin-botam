import logging
import re


def check_timedelta_format(timedelta_str: str) -> bool:
    '''
    "0일0시간0분0초' 형식의 패턴을 만족하는 지 검사
    :param timedelta_str: 검사할 문자열
    :return:
    '''
    # 정규표현식 x일x시간x분x초 형식이어야 함.
    pattern = r'^(?P<days>(\d+)일)?\s*(?P<hours>(\d+)시간)?\s*(?P<minutes>(\d+)분)?\s*(?P<seconds>(\d+)초)?$'
    match = re.match(pattern, timedelta_str)
    if not match:
        return False
    return True


def get_seperated_timedelta_korean(timedelta_str: str) -> (int, int, int, int):
    '''
    시간 문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: "0일0시간0분0초" 형식의 문자열
    :return: 일, 시간, 분, 초
    '''
    pattern = r'^(?P<days>(\d+)일)?\s*(?P<hours>(\d+)시간)?\s*(?P<minutes>(\d+)분)?\s*(?P<seconds>(\d+)초)?$'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0 if g[1] is None else int(g[1])
    h = 0 if g[3] is None else int(g[3])
    m = 0 if g[5] is None else int(g[5])
    s = 0 if g[7] is None else int(g[7])
    return d, h, m, s


def get_seperated_timedlta_ddhhmm(timedelta_str: str) -> (int, int, int, int):
    '''
    시간 문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: "dd:hh:mm" 형식의 문자열
    :return:
    '''
    pattern = r'(\d{2}):(\d{2}):(\d{2})'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0 if g[0] is None else int(g[0])
    h = 0 if g[1] is None else int(g[1])
    m = 0 if g[2] is None else int(g[2])
    s = 0
    return d, h, m, s

def get_seperated_time_hhmm(timedelta_str: str) -> (int, int, int, int):
    '''
    시각(시간이 아님) 문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: 'hh:mm' 형식의 문자열
    :return: "hh:mm" 형식의 문자열. 이건 몇시간 몇분이 아니라 몇시몇분을 나타낸다.
    '''
    pattern = r'(\d{2}):(\d{2}))'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0
    h = 0 if g[0] is None else int(g[0])
    m = 0 if g[1] is None else int(g[1])
    s = 0
    return d, h, m, s