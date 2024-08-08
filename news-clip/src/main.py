import os
from scrap import Scrap
from news_summarizer import NewsSummarizer
from wordcloud_generator import WordCloudGenerator

# 상수 정의
API_KEY = os.getenv("OPENAI_API_KEY")

# Scrape
CATEGORIES = {
        "정치": "100",
        "경제": "101",
        "사회": "102",
        "생활/문화": "103",
        "세계": "104",
        "IT/과학": "105"
    }
ARTICLE_CSV = 'article_df.csv'

# Word cloud
OUTPUT_IMAGE = 'wordcloud.png'
FONT_PATH = os.path.join('../font', 'NanumBarunGothic.ttf')

# AI Summary
SUMMARIZED_CSV = 'summarized_articles.csv'
TOP_ARTICLES_CSV = 'top_articles.csv'
TOP_N = 3

if __name__ == "__main__":
    # # Scrap 클래스 인스턴스 생성 및 스크래핑 시작
    # scraper = Scrap(CATEGORIES, ARTICLE_CSV)
    # scraper.scrap(max_workers=10)

    # WordCloudGenerator 클래스 인스턴스 생성
    wc_generator = WordCloudGenerator(csv_file=ARTICLE_CSV, output_image=OUTPUT_IMAGE, font_path=FONT_PATH)

    # 워드 클라우드 생성 및 출력
    wc_generator.generate_wordcloud()

    # # 뉴스 요약 작업
    # summarizer = NewsSummarizer(api_key=API_KEY)
    #
    # top_articles = summarizer.summarize_and_select_top_articles(ARTICLE_CSV, SUMMARIZED_CSV, TOP_ARTICLES_CSV,
    #                                                             top_n=TOP_N)
    # print(f"\033[95m뉴스 요약 및 중요 기사 선별 완료.\033[0m")
    #
    # # 병합된 summary 내용 출력
    # summarizer.print_merged_content(TOP_ARTICLES_CSV)


