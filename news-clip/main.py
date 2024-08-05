import os
from scrap import Scrap
from news_summarizer import NewsSummarizer

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
    # artdic_lst = scraper.collect_articles(all_hrefs)
    #
    # # DataFrame 생성
    # art_df = scraper.to_dataframe(artdic_lst)
    #
    # # DataFrame을 CSV 파일로 저장
    # art_df.to_csv("article_df.csv", index=False, encoding='utf-8-sig')
    # print("CSV 파일 저장 완료: article_df.csv")

    # 뉴스 요약 작업
    API_KEY = os.getenv("OPENAI_API_KEY")
    summarizer = NewsSummarizer(api_key=API_KEY)

    # 기사 요약
    summaries = summarizer.summarize_articles_from_csv("article_df.csv")

    # 요약 결과를 CSV 파일로 저장
    summarizer.save_summaries_to_csv(summaries, "summary_df.csv")

    print("뉴스 요약 완료: summary_df.csv")
