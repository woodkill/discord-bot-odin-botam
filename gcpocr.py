from google.cloud import vision
from google.oauth2.service_account import Credentials
import cv2
import imutils
import logging
import io
import os
import numpy as np
import math
import difflib

credentials = Credentials.from_service_account_file('./cloudvision.json')
clock_icon_template_image = cv2.imread('./images/template_clock.png', cv2.IMREAD_GRAYSCALE)

def remove_invalid_areas(image_bytes):
    """

    :param image_bytes:
    :return:
    """
    # 화일에서 읽는것 대신 디스코드 API가 주는 bytes객체 사용
    # origin_image = cv2.imread(image_file)
    image_np = np.frombuffer(image_bytes, np.uint8)
    origin_image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    image = cv2.cvtColor(origin_image, cv2.COLOR_BGR2GRAY)

    # 전역변수로 뺐음
    # clock_icon_template_image = cv2.imread(template_file, cv2.IMREAD_GRAYSCALE)

    for scale in np.linspace(0.4, 1.8, 13)[::-1]:
        resized = imutils.resize(clock_icon_template_image, width=int(clock_icon_template_image.shape[1] * scale))
        ratio = clock_icon_template_image.shape[1] / float(resized.shape[1])

        result = cv2.matchTemplate(image, resized, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        location = np.where(result >= threshold)
        for pt in zip(*location[::-1]):
            origin_image[pt[1]: pt[1] + resized.shape[0], pt[0]: pt[0] + resized.shape[1]] = (0, 0, 0)

    # new_image_name = image_file.replace('.png', '_del.png')
    # cv2.imwrite(new_image_name, origin_image)
    # return new_image_name

    retval, buffer = cv2.imencode('.png', origin_image)
    new_image_bytes = buffer.tobytes()

    return new_image_bytes


# 디스코드가 준 bytes객체를 바로 쓸 때
# def read_text(image_bytes):
#     """
#     google cloud platform vision을 이용해 이미지에서 한글 텍스트를 추출
#     :param image_bytes:
#     :return:
#     """
#
#     client = vision.ImageAnnotatorClient(credentials=credentials)
#     image = vision.Image(content=image_bytes)
#     response = client.text_detection(image=image)
#     texts = response.text_annotations
#     if len(texts) < 1:
#         return []
#
#     descriptions = texts[0].description.split("\n")
#
#     raw_results = []
#     index = 1
#
#     special_chars = 'ⓒ㉡①|●②'
#
#     for description in descriptions:
#         content = description.replace(" ", "")
#         str_len = 0
#         for i in range(index, len(texts)):
#             str_len += len(texts[i].description)
#             if str_len == len(content):
#                 vertices = [[texts[index].bounding_poly.vertices[0].x, texts[index].bounding_poly.vertices[0].y], \
#                             [texts[i].bounding_poly.vertices[1].x, texts[i].bounding_poly.vertices[1].y], \
#                             [texts[i].bounding_poly.vertices[2].x, texts[i].bounding_poly.vertices[2].y], \
#                             [texts[index].bounding_poly.vertices[3].x, texts[index].bounding_poly.vertices[3].y]]
#
#                 raw_results.append((vertices, description.translate({ord(i): None for i in special_chars}).strip(), 0.99))
#                 index = i + 1
#                 break
#
#     #print(raw_results)
#
#     return raw_results

# remove_invalid_areas 함수로 전처리한 결과를 쓸때
def read_text(cv_image):
    """
    google cloud platform vision을 이용해 이미지에서 한글 텍스트를 추출
    :param image_bytes:
    :return:
    """

    client = vision.ImageAnnotatorClient(credentials=credentials)
    image = vision.Image(content=cv_image)
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

def find_current_time(text_results):
    """
    시간표 이미지 좌상단의 '현재 시간' 추출
    :param text_results: read_text 함수에서 리턴한 리스트
    :return:
    """
    for i in range(len(text_results)):
        if text_results[i][1].startswith('현재 시간'):
            if len(text_results[i][1]) > 10:
                return text_results[i][1].replace('현재 시간', '').strip()
            else:
                nearest_index = get_nearest_box_index(text_results, i, 20, '')
                if nearest_index < 0:
                    return None
                return text_results[nearest_index][1]

    return None


# def get_nearest_box_index(text_results, base_index, vertical_weight, right_only):
#     """
#     가장 가까운 글자 박스 검출
#     :param text_results:
#     :param base_index:
#     :param vertical_weight:
#     :param right_only:
#     :return:
#     """
#     nearest_index = -1
#     nearest_distance = 1000000
#     for i in range(len(text_results)):
#         if i == base_index:
#             continue
#
#         if right_only and text_results[base_index][0][0] > text_results[i][0][0]:
#             continue
#
#         distance = distance_boxes(text_results[base_index][0], text_results[i][0])
#         if vertical_weight > 0:
#             distance += vertical_distance_boxes(text_results[base_index][0], text_results[i][0]) * vertical_weight
#
#         if distance < nearest_distance:
#             nearest_index = i
#             nearest_distance = distance
#
#     return nearest_index

def get_nearest_box_index(text_results, base_index, vertical_weight, direction):
    """
    가장 가까운 글자 박스 검출
    :param text_results:
    :param base_index:
    :param vertical_weight:
    :param direction:
    :return:
    """
    nearest_index = -1
    nearest_distance = 1000000
    for i in range(len(text_results)):
        if i == base_index:
            continue

        if direction:
            if 'right' in direction and text_results[base_index][0][0][0] > text_results[i][0][0][0]:
                continue
            if 'bottom' in direction and text_results[base_index][0][0][1] > text_results[i][0][0][1]:
                continue

        distance = distance_boxes(text_results[base_index][0], text_results[i][0])
        if vertical_weight > 0:
            distance += vertical_distance_boxes(text_results[base_index][0], text_results[i][0]) * vertical_weight

        if distance < nearest_distance:
            nearest_index = i
            nearest_distance = distance

    return nearest_index


def distance_boxes(box1, box2):
    """
    두점의 거리 계산
    :param box1:
    :param box2:
    :return:
    """
    center1 = [(box1[1][0] - box1[0][0]) / 2 + box1[0][0], (box1[1][1] - box1[0][1]) / 2 + box1[0][1]]
    center2 = [(box2[1][0] - box2[0][0]) / 2 + box2[0][0], (box2[1][1] - box2[0][1]) / 2 + box2[0][1]]

    return math.sqrt((center2[0] - center1[0])**2 + (center2[1] - center1[1])**2)


def vertical_distance_boxes(box1, box2):
    """
    y축에 대한 거리 계산
    :param box1:
    :param box2:
    :return:
    """
    center1 = (box1[1][1] - box1[0][1]) / 2 + box1[0][1]
    center2 = (box2[1][1] - box2[0][1]) / 2 + box2[0][1]

    return abs(center1 - center2)


def delete_invalid_names(text_results):
    """
    검출을 원하지 않는 단어를 걸러낸다.
    :param text_results:
    :return:
    """
    ignore_names = ['현재 시간', '노른의 시간표', '미드가르드', '요툰하임', '니다벨리르', '알브하임', '무스펠하임', \
                    '아스가르드', '던전', '거점 지배자', '절대자', '대륙 침략자', '발할라 대전']

    new_results = []

    for i in range(len(text_results)):
        if len(text_results[i][1]) <= 1:
            continue

        source_name = list(text_results[i][1])

        ignore = False
        for j in range(len(ignore_names)):
            ignore_name = list(ignore_names[j])

            if bytes_similarity(source_name, ignore_name) > 0.6:
                ignore = True
                #print('(deleted) ', text_results[i][1], ' ignore_name: ', ignore_names[j], ' similarity: ', bytes_similarity(source_name, ignore_name))
                break

        if ignore == False:
            new_results.append(text_results[i])

    return new_results


def bytes_similarity(list1, list2):
    """

    :param list1:
    :param list2:
    :return:
    """
    list1_bytes = list(bytes(''.join(list1), 'utf-8'))
    list2_bytes = list(bytes(''.join(list2), 'utf-8'))

    sm = difflib.SequenceMatcher(None, list1_bytes, list2_bytes)
    similarity = sm.ratio()

    return similarity


def mapping(text_results, bossname_list):
    """
    보스 이름과 매칭되는 남은 시간을 찾는 함수
    이미지상 보스 이름과 해당 보스의 남은 시간이 서로 가장 가깝게 위치함.
    find_boss_name()에서 보스 이름이 나왔다고 하면, 그것과 가장 가까운 텍스트 영역을 찾음. 텍스트 디텍트가 제대로 되었다면, 아마도 남은 시간일 것

    :param text_results:
    :return:
    """
    mapped_data = []
    for i in range(len(text_results)):
        boss_name = find_boss_name(text_results[i][1], bossname_list)
        if boss_name is None:
            continue

        #print('origin: ', text_results[i][1], ' mapped: ', boss_name)

        nearest_index = get_nearest_box_index(text_results, i, 0, 'right,bottom')
        if nearest_index > -1:
            mapped_data.append([boss_name, text_results[nearest_index][1].replace("0 ", "", 1)])    # 남은 시간의 젤 앞 시계 이모티콘을 숫자 '0' 으로 인식하기도 함. 그 부분 제거

    return mapped_data


def find_boss_name(origin_name, bossname_list):
    """
    보스 이름을 정확한 이름으로 변환
    일반적이지 않은 이름이라 한두글자씩 틀리게 인식됨.
    정확한 이름을 리스트에 넣은 후, 인식된 이름과 가장 유사한 정확한 보스 이름 선정
    :param origin_name:
    :return:
    """
    boss_names = ['혼돈의마수굴베이그', '혼돈의사제강글로티', '분노의모네가름', '나태의드라우그', '그로아의사념', '헤르모드의사념', '야른의사념', '굴베이그의사념', '파>프니르의그림자', '그로아', '칼바람하피', '매트리악', '레라드', '탕그뇨스트', '갸름', '티르', '파르바', '셀로비아', '흐니르', '페티', '바우티', '니드호그', '야른', '발두르', '토르', '라이노르', '비요른', '헤르모드', '스칼라니르', '브륀힐드', '라타토스크', '수드리', '파프니르', '오딘', '스바르트', '두라스로르', '모네가름', '드라우그', '굴베이그', '아우둠라', '수르트', '메기르', '신마라', '헤르가름', '탕그리스니르', '엘드룬', '우로보로스', '헤임달', '미미르', '발리', '노트', '샤무크', '스칼드메르', '화신그로아']

    name = list(origin_name)

    max_similarity = 0
    max_index = -1
    for i in range(len(bossname_list)):
        boss_name = list(bossname_list[i])

        similarity = bytes_similarity(name, boss_name)
        if similarity > max_similarity:
            max_similarity = similarity
            max_index = i

    #if max_index >= 0:
    #    print('origin: ', origin_name, ' target: ', boss_names[max_index], ' similarity: ', max_similarity)

    # 가장 유사한 이름과의 유사도가 0.55 미만이라면 무시 (예를 들면, '5시간 37분 남음' 같은 것들)
    return bossname_list[max_index] if max_similarity >= 0.55 else None


def get_ocr_boss_time_list_by_bytes(image_bytes: bytes, bossname_list) -> (str, list):
    """

    :param image_bytes:
    :param bossname_list:
    :return:
    """
    # 시계 아이콘 제거 전처리
    new_image_bytes = remove_invalid_areas(image_bytes)

    # OCR 수행
    # text_results = read_text(image_bytes)
    text_results = read_text(new_image_bytes)

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
