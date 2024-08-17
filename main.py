import os
from src.scrap.scrap import Scrap
from src.gpt.news_summarizer import NewsSummarizer
from src.gpt.news_filter import NewsFilter
from src.gpt.news_review import NewsReview
from src.wordcloud.wordcloud_generator import WordCloudGenerator
from src.slack.slack_notifier import SlackNotifier
from datetime import datetime
import pandas as pd
import pytz

# 한국 시간(KST) 타임존 설정
kst = pytz.timezone('Asia/Seoul')

# 상수 정의
API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
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
FONT_PATH = os.path.join('font', 'NanumBarunGothic.ttf')

# AI Summary
SUMMARIZED_CSV = os.path.join(OUTPUT_DIR, 'summarized_articles.csv')
TOP_ARTICLES_CSV = os.path.join(OUTPUT_DIR, 'top_articles.csv')
TOP_N = 3

def reduce_articles_by_section(input_csv, output_csv, n):
    """
    해당 메서드는 너무 많은 AI 호출을 줄이기 위해 csv 전처리 용으로 사용하는 테스트 메서드입니다.
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

    """
    뉴스 스크래핑
    """
    # Scrap 클래스 인스턴스 생성 및 스크래핑 시작
    scraper = Scrap(CATEGORIES, ARTICLE_CSV)
    scraper.scrap(max_workers=10)

    """
    스크래핑 결과 전처리 - 섹션별로 20개의 기사만 추출합니다.
    """
    reduce_articles_by_section(ARTICLE_CSV, ARTICLE_CSV, 20)

    # """
    # 워드 클라우드 이미지 생성
    # """
    # # WordCloudGenerator 클래스 인스턴스 생성
    # wc_generator = WordCloudGenerator(csv_file=ARTICLE_CSV, output_image=OUTPUT_IMAGE, font_path=FONT_PATH)
    #
    # # 워드 클라우드 생성 및 출력
    # wc_generator.generate_wordcloud()

    """
    뉴스 요약 작업
    """
    # NewsSummarizer 인스턴스 생성
    summarizer = NewsSummarizer(api_key=API_KEY)
    summarizer.summarize_articles(ARTICLE_CSV, SUMMARIZED_CSV)

    """
    주요 뉴스 필터링
    """
    # NewsFilter 인스턴스 생성
    news_filter = NewsFilter(api_key=API_KEY)
    news_filter.filter_top_articles(SUMMARIZED_CSV, TOP_ARTICLES_CSV, top_n=TOP_N)

    print(f"\033[95m뉴스 요약 및 중요 기사 선별 완료.\033[0m")

    """
    병합된 summary 내용 출력 및 한줄 평 생성
    """
    merged_content = news_filter.print_merged_content(TOP_ARTICLES_CSV)
    news_review = NewsReview(api_key=API_KEY)
    one_line_review = news_review.generate_one_line_review(merged_content)

    """
    슬랙 메세지 전송
    """
    # SlackNotifier 인스턴스 생성
    notifier = SlackNotifier(WEBHOOK_URL)

    # 오늘의 날짜를 동적으로 생성
    today_date = datetime.now(kst).strftime("%m월 %d일")

    # 기본 메시지 텍스트 생성
    message = f"*:hatched_chick:  [깐추리가 알려주는 {today_date} 간추린 아침뉴스]*\n\n"

    # 합칠 내용들 가져오기 (예: merged_content 및 one_line_review)
    one_line_review_formatted = f"*:baby_chick: [깐추리의 뉴스 요약!]*\n\n*_{one_line_review}_*"
    final_message = message + merged_content + "\n\n\n" + one_line_review_formatted

    # 메시지와 함께 이미지 전송
    notifier.send_message(final_message)
    print("\033[92m뉴스 요약 작업 완료\033[0m")

