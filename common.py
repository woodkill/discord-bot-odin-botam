import re


def check_timedelta_format(timedelta_str: str) -> bool:
    # 정규표현식 x일x시간x분x초 형식이어야 함.
    pattern = r'^(?P<days>(\d+)일)?\s*(?P<hours>(\d+)시간)?\s*(?P<minutes>(\d+)분)?\s*(?P<seconds>(\d+)초)?$'
    match = re.match(pattern, timedelta_str)
    if not match:
        return False
    return True


def get_seperated_timedelta(timedelta_str: str) -> (int, int, int, int):
    pattern = r'^(?P<days>(\d+)일)?\s*(?P<hours>(\d+)시간)?\s*(?P<minutes>(\d+)분)?\s*(?P<seconds>(\d+)초)?$'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0 if g[1] is None else g[1]
    h = 0 if g[3] is None else g[3]
    m = 0 if g[5] is None else g[5]
    s = 0 if g[7] is None else g[7]
    return d, h, m, s
