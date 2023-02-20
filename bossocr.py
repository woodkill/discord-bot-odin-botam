import cv2
import easyocr
import numpy as np
import math


'''
pip3 install opencv-python
pip3 install easyocr
'''



'''
원본 이미지에서 특정 영역의 색상값만 남기고 나머지 영역은 삭제
'''
def remove_background(file_name):
    image = cv2.imread(file_name)
    # image는 RGB 채널이 아니라 BGR 채널임 (opencv 디폴트 채널 순서)

    # 남은 시간 색상 범위 (Blue, Green, Red)
    lower = np.array([110, 90, 5])
    upper = np.array([255, 220, 60])

    # 해당 색상 범위의 영역만 mask로 추출
    img_mask = cv2.inRange(image, lower, upper)
    #cv2.imwrite('./mask.png', img_mask)

    # 오렌지색
    lower = np.array([15, 55, 145])
    upper = np.array([40, 130, 245])

    img_mask3 = cv2.inRange(image, lower, upper)
    #cv2.imwrite('./mask.png', img_mask3)

    # 노랑이
    lower = np.array([20, 110, 130])
    upper = np.array([46, 210, 255])

    img_mask4 = cv2.inRange(image, lower, upper)

    # 보스 이름을 뽑기 위한 흰색 범위 (BGR)
    lower = np.array([160, 160, 160])
    upper = np.array([255, 255, 255])

    img_mask2 = cv2.inRange(image, lower, upper)

    # 뽑은 색상 영역 mask를 다 합친 후 원본 image 이미지와 and 연산.
    mask = img_mask + img_mask2 + img_mask3 + img_mask4

    result = cv2.bitwise_and(image, image, mask=mask)
    cv2.imwrite('text_only.png', result)    # 디버깅용

    return result

'''
easyocr 을 이용해 이미지에서 한글 텍스트를 출력.
출력된 결과물 중 confidence값이 0.15 미만인 결과는 삭제.
디텍트 되는 결과물 중 원하는 텍스트가 없다면, confidence 값 조절 가능.
'''
def read_text(image):
    reader = easyocr.Reader(['ko'])
    raw_result = reader.readtext(image)

    #print(raw_result)

    filtered = []

    for i in range(len(raw_result)):
        if raw_result[i][2] < 0.15:
            continue
        filtered.append(raw_result[i])

    return filtered

'''
단어의 유사도 측정
자카드 방식 (원하는 결과가 잘 나오지 않으면, 다른 유사도 측정 방식으로 변경 가능)
https://blog.naver.com/dsgsengy/222801301771
'''
def jaccard_similarity(list1, list2):
    s1 = set(list1)
    s2 = set(list2)
    return float(len(s1.intersection(s2)) / len(s1.union(s2)))

'''
보스 이름을 정확한 이름으로 변환
일반적이지 않은 이름이라 한두글자씩 틀리게 인식됨.
정확한 이름을 리스트에 넣은 후, 인식된 이름과 가장 유사한 정확한 보스 이름 선정
'''
def find_boss_name(name):
    boss_names = ['그로아', '매트리악', '탕그뇨스트', '칼바람 하피', '레라드', '파르바', '흐니르', '바우티', '야른', '셀로비아', '페티', '니드호그', '티르', '라이노르', '헤르모드', '브륀힐드', '수드리', '비요른', '스칼라니르', '라타토스크', '토르'] # 보스 이름 전부 추가 필요
    ignore_names = ['현재 시간', '노른의 시간표', '미드가르드', '요툰하임', '니다벨리르', '던전', '거점 지배자', '대륙 침략자', '발할라 대전']

    name = list(name)

    for i in range(len(ignore_names)):
        ignore_name = list(ignore_names[i])

        if jaccard_similarity(name, ignore_name) > 0.5:
            return None

    max_similarity = 0
    max_index = -1
    for i in range(len(boss_names)):
        boss_name = list(boss_names[i])

        similarity = jaccard_similarity(name, boss_name)
        if similarity > max_similarity:
            max_similarity = similarity
            max_index = i

    # 가장 유사한 이름과의 유사도가 0.2 이하라면 무시 (예를 들면, '5시간 37분 남음' 같은 것들)
    return boss_names[max_index] if max_similarity > 0.2 else None

'''
두점의 거리 계산
'''
def distance_boxes(box1, box2):
    center1 = [(box1[1][0] - box1[0][0]) / 2 + box1[0][0], (box1[1][1] - box1[0][1]) / 2 + box1[0][1]]
    center2 = [(box2[1][0] - box2[0][0]) / 2 + box2[0][0], (box2[1][1] - box2[0][1]) / 2 + box2[0][1]]

    return math.sqrt((center2[0] - center1[0])**2 + (center2[1] - center1[1])**2)

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

        nearest_index = -1
        nearest_distance = 100000
        for k in range(i + 1, len(text_results)):
            distance = distance_boxes(text_results[i][0], text_results[k][0])
            if distance < nearest_distance:
                nearest_index = k
                nearest_distance = distance

        if nearest_index > -1:
            mapped_data.append([boss_name, text_results[nearest_index][1].replace("0 ", "", 1)])    # 남은 시간의 젤 앞 시계 이모티콘을 숫자 '0' 으로 인식하기도 함. 그 부분 제거

    return mapped_data



# 이미지에서 관심있는 영역만 남김
image = remove_background('./odin4.png')
# OCR 수행
text_results = read_text(image)

#print(text_results)

# OCR로 추출된 텍스트들의 관계 정리
final_results = mapping(text_results)
print(final_results)
