import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

# 네이버 뉴스 카테고리 URL
BASE_URL = "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1="
CATEGORIES = {
    "정치": "100",
    "경제": "101",
    "사회": "102",
    "생활/문화": "103",
    "세계": "104",
    "IT/과학": "105"
}


def ex_tag(sid, page):
    """뉴스 분야(sid)와 페이지(page)를 입력하면 링크들을 리스트로 추출하는 함수"""
    url = f"https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={sid}&page={page}"
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(html.text, "lxml")
    a_tag = soup.find_all("a")

    tag_lst = []
    for a in a_tag:
        if "href" in a.attrs and f"sid={sid}" in a["href"] and "article" in a["href"]:
            tag_lst.append(a["href"])

    return tag_lst


def re_tag(sid):
    """특정 분야의 100페이지까지의 뉴스의 링크를 수집하여 중복 제거한 리스트로 변환하는 함수"""
    re_lst = []
    for i in tqdm(range(100)):
        lst = ex_tag(sid, i + 1)
        re_lst.extend(lst)

    # 중복 제거
    re_set = set(re_lst)
    re_lst = list(re_set)

    return re_lst


def art_crawl(all_hrefs, sid, index):
    """
    sid와 링크 인덱스를 넣으면 기사제목, 날짜, 본문을 크롤링하여 딕셔너리를 출력하는 함수

    Args:
        all_hrefs(dict): 각 분야별로 100페이지까지 링크를 수집한 딕셔너리 (key: 분야(sid), value: 링크)
        sid(int): 분야 [100: 정치, 101: 경제, 102: 사회, 103: 생활/문화, 104: 세계, 105: IT/과학]
        index(int): 링크의 인덱스

    Returns:
        dict: 기사제목, 날짜, 본문이 크롤링된 딕셔너리
    """
    art_dic = {}

    title_selector = "h2.media_end_head_headline"
    date_selector = ".media_end_head_info_datestamp_time"
    main_selector = "#dic_area"

    url = all_hrefs[sid][index]
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(html.text, "lxml")

    # 제목 수집
    title = soup.select_one(title_selector).get_text(strip=True) if soup.select_one(title_selector) else 'N/A'

    # 날짜 수집
    date = soup.select_one(date_selector).get_text(strip=True) if soup.select_one(date_selector) else 'N/A'

    # 본문 수집
    main = soup.select_one(main_selector).get_text(strip=True) if soup.select_one(main_selector) else 'N/A'

    art_dic["title"] = title
    art_dic["date"] = date
    art_dic["main"] = main

    return art_dic


if __name__ == "__main__":
    all_hrefs = {}

    # 모든 섹션의 링크 수집
    for category, code in CATEGORIES.items():
        print(f"Collecting links for {category}...")
        all_hrefs[int(code)] = re_tag(code)

    # 모든 섹션의 데이터 수집 (제목, 날짜, 본문, section, url)
    artdic_lst = []
    for section in tqdm(range(100, 106)):
        print(f"Collecting articles for section {section}...")
        for i in tqdm(range(len(all_hrefs[section]))):
            try:
                art_dic = art_crawl(all_hrefs, section, i)
                art_dic["section"] = section
                art_dic["url"] = all_hrefs[section][i]
                artdic_lst.append(art_dic)
            except Exception as e:
                print(f"Error scraping article {i} in section {section}: {e}")

    # DataFrame 생성
    art_df = pd.DataFrame(artdic_lst)

    # DataFrame을 콘솔에 출력
    print(art_df.head())

    # DataFrame을 CSV 파일로 저장
    art_df.to_csv("article_df.csv", index=False, encoding='utf-8-sig')
    print("CSV 파일 저장 완료: article_df.csv")
