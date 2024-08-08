import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


class Scrap:
    HEADERS = {"User-Agent": "Mozilla/5.0"}

    def __init__(self, categories):
        """
        :param categories: 카테고리와 카테고리 코드를 포함하는 딕셔너리
        """
        self.categories = categories

    def ex_tag(self, html_content):
        """HTML에서 기사 링크들을 리스트로 추출하는 함수"""
        # BeautifulSoup로 HTML 파싱
        soup = BeautifulSoup(html_content, "html.parser")

        # 모든 <a> 태그에서 기사 링크 추출
        a_tags = soup.find_all("a", href=True)

        tag_lst = []
        for a in a_tags:
            href = a["href"]
            if href.startswith("https://n.news.naver.com/mnews/article/") and "/comment/" not in href:
                tag_lst.append(href)

        return tag_lst

    def fetch_category_html(self, sid):
        """주어진 섹션의 HTML 콘텐츠를 가져오는 함수"""
        url = f"https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={sid}"
        response = requests.get(url, headers=self.HEADERS)
        return response.text

    def re_tag(self, sid):
        """특정 분야의 뉴스 링크를 수집하여 중복 제거한 리스트로 변환하는 함수"""
        html_content = self.fetch_category_html(sid)
        re_lst = self.ex_tag(html_content)

        # 중복 제거
        re_set = set(re_lst)
        re_lst = list(re_set)

        return re_lst

    def art_crawl(self, url):
        """기사를 크롤링하여 제목, 날짜, 본문을 추출하는 함수"""
        art_dic = {}

        title_selector = "h2.media_end_head_headline"
        date_selector = ".media_end_head_info_datestamp_time"
        main_selector = "#dic_area"

        html = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(html.text, "html.parser")

        title = soup.select_one(title_selector).get_text(strip=True) if soup.select_one(title_selector) else 'N/A'
        date = soup.select_one(date_selector).get_text(strip=True) if soup.select_one(date_selector) else 'N/A'
        main = soup.select_one(main_selector).get_text(strip=True) if soup.select_one(main_selector) else 'N/A'

        art_dic["title"] = title
        art_dic["date"] = date
        art_dic["main"] = main
        art_dic["url"] = url

        return art_dic

    def collect_all_hrefs(self):
        """모든 카테고리에서 기사 링크를 수집하는 함수"""
        all_hrefs = {}
        for category, code in self.categories.items():
            print(f"Collecting links for {category}...")
            all_hrefs[int(code)] = self.re_tag(code)
        return all_hrefs

    def collect_articles(self, all_hrefs, max_workers=5):
        """병렬 처리를 통해 모든 섹션의 기사 데이터를 수집하는 함수"""
        artdic_lst = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for section, urls in all_hrefs.items():
                print(f"Collecting articles for section {section}...")
                for url in urls:
                    futures.append(executor.submit(self.art_crawl, url))

            for future in tqdm(as_completed(futures), total=len(futures), desc="Scraping Articles"):
                try:
                    art_dic = future.result()
                    # 기사 데이터에 올바른 section 값을 추가
                    art_dic["section"] = [section for section, urls in all_hrefs.items() if art_dic["url"] in urls][0]
                    artdic_lst.append(art_dic)
                except Exception as e:
                    print(f"Error scraping article: {e}")

        return artdic_lst

    def to_dataframe(self, artdic_lst):
        """기사 데이터를 DataFrame으로 변환하는 함수"""
        art_df = pd.DataFrame(artdic_lst)
        return art_df