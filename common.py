import logging
import discord
from discord.ext import commands
import re
from const_data import *

cPREFIX_ANSI = "ansi\n"
cPREFIX_CODEBLOCK_OK = "\x1b[34;1m"
cPREFIX_CODEBLOCK_ERROR = "\x1b[31;1m"
cPREFIX_CODEBLOCK_USAGE = "\x1b[32;1m"
cPREFIX_CODEBLOCK_LOTTERY_ITEM = "\x1b[32;1m"
cPOSTFIX_CODEBLOCK = "\x1b[0m"


def to_ok_code_block(msg: str) -> str:
    """
    파란색 코드 블럭 문자열로 변환해서 리턴해준다.
    :param msg: 본문 문자열
    :return: 변환된 문자열
    """
    return f"```{cPREFIX_ANSI}" \
           f"{cPREFIX_CODEBLOCK_OK}" \
           f"{msg}\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"```"


def to_error_code_block(msg: str) -> str:
    """
    빨간색 코드 블럭 문자열로 변환해서 리턴해준다.
    :param msg: 본문 문자열
    :return: 변환된 문자열
    """
    return f"```{cPREFIX_ANSI}" \
           f"{cPREFIX_CODEBLOCK_ERROR}" \
           f"{msg}\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"```"


def to_guide_code_block(msg: str) -> str:
    """
    초록색 코드 블럭 문자열로 변환해서 리턴해준다.
    :param msg: 본문 문자열
    :return: 변환된 문자열
    """
    return f"```{cPREFIX_ANSI}" \
           f"{cPREFIX_CODEBLOCK_USAGE}" \
           f"{msg}\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"```"


def to_chulcheck_code_block(msg: str, member_list: list):
    """

    :param msg:
    :param members:
    :return:
    """
    count = len(member_list)
    str_members = ', '.join(member_list)
    return f"```{cPREFIX_ANSI}" \
           f"{cPREFIX_CODEBLOCK_OK}" \
           f"{msg}\n" \
           f"{cPREFIX_CODEBLOCK_USAGE}" \
           f"출석인원:{count}\n\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"{str_members}" \
           f"```"


def to_before_lottery_code_block(item_name: str, target_count: int, member_list: list):
    """

    :param item_name:
    :param target_count:
    :param member_list:
    :return:
    """
    count = len(member_list)
    str_members = ', '.join(member_list)
    return f"```{cPREFIX_ANSI}" \
           f"{cPREFIX_CODEBLOCK_LOTTERY_ITEM}" \
           f"{item_name}\n\n" \
           f"{cPREFIX_CODEBLOCK_OK}" \
           f"뽑기({target_count}) 대상({len(member_list)})\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"{str_members}" \
           f"```"


def to_after_lottery_code_block(item_name: str, target_count: int, member_list: list, selected_member_list: list):
    """

    :param item_name:
    :param target_count:
    :param member_list:
    :return:
    """
    count = len(member_list)
    str_members = ', '.join(member_list)
    return f"```{cPREFIX_ANSI}" \
           f"{cPREFIX_CODEBLOCK_LOTTERY_ITEM}" \
           f"{item_name}\n\n" \
           f"{cPREFIX_CODEBLOCK_OK}" \
           f"뽑기({target_count}) 대상({len(member_list)})\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"{str_members}\n\n" \
           f"{cPREFIX_CODEBLOCK_OK}" \
           f"당첨({len(selected_member_list)})\n" \
           f"{cPOSTFIX_CODEBLOCK}" \
           f"{', '.join(selected_member_list)}" \
           f"```"


async def send_common_message(ctx: commands.Context, msg:str):
    """
    흰색 코드 블럭 문자열로 context 채널에 전송
    :param ctx:
    :param msg:
    :return:
    """
    lapping_msg = f"```" \
                  f"{msg}" \
                  f"```"
    await ctx.send(lapping_msg)


async def send_ok_message(ctx: commands.Context, msg: str):
    """
    파란색 코드 블럭 문자열로 context 채널에 전송
    :param ctx: Context
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```{cPREFIX_ANSI}" \
                  f"{cPREFIX_CODEBLOCK_OK}" \
                  f"{msg}\n" \
                  f"{cPOSTFIX_CODEBLOCK}" \
                  f"```"
    await ctx.send(lapping_msg)


async def send_error_message(ctx: commands.Context, msg: str):
    """
    빨간색 코드 블럭 문자열로 context 채널에 전송
    :param ctx: Context
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```{cPREFIX_ANSI}" \
                  f"{cPREFIX_CODEBLOCK_ERROR}" \
                  f"{msg}\n" \
                  f"{cPOSTFIX_CODEBLOCK}" \
                  f"```"
    await ctx.send(lapping_msg)


async def send_guide_message(ctx: commands.Context, msg: str):
    """
    초록색 코드 블럭 문자열로 context 채널에 전송
    :param ctx: Context
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```{cPREFIX_ANSI}" \
                  f"{cPREFIX_CODEBLOCK_USAGE}" \
                  f"{msg}\n" \
                  f"{cPOSTFIX_CODEBLOCK}" \
                  f"```"
    await ctx.send(lapping_msg)


async def response_error_message(response: discord.Interaction.response, msg:str):
    """
    빨간색 코드 블럭 문자열로 응답메세지 전송
    :param response: Response
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```{cPREFIX_ANSI}" \
                  f"{cPREFIX_CODEBLOCK_ERROR}" \
                  f"{msg}\n" \
                  f"{cPOSTFIX_CODEBLOCK}" \
                  f"```"
    await response.send_message(lapping_msg)


async def send_ok_embed(ctx: commands.Context, msg: str, additional: str = ""):
    """
    파란색 임베드 전송 간편 버전
    :param ctx: Context
    :param msg: 메세지
    :param additional: footer에 넣을 문자열
    :return: 없음
    """
    embed = discord.Embed(description=msg, color=discord.Color.blurple())
    embed.set_footer(text=additional)
    await ctx.send(embed=embed)


async def send_error_embed(ctx: commands.Context, msg: str, additional: str = ""):
    """
    빨간색 임베드 전송 간편 버전
    :param ctx: Context
    :param msg: 메세지
    :param additional: footer에 넣을 문자열
    :return: 없음
    """
    embed = discord.Embed(description=msg, color=discord.Color.red())
    embed.set_footer(text=additional)
    await ctx.send(embed=embed)


async def send_usage_embed(ctx: commands.Context, cmd: str, title: str = u"사용법", additional: str = ""):
    """
    사용법 임베드를 전송
    :param ctx: Context
    :param cmd: 명령어
    :param title: 타이틀
    :param additional:
    :return:
    """
    if cmd not in cUsageDic:
        return
    embed = discord.Embed(
        title=f"{ctx.prefix}{cUsageDic[cmd][kCMD_USAGE]}",
        description=cUsageDic[cmd][kCMD_EXPLANATION] if additional == "" else additional,
        color=discord.Color.brand_green())
    # embed.add_field(name=title, value=f"{ctx.prefix}{cUsageDic[cmd][kCMD_USAGE]}")
    # str_explanation = cUsageDic[cmd][kCMD_EXPLANATION] if additional == "" else additional
    # embed.set_footer(text=str_explanation)
    await ctx.send(embed=embed)


def get_help_list_embed():
    """

    :return:
    """
    embed = discord.Embed(title=u"사용법", description="[,] 안에 있는 것은 생략 가능", color=discord.Color.brand_green())
    for cmd, usage in cUsageDic.items():
        str_usage = f"{cPREFIX}{usage[kCMD_USAGE]}"
        str_explanation = usage[kCMD_EXPLANATION]
        embed.add_field(name=str_usage, value=str_explanation, inline=False)
    return embed


def is_korean_timedelta_format(timedelta_str: str) -> bool:
    """
    "0일0시간0분0초' 형식의 패턴을 만족하는 지 검사
    :param timedelta_str: 검사할 문자열
    :return:
    """
    # 정규표현식 x일x시간x분x초 형식이어야 함.
    pattern = r'^(?P<days>(\d+)일)?\s*(?P<hours>(\d+)시간)?\s*(?P<minutes>(\d+)분)?\s*(?P<seconds>(\d+)초)?$'
    match = re.match(pattern, timedelta_str)
    if not match:
        return False
    return True


def is_hh_mm_timedelta_format(time_str: str) -> bool:
    """
    HH:MM 형식의 패턴을 만족하는 지 검사
    :param time_str:
    :return:
    """
    # 정규표현식 HH:MM 형식이어야 함.
    pattern = r'(\d{2}):(\d{2})'
    match = re.match(pattern, time_str)
    if not match:
        return False
    return True


def get_yearmonthday_korean(timedelta_str: str) -> (int, int, int):
    """
    문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: "0년0월0일" 형식의 문자열
    :return: 년, 월, 일
    """
    pattern = r'^(?P<year>(\d+)년)?\s*(?P<month>(\d+)월)?\s*(?P<day>(\d+)일)?$'
    match = re.match(pattern, timedelta_str)
    if not match:
        return 0, 0, 0
    g = match.groups()
    y = 0 if g[1] is None else int(g[1])
    m = 0 if g[3] is None else int(g[3])
    d = 0 if g[5] is None else int(g[5])
    return y, m, d


def get_separated_timedelta_korean(timedelta_str: str) -> (int, int, int, int):
    """
    시간 문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: "0일0시간0분0초" 형식의 문자열
    :return: 일, 시간, 분, 초
    """
    pattern = r'^(?P<days>(\d+)일)?\s*(?P<hours>(\d+)시간)?\s*(?P<minutes>(\d+)분)?\s*(?P<seconds>(\d+)초)?$'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0 if g[1] is None else int(g[1])
    h = 0 if g[3] is None else int(g[3])
    m = 0 if g[5] is None else int(g[5])
    s = 0 if g[7] is None else int(g[7])
    return d, h, m, s


def get_separated_timedelta_ddhhmm(timedelta_str: str) -> (int, int, int, int):
    """
    시간 문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: "dd:hh:mm" 형식의 문자열
    :return:
    """
    pattern = r'(\d{2}):(\d{2}):(\d{2})'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0 if g[0] is None else int(g[0])
    h = 0 if g[1] is None else int(g[1])
    m = 0 if g[2] is None else int(g[2])
    s = 0
    return d, h, m, s


def get_separated_time_hhmm(timedelta_str: str) -> (int, int, int, int):
    """
    시각(시간이 아님) 문자열을 분석, 쪼개서 리턴하는 함수.
    :param timedelta_str: 'hh:mm' 형식의 문자열
    :return: "hh:mm" 형식의 문자열. 이건 몇시간 몇분이 아니라 몇시몇분을 나타낸다.
    """
    pattern = r'(\d{2}):(\d{2})'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0
    h = 0 if g[0] is None else int(g[0])
    m = 0 if g[1] is None else int(g[1])
    s = 0
    return d, h, m, s


def extract_number_at_end_of_string(s):
    match = re.search(r'\d+$', s)
    if match:
        return int(match.group())
    else:
        return None


def parse_lottery_message(msg: str) -> (str, int, list):
    pmsg = discord.utils.remove_markdown(msg)
    pmsg = pmsg.removeprefix(cPREFIX_ANSI)
    msg_list = pmsg.split()
    item_name = msg_list[0].removeprefix(cPREFIX_CODEBLOCK_LOTTERY_ITEM)
    target_count = int(msg_list[1].removeprefix(cPREFIX_CODEBLOCK_OK).removeprefix(u"뽑기(").removesuffix(u")"))
    msg_list[3] = msg_list[3].removeprefix(cPOSTFIX_CODEBLOCK)
    member_list = []
    if len(msg_list[3]) > 0:
        for i in range(3, len(msg_list)):
            member_list.append(msg_list[i].removesuffix(','))
    return item_name, target_count, member_list


def is_selected_lottery_message(msg: str) -> bool:
    return True if msg.find(u"당첨") != -1 else False
