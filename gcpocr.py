from google.cloud import vision
import io
import os
import numpy as np
import math
import difflib


def read_text(image_bytes):
    #os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_credentials

    client = vision.ImageAnnotatorClient()

    image = vision.Image(content=image_bytes)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    if len(texts) < 1:
        return []

    descriptions = texts[0].description.split("\n")

    raw_results = []
    index = 1

    special_chars = 'ⓒ㉡①|●②'

    for description in descriptions:
        content = description.replace(" ", "")

        str_len = 0
        for i in range(index, len(texts)):
            str_len += len(texts[i].description)
            if str_len == len(content):
                vertices = [[texts[index].bounding_poly.vertices[0].x, texts[index].bounding_poly.vertices[0].y], \
                            [texts[i].bounding_poly.vertices[1].x, texts[i].bounding_poly.vertices[1].y], \
                            [texts[i].bounding_poly.vertices[2].x, texts[i].bounding_poly.vertices[2].y], \
                            [texts[index].bounding_poly.vertices[3].x, texts[index].bounding_poly.vertices[3].y]]

                raw_results.append((vertices, description.translate({ord(i): None for i in special_chars}).strip(), 0.99))
                index = i + 1
                break

    #print(raw_results)

    return raw_results


def get_ocr_boss_time_list_by_bytes(image_bytes: bytes, bossname_list) -> (str, list):
    """

    :param image_bytes:
    :param bossname_list:
    :return:
    """
    # OCR 수행
    text_results = read_text(image_bytes)

    #print(text_results)

    # 이미지 좌상단 현재 시간 추출
    screenshot_time = find_current_time(text_results)
    # print('현재 시간: ', screenshot_time)

    # OCR로 추출된 텍스트들의 관계 정리
    text_results = delete_invalid_names(text_results)
    #print(text_results)
    final_results = mapping(text_results, bossname_list)
    # print(final_results)

    # 문자열 정리
    screenshot_time = screenshot_time.replace(" ", "")
    screenshot_time = screenshot_time.replace(":", "")
    screenshot_time = screenshot_time.replace(".", "")
    screenshot_time = screenshot_time.replace(";", "")
    screenshot_time = screenshot_time.replace(",", "")
    for boss_time_pair in final_results:
        # 보스명 및 남은시간에 스페이스 있으면 제거
        boss_time_pair[0] = boss_time_pair[0].replace(" ", "")
        boss_time_pair[1] = boss_time_pair[1].replace(" ", "")
        boss_time_pair[1] = boss_time_pair[1].replace("남음", "")

    return screenshot_time, final_results
