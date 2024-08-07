import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time


class NewsSummarizer:
    def __init__(self, api_key):
        """
        :param api_key: OpenAI API key
        """
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", stream=True)

        # 시스템 메시지로 톤앤 매너 설정
        self.system_message = (
            """"
                당신은 중립적이고 공정한 뉴스 요약자입니다. 모든 뉴스 기사를 200자 내외로 간결하고 명확하게 요약해 주세요.
                추가 요구사항은 다음과 같습니다.
                - 요약된 텍스트는 한 문단으로만 구성됩니다.
                - 문단 앞에는 ● 를 붙여주세요.
                - 각 문장은 ~니다의 종결 어미를 사용해주세요.
                
                예시: ● 증시 폭락의 여파로 정치권에선 내년 1월부터 시행되는 금융투자세를 놓고 격론이 벌어지고 있습니다. 국민의힘은 시장 불안 해소를 위해 당장 폐지를 논의하자고 했지만 민주당은 증시폭락의 책임부터 지라고 맞서고 있습니다. 당 대표 연임이 유력한 이재명 후보는 5년간 5억원까지는 비과세하자는 수정안을 언급했습니다.
            """
        )

        # 템플릿 생성
        self.prompt_template = """
        뉴스 기사:
        {text}

        요약:
        """

        # ChatPromptTemplate에 시스템 메시지를 포함시킴
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_message),
            ("human", self.prompt_template)
        ])

    def summarize_content(self, text):
        """
        주어진 텍스트를 요약하는 함수 (실시간 스트리밍으로 출력)
        :param text: 요약할 텍스트
        :return: 요약된 텍스트
        """
        # 텍스트를 사용하여 프롬프트를 구성
        formatted_prompt = self.prompt.format(text=text)
        summary = ""

        start_time = time.time()  # 시작 시간 기록

        # 스트리밍된 응답을 실시간으로 출력
        for token in self.llm.stream(formatted_prompt):
            content = token.content  # AIMessageChunk의 content 속성을 가져옴
            print(content, end="", flush=True)  # 실시간으로 콘솔창에 출력
            summary += content

        elapsed_time = time.time() - start_time  # 경과 시간 계산
        print(f"\n기사 요약 완료 (소요 시간: {elapsed_time:.2f}초)\n")

        return summary

    def summarize_articles_from_csv(self, csv_file):
        """
        Summarize news articles from a CSV file using ThreadPoolExecutor.
        :param csv_file: Path to the CSV file
        :return: List of summarized articles
        """
        df = pd.read_csv(csv_file)
        total_articles = len(df)
        print(f"총 {total_articles}개의 기사가 발견되었습니다.")

        summaries = []

        start_time = time.time()  # 시작 시간 기록

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for index, row in df.iterrows():
                article_text = row['main']  # 'main' 컬럼이 기사 본문을 포함한다고 가정
                futures.append(executor.submit(self.summarize_content, article_text))

            for index, future in tqdm(enumerate(as_completed(futures)), total=total_articles, desc="진행 상황", unit="기사"):
                summary = future.result()
                elapsed_time = time.time() - start_time

                summaries.append({
                    "title": df.loc[index, 'title'],
                    "date": df.loc[index, 'date'],
                    "summary": summary,
                    "elapsed_time": elapsed_time  # 각 기사의 요약에 걸린 시간 추가
                })

                print(f"기사 {index + 1}/{total_articles} 요약 완료 (소요 시간: {elapsed_time:.2f}초)\n")

        return summaries

    def save_summaries_to_csv(self, summaries, output_file):
        """
        Save the summarized articles to a CSV file.
        :param summaries: List of summarized articles
        :param output_file: Output CSV file path
        """
        summaries_df = pd.DataFrame(summaries)
        summaries_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Summaries saved to {output_file}")