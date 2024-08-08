import os
from scrap import Scrap
from news_summarizer import NewsSummarizer
from wordcloud_generator import WordCloudGenerator
import pandas as pd

# 상수 정의
API_KEY = os.getenv("OPENAI_API_KEY")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../output')

# Scrape
CATEGORIES = {
    "정치": "100",
    "경제": "101",
    "사회": "102",
    "생활/문화": "103",
    "세계": "104",
    "IT/과학": "105"
}
ARTICLE_CSV = os.path.join(OUTPUT_DIR, 'article_df.csv')

# Word cloud
OUTPUT_IMAGE = os.path.join(OUTPUT_DIR, 'wordcloud.png')
FONT_PATH = os.path.join('../font', 'NanumBarunGothic.ttf')

# AI Summary
SUMMARIZED_CSV = os.path.join(OUTPUT_DIR, 'summarized_articles.csv')
TOP_ARTICLES_CSV = os.path.join(OUTPUT_DIR, 'top_articles.csv')
TOP_N = 3


def reduce_articles_by_section(input_csv, output_csv, n):
    """
    article_df.csv를 불러와서 각 섹션별로 n개의 아이템만 추출한 후, output_csv 파일로 저장합니다.

    :param input_csv: 원본 CSV 파일 경로
    :param output_csv: 축소된 데이터를 저장할 CSV 파일 경로
    :param n: 각 섹션별로 남길 아이템의 수
    """
    # CSV 파일 읽기
    df = pd.read_csv(input_csv)

    # 각 섹션별로 n개의 아이템만 남기기
    reduced_df = df.groupby('section').head(n)

    # 결과를 CSV 파일로 저장
    reduced_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"축소된 데이터가 {output_csv}에 저장되었습니다.")


if __name__ == "__main__":
    # Output 폴더가 없으면 만들고 시작
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # # Scrap 클래스 인스턴스 생성 및 스크래핑 시작
    # scraper = Scrap(CATEGORIES, ARTICLE_CSV)
    # scraper.scrap(max_workers=10)

    # reduce_articles_by_section(ARTICLE_CSV, ARTICLE_CSV, 5)

    # # WordCloudGenerator 클래스 인스턴스 생성
    # wc_generator = WordCloudGenerator(csv_file=ARTICLE_CSV, output_image=OUTPUT_IMAGE, font_path=FONT_PATH)
    #
    # # 워드 클라우드 생성 및 출력
    # wc_generator.generate_wordcloud()

    # 뉴스 요약 작업
    summarizer = NewsSummarizer(api_key=API_KEY)

    # summarizer.summarize_and_select_top_articles(ARTICLE_CSV, SUMMARIZED_CSV, TOP_ARTICLES_CSV,
    #                                                             top_n=TOP_N)
    # print(f"\033[95m뉴스 요약 및 중요 기사 선별 완료.\033[0m")

    # 병합된 summary 내용 출력 및 한줄 평 생성
    merged_content = summarizer.print_merged_content(TOP_ARTICLES_CSV)
    summary = summarizer.generate_daily_summary(merged_content)
