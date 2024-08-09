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
                    - 주어지는 뉴스 기사를 요약해주세요.     
                    - 요약은 반드시 글자수 150자를 넘으면 안됩니다.
                    - 문장의 어미는 반드시 합쇼체, 하십시오(~습니다, ~입니다)체로 작성해야 합니다.
                    - 친절한 어투로 작성해야 합니다.
                    - 한국어 맞춤법과 띄어쓰기를 지켜야합니다.

                강력한 주의: 위의 조건을 지키지 않는 요약은 무효화됩니다.
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
