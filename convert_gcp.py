from google.cloud import vision
import io
import os
import numpy as np
import math
import difflib


'''
pip3 install --upgrade google-cloud-vision
'''

'''
gcp vision ocr 을 이용해 이미지에서 한글 텍스트를 추출.
'''

gcp_credentials = "./google_cloud_platform.json"


def read_text(image):
    #os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = gcp_credentials

    client = vision.ImageAnnotatorClient()

    with io.open(image, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

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


'''
단어의 유사도 측정
자카드 방식 (원하는 결과가 잘 나오지 않으면, 다른 유사도 측정 방식으로 변경 가능)
https://blog.naver.com/dsgsengy/222801301771
'''

def jaccard_similarity(list1, list2):
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
    ignore_names = ['현재 시간', '노른의 시간표', '미드가르드', '요툰하임', '니다벨리르', '알브하임', '무스펠하임', '아스가르드', '던전', '거점 지배자', '대륙 침략자', '발할라 대전', '절대자']

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
            


'''
보스 이름을 정확한 이름으로 변환
일반적이지 않은 이름이라 한두글자씩 틀리게 인식됨.
정확한 이름을 리스트에 넣은 후, 인식된 이름과 가장 유사한 정확한 보스 이름 선정
'''
def find_boss_name(origin_name):
    boss_names = ['혼돈의마수굴베이그', '혼돈의사제강글로티', '분노의모네가름', '나태의드라우그', '그로아의사념', '헤르모드의사념', '야른의사념', '굴베이그의사념', '파>프니르의그림자', '그로아', '칼바람하피', '매트리악', '레라드', '탕그뇨스트', '갸름', '티르', '파르바', '셀로비아', '흐니르', '페티', '바우티', '니드호그', '야른', '발두르', '토르', '라이노르', '비요른', '헤르모드', '스칼라니르', '브륀힐드', '라타토스크', '수드리', '파프니르', '오딘', '스바르트', '두라스로르', '모네가름', '드라우그', '굴베이그', '아우둠라', '수르트', '메기르', '신마라', '헤르가름', '탕그리스니르', '엘드룬', '우로보로스', '헤임달', '미미르', '발리', '노트', '샤무크', '스칼드메르', '화신그로아']

    name = list(origin_name)

    max_similarity = 0
    max_index = -1
    for i in range(len(boss_names)):
        boss_name = list(boss_names[i])

        similarity = bytes_similarity(name, boss_name)
        if similarity > max_similarity:
            max_similarity = similarity
            max_index = i

    #if max_index >= 0:
    #    print('origin: ', origin_name, ' target: ', boss_names[max_index], ' similarity: ', max_similarity)

    # 가장 유사한 이름과의 유사도가 0.55 미만이라면 무시 (예를 들면, '5시간 37분 남음' 같은 것들)
    return boss_names[max_index] if max_similarity >= 0.55 else None


'''
가장 가까운 글자 박스 검출
'''
def get_nearest_box_index(text_results, base_index, vertical_weight, right_only):
    nearest_index = -1
    nearest_distance = 1000000
    for i in range(len(text_results)):
        if i == base_index:
            continue

        if right_only and text_results[base_index][0][0] > text_results[i][0][0]:
            continue

        distance = distance_boxes(text_results[base_index][0], text_results[i][0])
        if vertical_weight > 0:
            distance += vertical_distance_boxes(text_results[base_index][0], text_results[i][0]) * vertical_weight

        if distance < nearest_distance:
            nearest_index = i
            nearest_distance = distance

    return nearest_index


'''
현재 시간 추출
'''
def find_current_time(text_results):
    for i in range(len(text_results)):
        if text_results[i][1].startswith('현재 시간'):
            if len(text_results[i][1]) > 10:
                return text_results[i][1].replace('현재 시간', '').strip()
            else:
                nearest_index = get_nearest_box_index(text_results, i, 20, False)
                if nearest_index < 0:
                    return None
                return text_results[nearest_index][1]

    return None


'''
두점의 거리 계산
'''
def distance_boxes(box1, box2):
    center1 = [(box1[1][0] - box1[0][0]) / 2 + box1[0][0], (box1[1][1] - box1[0][1]) / 2 + box1[0][1]]
    center2 = [(box2[1][0] - box2[0][0]) / 2 + box2[0][0], (box2[1][1] - box2[0][1]) / 2 + box2[0][1]]

    return math.sqrt((center2[0] - center1[0])**2 + (center2[1] - center1[1])**2)


'''
y축에 대한 거리 계산
'''
def vertical_distance_boxes(box1, box2):
    center1 = (box1[1][1] - box1[0][1]) / 2 + box1[0][1]
    center2 = (box2[1][1] - box2[0][1]) / 2 + box2[0][1]

    return abs(center1 - center2)


'''
보스 이름과 매칭되는 남은 시간을 찾는 함수
이미지상 보스 이름과 해당 보스의 남은 시간이 서로 가장 가깝게 위치함.
find_boss_name()에서 보스 이름이 나왔다고 하면, 그것과 가장 가까운 텍스트 영역을 찾음. 텍스트 디텍트가 제대로 되었다면, 아마도 남은 시간일 것
'''
def mapping(text_results):
    mapped_data = []
    for i in range(len(text_results)):
        boss_name = find_boss_name(text_results[i][1])
        if boss_name is None:
            continue

        #print('origin: ', text_results[i][1], ' mapped: ', boss_name)

        nearest_index = get_nearest_box_index(text_results, i, 0, True)
        if nearest_index > -1:
            mapped_data.append([boss_name, text_results[nearest_index][1].replace("0 ", "", 1)])    # 남은 시간의 젤 앞 시계 이모티콘을 숫자 '0' 으로 인식하기도 함. 그 부분 제거

    return mapped_data


images = ['./odin.png', './odin2.png', './odin3.png', './odin4.png', './odin5.png', './odin6.png', './odin7.png', './odin8.png', './odin9.png', './odin10.png', './odin11.png', './odin12.png', './odin13.png', './odin14.png', './odin15.png']

for image in images:
    print('image name : {}'.format(image))
    # OCR 수행
    text_results = read_text(image)

    #print(text_results)

    # OCR로 추출된 텍스트들의 관계 정리
    current_time = find_current_time(text_results)
    print('현재 시간: {}'.format(current_time))

    text_results = delete_invalid_names(text_results)

    #print(text_results)

    final_results = mapping(text_results)
    print(final_results)
