import pandas as pd
from src.util.utils import print_progress_bar
import threading
from langchain_openai import ChatOpenAI
import time

class NewsFilter:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", temperature=0)
        self.filter_completed_pages = 0
        self.lock = threading.Lock()

    def compare_importance(self, article1, article2):
        prompt = f"""
        다음 두 기사를 비교하여 더 중요한 기사를 선택해 주세요:

        기사 1: {article1['summary']}

        기사 2: {article2['summary']}

        중요성을 판단할 기준은 다음과 같습니다:
        1. 사회적 영향력: 얼마나 많은 사람들에게 영향을 미칠 가능성이 있는가?
        2. 시의성: 현재의 시점에서 얼마나 중요한가?
        3. 심각성: 다루는 이슈가 얼마나 심각한가?
        4. 독창성: 독창적이고 새로운 정보를 제공하는가?
        5. 관련성: 특정 분야나 주제에 얼마나 관련성이 있는가?

        위의 기준을 바탕으로 더 중요한 기사를 선택해 주세요.
        답변 형식: "기사 1" 또는 "기사 2"
        """
        response = self.llm.invoke(prompt).content
        return article1 if "기사 1" in response else article2

    def filter_top_articles(self, summarized_csv, output_csv, top_n=3):
        start_time = time.time()
        summaries_df = pd.read_csv(summarized_csv)
        total_sections = summaries_df['section_code'].nunique()
        total_items = total_sections * top_n
        print(f"총 {total_sections}개의 섹션에서 {total_items}개의 기사를 선별할 예정입니다.")

        top_articles = []
        grouped_df = summaries_df.groupby('section_code')

        for section, group in grouped_df:
            section_name = group['section_name'].iloc[0]  # 그룹의 첫 번째 행에서 section_name 가져오기
            print(f"[{section_name}] 섹션의 중요한 기사 선택 중...")

            articles = group.to_dict('records')
            selected_articles = []

            for _ in range(top_n):
                if len(articles) > 1:
                    top_article = self.compare_importance(articles[0], articles[1])
                    selected_articles.append(top_article)
                    articles.remove(top_article)
                elif articles:
                    selected_articles.append(articles[0])
                    break

                with self.lock:
                    self.filter_completed_pages += 1
                    print_progress_bar("기사 선별", self.filter_completed_pages, total_items)

            top_articles.extend(selected_articles)

        top_articles_df = pd.DataFrame(top_articles)
        top_articles_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\033[95m최종 선택된 기사가 {output_csv}에 저장되었습니다.\033[0m")

        elapsed_time = time.time() - start_time
        print(f"\033[95m기사 선별 작업이 완료되었습니다. 총 소요 시간: {elapsed_time:.2f}초\033[0m")

        return top_articles_df

    def print_merged_content(self, top_articles_csv):
        """
        top_articles.csv 파일의 summary 열을 가져와서 섹션별로 문자열로 병합한 후 반환합니다.
        :param top_articles_csv: 최종 선택된 기사가 저장된 CSV 파일 경로
        :return: 섹션별로 병합된 summary 내용 (문자열)
        """
        top_articles_df = pd.read_csv(top_articles_csv)

        # 섹션별로 그룹화하여 섹션 이름과 함께 summary를 병합
        sections = top_articles_df['section_name'].unique()  # 'section_name'으로 그룹화

        merged_content = []
        for section in sections:
            merged_content.append(f"\n*[{section}]*")  # 섹션 이름 추가
            section_articles = top_articles_df[top_articles_df['section_name'] == section]['summary'].tolist()
            merged_content.extend([f"● {summary}" for summary in section_articles])

        # 전체를 "\n\n"으로 구분하여 하나의 문자열로 병합
        final_content = "\n\n".join(merged_content)

        return final_content
