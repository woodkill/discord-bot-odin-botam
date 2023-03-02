import cv2
import easyocr
import numpy as np
import math
import difflib

'''
pip3 install opencv-python
pip3 install easyocr
'''

def remove_background(image):
    """
    원본 이미지에서 특정 영역의 색상값만 남기고 나머지 영역은 삭제
    :param image: 읽은 이미지
    :return:
    """

    # 남은 시간 색상 범위 (Blue, Green, Red)
    lower = np.array([110, 90, 5])
    upper = np.array([255, 220, 60])

    # 해당 색상 범위의 영역만 mask로 추출
    img_mask = cv2.inRange(image, lower, upper)
    #cv2.imwrite('./mask.png', img_mask)

    # 오렌지색
    lower = np.array([0, 50, 110])
    upper = np.array([20, 140, 255])

    img_mask3 = cv2.inRange(image, lower, upper)
    #cv2.imwrite('./mask3.png', img_mask3)

    # 노랑이
    lower = np.array([0, 110, 160])
    upper = np.array([10, 215, 255])

    img_mask4 = cv2.inRange(image, lower, upper)

    # 보스 이름을 뽑기 위한 흰색 범위 (BGR)
    lower = np.array([130, 130, 130])
    upper = np.array([255, 255, 255])

    img_mask2 = cv2.inRange(image, lower, upper)

    # 뽑은 색상 영역 mask를 다 합친 후 원본 image 이미지와 and 연산.
    mask = img_mask + img_mask2 + img_mask3 + img_mask4

    result = cv2.bitwise_and(image, image, mask=mask)
    # cv2.imwrite('text_only.png', result)    # 디버깅용

    return result


def read_text(image):
    """
    easyocr 을 이용해 이미지에서 한글 텍스트를 출력.
    출력된 결과물 중 confidence값이 0.15 미만인 결과는 삭제.
    디텍트 되는 결과물 중 원하는 텍스트가 없다면, confidence 값 조절 가능.
    :param image:
    :return:
    """
    reader = easyocr.Reader(['ko'])
    raw_result = reader.readtext(image)

    #print(raw_result)

    filtered = []

    for i in range(len(raw_result)):
        if raw_result[i][2] < 0.07:
            continue
        filtered.append(raw_result[i])

    #print(filtered)

    return filtered


def jaccard_similarity(list1, list2):
    """
    단어의 유사도 측정
    자카드 방식 (원하는 결과가 잘 나오지 않으면, 다른 유사도 측정 방식으로 변경 가능)
    https://blog.naver.com/dsgsengy/222801301771
    :param list1:
    :param list2:
    :return:
    """
    s1 = set(list1)
    s2 = set(list2)
    return float(len(s1.intersection(s2)) / len(s1.union(s2)))


def bytes_similarity(list1, list2):
    list1_bytes = list(bytes(''.join(list1), 'utf-8'))
    list2_bytes = list(bytes(''.join(list2), 'utf-8'))

    sm = difflib.SequenceMatcher(None, list1_bytes, list2_bytes)
    similarity = sm.ratio()
    
    return similarity


def delete_invalid_names(text_results):
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

            if bytes_similarity(source_name, ignore_name) > 0.7:
                ignore = True
                #print('(deleted) ', text_results[i][1], ' ignore_name: ', ignore_names[j], ' similarity: ', bytes_similarity(source_name, ignore_name))
                break

        if ignore == False:
            new_results.append(text_results[i])

    return new_results
            

def find_boss_name(origin_name, bossname_list):
    """
    보스 이름을 정확한 이름으로 변환
    일반적이지 않은 이름이라 한두글자씩 틀리게 인식됨.
    정확한 이름을 리스트에 넣은 후, 인식된 이름과 가장 유사한 정확한 보스 이름 선정
    :param origin_name:
    :param bossname_list:
    :return:
    """

    # TODO: 이거 서버DB에서 받아온걸로 교체해야 한다.
    # bossname_list = ['혼돈의마수굴베이그', '혼돈의사제강글로티', '분노의모네가름', '나태의드라우그', '그로아의사념', '헤르모드의사념', '야른의사념', '굴베이그의사념', \
    #               '파프니르의그림자', '그로아', '칼바람하피', '매트리악', '레라드', '탕그뇨스트', '갸름', '티르', '파르바', '셀로비아', '흐니르', '페티', '바우티', \
    #               '니드호그', '야른', '발두르', '토르', '라이노르', '비요른', '헤르모드', '스칼라니르', '브륀힐드', '라타토스크', '수드리', '파프니르', '오딘', '스바르트',\
    #               '두라스로르', '모네가름', '드라우그', '굴베이그', '아우둠라', '수르트', '메기르', '신마라', '헤르가름', '탕그리스니르', '엘드룬', '우로보로스', '헤임달', \
    #               '미미르', '발리', '노트', '샤무크', '스칼드메르', '화신그로아']

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


def get_nearest_box_index(text_results, base_index, vertical_weight):
    """

    :param text_results:
    :param base_index:
    :param vertical_weight:
    :return:
    """
    nearest_index = -1
    nearest_distance = 1000000
    for i in range(len(text_results)):
        if i == base_index:
            continue

        distance = distance_boxes(text_results[base_index][0], text_results[i][0])
        if vertical_weight > 0:
            distance += vertical_distance_boxes(text_results[base_index][0], text_results[i][0]) * vertical_weight

        if distance < nearest_distance:
            nearest_index = i
            nearest_distance = distance

    return nearest_index


def find_current_time(text_results):
    """
    현재 시간 추출
    :param text_results:
    :return:
    """
    current_time_text = list('현재 시간')
    for i in range(len(text_results)):
        text = list(text_results[i][1])
        if bytes_similarity(current_time_text, text) < 0.8:
            continue

        nearest_index = get_nearest_box_index(text_results, i, 20)
        if nearest_index < 0:
            return None

        return text_results[nearest_index][1]

    return None


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


def mapping(text_results, bossname_list):
    """
    보스 이름과 매칭되는 남은 시간을 찾는 함수
    이미지상 보스 이름과 해당 보스의 남은 시간이 서로 가장 가깝게 위치함.
    find_boss_name()에서 보스 이름이 나왔다고 하면, 그것과 가장 가까운 텍스트 영역을 찾음. 텍스트 디텍트가 제대로 되었다면, 아마도 남은 시간일 것
    :param text_results:
    :param bossname_list:
    :return:
    """

    mapped_data = []
    for i in range(len(text_results)):
        boss_name = find_boss_name(text_results[i][1], bossname_list)
        if boss_name is None:
            continue

        #print('origin: ', text_results[i][1], ' mapped: ', boss_name)

        nearest_index = get_nearest_box_index(text_results, i, 0)
        if nearest_index > -1:
            mapped_data.append([boss_name, text_results[nearest_index][1].replace("0 ", "", 1)])    # 남은 시간의 젤 앞 시계 이모티콘을 숫자 '0' 으로 인식하기도 함. 그 부분 제거

    return mapped_data


def get_ocr_boss_time_list_by_file(file_path: str, bossname_list) -> (str, list):
    """

    :param file_path:
    :param bossname_list:
    :return:
    """

    image = cv2.imread(file_path)

    # 이미지에서 관심있는 영역만 남김
    image = remove_background(image)

    # OCR 수행
    text_results = read_text(image)

    #print(text_results)

    # 이미지 좌상단 현재 시간 추출
    current_time = find_current_time(text_results)
    # print('현재 시간: ', current_time)

    # OCR로 추출된 텍스트들의 관계 정리
    text_results = delete_invalid_names(text_results)
    #print(text_results)
    final_results = mapping(text_results, bossname_list)
    # print(final_results)

    return current_time, final_results


def get_ocr_boss_time_list_by_bytes(image_bytes: bytes, bossname_list) -> (str, list):
    """

    :param image_bytes:
    :param bossname_list:
    :return:
    """


    image_np = np.frombuffer(image_bytes, np.uint8)
    img_np = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

    # 이미지에서 관심있는 영역만 남김
    image = remove_background(img_np)

    # image는 RGB 채널이 아니라 BGR 채널임 (opencv 디폴트 채널 순서)

    # OCR 수행
    text_results = read_text(image)

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
    for boss_time_pair in final_results:
        # 보스명 및 남은시간에 스페이스 있으면 제거
        boss_time_pair[0] = boss_time_pair[0].replace(" ", "")
        boss_time_pair[1] = boss_time_pair[1].replace(" ", "")
        boss_time_pair[1] = boss_time_pair[1].replace("남음", "")

    return screenshot_time, final_results
