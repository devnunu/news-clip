import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm

class Scrap:
    BASE_URL = "https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1="
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(self, categories):
        """
        :param categories: 카테고리와 카테고리 코드를 포함하는 딕셔너리
        """
        self.categories = categories

    def ex_tag(self, sid):
        """뉴스 분야(sid)와 페이지(page)를 입력하면 링크들을 리스트로 추출하는 함수"""
        url = f"{self.BASE_URL}{sid}"
        html = requests.get(url, headers=self.HEADERS)

        # BeautifulSoup로 HTML 파싱
        soup = BeautifulSoup(html.text, "html.parser")  # Use 'lxml' if you have it installed

        # 모든 <a> 태그 찾기
        a_tags = soup.find_all("a", href=True)  # href 속성이 있는 것만 찾기

        tag_lst = []
        for a in a_tags:
            href = a["href"]

            # 새로운 조건: 링크가 https://n.news.naver.com/mnews/article/로 시작하는지 확인
            if href.startswith("https://n.news.naver.com/mnews/article/"):
                # 'comment'가 경로에 포함되지 않는지 확인
                if "/comment/" not in href:
                    # 'article' 뒤의 숫자 경로 형식을 확인 (단순한 형식 확인)
                    path_parts = href.split('/')
                    if len(path_parts) >= 6 and path_parts[-2].isdigit() and path_parts[-1].isdigit():
                        tag_lst.append(href)

        return tag_lst

    def re_tag(self, sid):
        """특정 분야의 1페이지까지의 뉴스의 링크를 수집하여 중복 제거한 리스트로 변환하는 함수"""
        re_lst = []
        lst = self.ex_tag(sid)
        re_lst.extend(lst)

        # 중복 제거
        re_set = set(re_lst)
        re_lst = list(re_set)

        return re_lst

    def art_crawl(self, all_hrefs, sid, index):
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
        html = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(html.text, "html.parser")  # Use 'lxml' if you have it installed

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

    def collect_all_hrefs(self):
        """
        모든 카테고리에서 기사 링크를 수집하는 함수
        Returns:
            dict: 카테고리 코드와 해당 카테고리의 기사 링크 목록이 저장된 딕셔너리
        """
        all_hrefs = {}
        for category, code in self.categories.items():
            print(f"Collecting links for {category}...")
            all_hrefs[int(code)] = self.re_tag(code)
        return all_hrefs

    def collect_articles(self, all_hrefs):
        """
        모든 섹션의 기사 데이터를 수집하는 함수
        Args:
            all_hrefs (dict): 카테고리 코드와 해당 카테고리의 기사 링크 목록이 저장된 딕셔너리
        Returns:
            list: 모든 섹션의 기사 데이터가 저장된 리스트
        """
        artdic_lst = []
        for section in tqdm(range(100, 106)):
            print(f"Collecting articles for section {section}...")
            for i in tqdm(range(len(all_hrefs[section]))):
                try:
                    art_dic = self.art_crawl(all_hrefs, section, i)
                    art_dic["section"] = section
                    art_dic["url"] = all_hrefs[section][i]
                    artdic_lst.append(art_dic)
                except Exception as e:
                    print(f"Error scraping article {i} in section {section}: {e}")
        return artdic_lst

    def to_dataframe(self, artdic_lst):
        """
        기사 데이터를 DataFrame으로 변환하는 함수
        Args:
            artdic_lst (list): 기사 데이터가 저장된 리스트
        Returns:
            pd.DataFrame: 기사 데이터를 담고 있는 데이터프레임
        """
        # 기사 데이터를 DataFrame으로 변환
        art_df = pd.DataFrame(artdic_lst)

        # 섹션별로 그룹화한 후, 각 섹션에서 10개의 기사만 선택
        top_articles = art_df.groupby('section').head(10).reset_index(drop=True)

        return top_articles

