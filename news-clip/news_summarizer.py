import pandas as pd
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from tqdm import tqdm


class NewsSummarizer:
    def __init__(self, api_key):
        """
        :param api_key: OpenAI API 키
        """
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-4", max_tokens=256)
        self.template = """
        다음은 뉴스 기사입니다. 기사의 핵심 정보를 간추려서 요약해 주세요. 아래 예시를 참고하여 자연스러운 뉴스 요약 문장으로 작성해 주세요:

        예시:
        ● 전 국민에게 25만원을 지급하자며 야당이 발의한 '25만원 지원법'이 국회 본회의에 상정됐습니다. 국민 모두에게 25만~35만원 범위에서 지역사랑상품권을 지급해 민생을 달래고 경기 회복의 '마중물'로 삼자는 취지의 '특별조치법' 입니다. 국민의힘은 물가와 금리에 악영향을 주는 '현금살포법'이라고 반발하며 또다시 필리버스터에 돌입했습니다.
        ● 최근 군 정보요원 신상 유출 의혹 사건과 관련해 여야가 간첩법 개정을 두고 공방을 벌이고 있습니다. 국민의힘은 21대 국회에서 민주당 때문에 간첩법 개정안이 통과되지 못했다고 주장했는데, 민주당은 터무니 없는 거짓말과 본질을 흐리는 남탓이라며 반발했습니다.

        뉴스 기사:
        {text}

        요약:
        """
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template=self.template,
        )
        self.sequence = self.prompt | self.llm

    def split_and_summarize(self, article_text):
        """기사 내용을 쪼개서 각각 요약하고 최종 요약을 반환하는 함수"""
        text_splitter = CharacterTextSplitter(chunk_size=2000, chunk_overlap=200)
        chunks = text_splitter.split_text(article_text)

        summaries = []
        for chunk in chunks:
            # Invoke sequence and extract the message content
            response = self.sequence.invoke({"text": chunk})
            summary = response["choices"][0]["message"]["content"].strip()
            summaries.append(summary)

        # 모든 요약을 결합하여 최종 요약 생성
        combined_summary = " ".join(summaries)
        return combined_summary

    def summarize_article(self, article_text):
        """뉴스 기사를 요약하는 함수"""
        return self.split_and_summarize(article_text)

    def summarize_articles_from_csv(self, csv_file):
        """CSV 파일에서 뉴스 기사를 읽어와서 요약하는 함수"""
        df = pd.read_csv(csv_file)
        summaries = []

        for index, row in tqdm(df.iterrows(), total=len(df), desc="Summarizing Articles"):
            article_text = row['main']  # 'main' 컬럼이 기사 본문을 포함한다고 가정
            summary = self.summarize_article(article_text)
            summaries.append({
                "title": row['title'],
                "date": row['date'],
                "summary": summary
            })

        return summaries

    def save_summaries_to_csv(self, summaries, output_file):
        """요약된 뉴스 기사를 CSV 파일로 저장하는 함수"""
        summaries_df = pd.DataFrame(summaries)
        summaries_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Summaries saved to {output_file}")
