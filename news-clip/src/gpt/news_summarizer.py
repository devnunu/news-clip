import threading
import time
import pandas as pd
from src.util.utils import print_progress_bar
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from openai import RateLimitError


class NewsSummarizer:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", temperature=0)
        self.system_message = (
            """"
                요구사항:
                    - 주어지는 뉴스 기사를 2 문장으로 요약해주세요.     
                    - 요약은 절대로 글자수 100자를 넘으면 안됩니다.
                    - 문장의 어미는 반드시 합쇼체, 하십시오(~습니다, ~입니다)체로 작성해야 합니다.
                    - 친절한 어투로 작성해야 합니다.
                    - 한국어 맞춤법과 띄어쓰기를 지켜야합니다.

                강력한 주의: 위의 조건을 지키지 않는 요약은 무효화됩니다.
                
                예시 1: 가상화폐의 대장주 비트코인이 미국 고용시장 지표 개선 조짐에 환호하며 급등하고 있습니다. 미국 가상화폐 거래소 코인베이스에 따르면 현지시간 8일 비트코인 1개당 가격이 24시간 전보다 6.27% 급등한 우리 돈 약 8천만 원에 거래됐습니다.
                예시 2: 1945년 8월 15일이 광복절이 아니라고 주장한 김형석 신임 독립기념관장이 어제 취임했습니다. 독립유공자 후손들의 격한 항의 속에서도 취임하자마자, 친일파로 매도된 인사들 명예 회복에 힘쓰겠다고 선언했습니다.
                예시 3: 최근 전기차 화재와 관련해 불안감이 높아지는 가운데 정부가 전기차 배터리 정보를 공개하도록 하는 방안을 검토하고 있습니다. 국토부는 오늘 국내 완성차 제조사 등과 회의를 열어 관련 입장을 들을 예정입니다.
                예시 4: 여자 탁구 대표팀은 세계 최강 중국을 상대한 단체전 준결승전에서 져, 내일 독일과 동메달을 결정전을 치르게 됐습니다. 세계랭킹 1, 2, 3위 선수들로 구성된 중국 탁구의 벽은 예상대로 높았습니다.
            """
        )
        self.prompt_template = """
        뉴스 기사:
        {text}

        요약:
        """
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("human", self.prompt_template)
        ])
        self.summary_completed_pages = 0
        self.lock = threading.Lock()

    def summarize_content(self, text):
        text_splitter = CharacterTextSplitter(separator='', chunk_size=10000, chunk_overlap=500)
        split_texts = text_splitter.split_text(text)
        summaries = []

        for split_text in split_texts:
            formatted_prompt = self.prompt.format(text=split_text)

            retry_attempts = 0
            max_attempts = 5
            while retry_attempts < max_attempts:
                try:
                    summary = self.llm.invoke(formatted_prompt).content
                    summaries.append(summary)
                    break  # 성공하면 반복 종료
                except RateLimitError as e:
                    retry_attempts += 1
                    wait_time = min(2 ** retry_attempts, 60)  # 지수적 백오프
                    print(
                        f"Rate limit exceeded, retrying in {wait_time} seconds... (Attempt {retry_attempts}/{max_attempts})")
                    time.sleep(wait_time)
            else:
                raise RuntimeError(f"Failed to summarize content after {max_attempts} attempts due to rate limits.")

        return "\n".join(summaries)

    def summarize_articles(self, csv_file, summarized_csv):
        start_time = time.time()
        df = pd.read_csv(csv_file)
        total_articles = len(df)
        print(f"총 {total_articles}개의 기사가 발견되었습니다.")

        summaries = []

        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = []
            for _, row in df.iterrows():
                article_text = row['main']
                futures.append(executor.submit(self.summarize_content, article_text))

            for future in as_completed(futures):
                summary = future.result()

                with self.lock:
                    self.summary_completed_pages += 1
                    print_progress_bar("요약", self.summary_completed_pages, total_articles)

                summaries.append({
                    "title": df.loc[self.summary_completed_pages - 1, 'title'],
                    "date": df.loc[self.summary_completed_pages - 1, 'date'],
                    "section": df.loc[self.summary_completed_pages - 1, 'section'],
                    "summary": summary
                })

        summaries_df = pd.DataFrame(summaries)
        summaries_df.to_csv(summarized_csv, index=False, encoding='utf-8-sig')
        print(f"\033[95m기사 요약이 완료되었습니다. 요약본이 {summarized_csv}에 저장되었습니다.\033[0m")

        elapsed_time = time.time() - start_time
        print(f"\033[95m요약 작업이 완료되었습니다. 총 소요 시간: {elapsed_time:.2f}초\033[0m")
