import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from konlpy.tag import Okt
import re
import random
from colorsys import hsv_to_rgb
import os  # 추가: 파일 경로를 처리하기 위해 필요


def generate_color_func(hue_min, hue_max):
    """지정된 Hue 범위에 따라 색상을 생성하는 함수"""

    def color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        hue = random.uniform(hue_min, hue_max)
        saturation = random.uniform(0.55, 0.85)  # 높은 채도 유지
        lightness = random.uniform(0.6, 0.8)  # 밝게 설정

        r, g, b = hsv_to_rgb(hue, saturation, lightness)
        return f"rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})"

    return color_func


class WordCloudGenerator:
    def __init__(self, csv_file, font_path=None, output_image='../output/wordcloud.png'):
        self.csv_file = csv_file
        self.font_path = font_path
        self.output_image = output_image
        self.okt = Okt()
        self.exclude_words = ["대해", "라며", "지난", "기자", "오늘", "내일", "어제", "위해", "때문", "연합뉴스", "이후", "지금", "관련", "통해",
                              "제공"]

        # 다양한 톤의 색상 팔레트 정의
        self.color_palettes = {
            'red': generate_color_func(0.0, 0.2),  # 붉은 톤
            'orange': generate_color_func(0.1, 0.3),  # 주황 톤
            'yellow': generate_color_func(0.2, 0.4),  # 노란 톤
            'green': generate_color_func(0.3, 0.5),  # 초록 톤
            'cyan': generate_color_func(0.4, 0.6),  # 청록 톤
            'blue': generate_color_func(0.5, 0.7),  # 파란 톤
            'purple': generate_color_func(0.6, 0.8),  # 보라 톤
            'pink': generate_color_func(0.7, 0.9),  # 핑크 톤
            'brown': generate_color_func(0.05, 0.25),  # 갈색 톤
            'magenta': generate_color_func(0.8, 1.0)  # 마젠타 톤
        }

    def preprocess_text(self, text):
        # 특수 문자 제거
        text = re.sub(r'[^\w\s]', '', text)

        # 형태소 분석을 통해 명사만 추출
        nouns = self.okt.nouns(text)

        # 1글자짜리 명사는 의미 없는 경우가 많아 제거
        nouns = [noun for noun in nouns if len(noun) > 1]

        # 제외할 단어 필터링
        nouns = [noun for noun in nouns if noun not in self.exclude_words]

        # 다시 하나의 문자열로 결합
        return ' '.join(nouns)

    def generate_wordcloud(self):
        # CSV 파일에서 데이터 불러오기
        df = pd.read_csv(self.csv_file)

        # 'main' 열의 텍스트를 모두 연결하여 하나의 문자열로 만듦
        text = " ".join(df['main'].tolist())

        # 전처리 수행
        processed_text = self.preprocess_text(text)

        # 워드 클라우드 생성
        selected_palette_name = random.choice(list(self.color_palettes.keys()))
        selected_color_func = self.color_palettes[selected_palette_name]
        wordcloud = WordCloud(font_path=self.font_path, width=1600, height=800, background_color='white',
                              collocations=False, max_words=80, scale=10, max_font_size=200,
                              color_func=selected_color_func).generate(processed_text)

        # 워드 클라우드 이미지 파일로 저장
        wordcloud.to_file(self.output_image)
        print(f"워드 클라우드 이미지가 {self.output_image} 파일로 저장되었습니다.")

        # 워드 클라우드 출력 (옵션)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
