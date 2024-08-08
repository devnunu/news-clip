import os
from scrap import Scrap
from news_summarizer import NewsSummarizer

# 상수 정의
API_KEY = os.getenv("OPENAI_API_KEY")
ARTICLE_CSV = 'article_df.csv'
SUMMARIZED_CSV = 'summarized_articles.csv'
TOP_ARTICLES_CSV = 'top_articles.csv'
TOP_N = 3

if __name__ == "__main__":
    # # 카테고리 정의
    # CATEGORIES = {
    #     "정치": "100",
    #     "경제": "101",
    #     "사회": "102",
    #     "생활/문화": "103",
    #     "세계": "104",
    #     "IT/과학": "105"
    # }
    #
    # # Scrap 클래스 인스턴스 생성
    # scraper = Scrap(CATEGORIES)
    #
    # # 모든 섹션의 링크 수집
    # all_hrefs = scraper.collect_all_hrefs()
    #
    # # 모든 섹션의 데이터 수집 (제목, 날짜, 본문, section, url)
    # # max_workers 값을 조정하여 병렬 처리의 스레드 수를 설정
    # artdic_lst = scraper.collect_articles(all_hrefs, max_workers=10)
    #
    # # DataFrame 생성
    # art_df = scraper.to_dataframe(artdic_lst)
    #
    # # DataFrame을 CSV 파일로 저장
    # art_df.to_csv(ARTICLE_CSV, index=False, encoding='utf-8-sig')
    # print(f"CSV 파일 저장 완료: {ARTICLE_CSV}")

    # 뉴스 요약 작업
    summarizer = NewsSummarizer(api_key=API_KEY)

    top_articles = summarizer.summarize_and_select_top_articles(ARTICLE_CSV, SUMMARIZED_CSV, TOP_ARTICLES_CSV,
                                                                top_n=TOP_N)
    print(f"\033[95m뉴스 요약 및 중요 기사 선별 완료.\033[0m")

    # 병합된 summary 내용 출력
    summarizer.print_merged_content(TOP_ARTICLES_CSV)


