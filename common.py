import logging
import discord
from discord.ext import commands
import re
from common import *
from const_data import *


def to_ok_code_block(msg: str) -> str:
    """
    파란색 코드 블럭 문자열로 변환해서 리턴해준다.
    :param msg: 본문 문자열
    :return: 변환된 문자열
    """
    return f"```ansi\n" \
           f"\033[34;1m" \
           f"{msg}\n" \
           f"\033[0m\n" \
           f"```"


def to_error_code_block(msg: str) -> str:
    """
    빨간색 코드 블럭 문자열로 변환해서 리턴해준다.
    :param msg: 본문 문자열
    :return: 변환된 문자열
    """
    return f"```ansi\n" \
           f"\033[31;1m" \
           f"{msg}\n" \
           f"\033[0m\n" \
           f"```"


def to_guide_code_block(msg: str) -> str:
    """
    초록색 코드 블럭 문자열로 변환해서 리턴해준다.
    :param msg: 본문 문자열
    :return: 변환된 문자열
    """
    return f"```ansi\n" \
           f"\033[32;1m" \
           f"{msg}\n" \
           f"\033[0m\n" \
           f"```"


async def send_ok_message(ctx: commands.Context, msg: str):
    """
    파란색 코드 블럭 문자열로 context 채널에 전송
    :param ctx: Context
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```ansi\n" \
                  f"\033[34;1m" \
                  f"{msg}\n" \
                  f"\033[0m\n" \
                  f"```"
    await ctx.send(lapping_msg)


async def send_error_message(ctx: commands.Context, msg: str):
    """
    빨간색 코드 블럭 문자열로 context 채널에 전송
    :param ctx: Context
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```ansi\n" \
                  f"\033[31;1m" \
                  f"{msg}\n" \
                  f"\033[0m\n" \
                  f"```"
    await ctx.send(lapping_msg)


async def send_guide_message(ctx: commands.Context, msg: str):
    """
    초록색 코드 블럭 문자열로 context 채널에 전송
    :param ctx: Context
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```ansi\n" \
                  f"\033[32;1m" \
                  f"{msg}\n" \
                  f"\033[0m\n" \
                  f"```"
    await ctx.send(lapping_msg)


async def response_error_message(response: discord.Interaction.response, msg:str):
    """
    빨간색 코드 블럭 문자열로 응답메세지 전송
    :param response: Response
    :param msg: 원본 문자열
    :return: 없음
    """
    lapping_msg = f"```ansi\n" \
                  f"\033[31;1m" \
                  f"{msg}\n" \
                  f"\033[0m\n" \
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


def is_hh_mm_timedelta_format(timedelta_str: str) -> bool:
    """
    HH:MM 형식의 패턴을 만족하는 지 검사
    :param timedelta_str:
    :return:
    """
    # 정규표현식 HH:MM 형식이어야 함.
    pattern = r'(\d{2}):(\d{2}))'
    match = re.match(pattern, timedelta_str)
    if not match:
        return False
    return True


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
    pattern = r'(\d{2}):(\d{2}))'
    match = re.match(pattern, timedelta_str)
    g = match.groups()
    d = 0
    h = 0 if g[0] is None else int(g[0])
    m = 0 if g[1] is None else int(g[1])
    s = 0
    return d, h, m, s