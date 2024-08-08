import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
from langchain.text_splitter import CharacterTextSplitter
import tiktoken  # 토큰 계산을 위해 tiktoken 라이브러리 사용


class NewsSummarizer:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(
            api_key=api_key,
            model="gpt-3.5-turbo",
            temperature=0
        )
        self.system_message = (
            """"
                요구사항:
                    - 주어지는 뉴스 기사를 요약해주세요.     
                    - 결과값은 한 문단이어야합니다.
                    - 200자를 넘지 않아야 합니다.
                    - 문장의 어미는 반드시 합쇼체, 하십시오(~습니다, ~입니다)체로 작성해야 합니다.
                    - 친절한 어투로 작성해야 합니다.

                강력한 주의: 위의 조건을 지키지 않는 요약은 무효화됩니다.

                예시: 
                    - 증시 폭락의 여파로 정치권에선 내년 1월부터 시행되는 금융투자세를 놓고 격론이 벌어지고 있습니다. 국민의힘은 시장 불안 해소를 위해 당장 폐지를 논의하자고 했지만 민주당은 증시폭락의 책임부터 지라고 맞서고 있습니다. 당 대표 연임이 유력한 이재명 후보는 5년간 5억원까지는 비과세하자는 수정안을 언급했습니다.
                    - '국민 삐약이', 탁구대표팀 신유빈 선수의 먹방이 화제죠. 경기 때마다 체력 보충을 위해 먹은 음식들이 연일 품절 대란이라고 합니다. 파리올림픽에서 활약하는 선수들 얼굴이 들어간 골드카드도 불티나게 팔리고 있습니다.
                    - 오늘은 수도권 등 중부지방을 중심으로 최대60mm 이상의 많은 비가 내리겠습니다. 남부지방은 낮 최고 36도의 폭염 속에 곳곳에 소나기가 강하게 내리겠습니다.
                    - 민생법안을 우선처리 하자며 협치에 물꼬를 튼 여야가 오늘 원내수석간 회동을 통해 본격 협의에 나섭니다. 하지만 야당이 강화된 세번째 해병대원 특검법 발의에 나서고, 25만 뭔 민생 지원금 처리도 협의 조건으로 내걸어 협치가 이뤄질진 미지수입니다.
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
        self.filter_completed_pages = 0
        self.lock = threading.Lock()

    def summarize_content(self, text):
        text_splitter = CharacterTextSplitter(separator='', chunk_size=10000, chunk_overlap=500)
        split_texts = text_splitter.split_text(text)

        summaries = []

        for i, split_text in enumerate(split_texts):
            # print(f"Part {i + 1}/{len(split_texts)} 요약 중...")

            formatted_prompt = self.prompt.format(text=split_text)
            # start_time = time.time()

            # 스트리밍 대신 한 번에 응답을 받도록 변경
            summary = self.llm.invoke(formatted_prompt).content

            # elapsed_time = time.time() - start_time
            # print(f"파트 {i + 1} 요약 완료 (소요 시간: {elapsed_time:.2f}초)")

            summaries.append(summary)

        return "\n".join(summaries)

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

        # 스트리밍 대신 한 번에 응답을 받도록 변경
        response = self.llm.invoke(prompt).content

        return article1 if "기사 1" in response else article2

    def summarize_articles(self, csv_file, summarized_csv):
        start_time = time.time()
        df = pd.read_csv(csv_file)
        total_articles = len(df)
        print(f"총 {total_articles}개의 기사가 발견되었습니다.")

        summaries = []

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = []
            for index, row in df.iterrows():
                article_text = row['main']
                futures.append(executor.submit(self.summarize_content, article_text))

            for future in as_completed(futures):
                summary = future.result()

                with self.lock:
                    self.summary_completed_pages += 1
                    self.print_progress_bar("요약", self.summary_completed_pages, total_articles)

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

    def filter_top_articles(self, summarized_csv, output_csv, top_n=3):
        start_time = time.time()
        summaries_df = pd.read_csv(summarized_csv)
        total_sections = summaries_df['section'].nunique()
        total_items = total_sections * top_n
        print(f"총 {total_sections}개의 섹션에서 {total_items}개의 기사를 선별할 예정입니다.")

        top_articles = []
        grouped_df = summaries_df.groupby('section')

        for section, group in grouped_df:
            print(f"섹션 {section}의 중요한 기사 선택 중...")

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
                    self.print_progress_bar("기사 선별", self.filter_completed_pages, total_items)

            top_articles.extend(selected_articles)

        top_articles_df = pd.DataFrame(top_articles)
        top_articles_df.to_csv(output_csv, index=False, encoding='utf-8-sig')
        print(f"\033[95m최종 선택된 기사가 {output_csv}에 저장되었습니다.\033[0m")

        elapsed_time = time.time() - start_time
        print(f"\033[95m기사 선별 작업이 완료되었습니다. 총 소요 시간: {elapsed_time:.2f}초\033[0m")

        return top_articles_df

    def summarize_and_select_top_articles(self, csv_file, summarized_csv, output_csv, top_n=3):
        self.summarize_articles(csv_file, summarized_csv)
        print("\n==========================================================================================\n")
        self.filter_top_articles(summarized_csv, output_csv, top_n)

    def print_merged_content(self, top_articles_csv):
        top_articles_df = pd.read_csv(top_articles_csv)
        merged_content = "\n\n".join([f"● {summary}" for summary in top_articles_df['summary'].tolist()])
        print("\nMerged Content:\n")
        print(merged_content)

    def print_progress_bar(self, work, completed, total, bar_length=40):
        """
        진행률을 표시하는 함수
        :param completed: 완료된 작업 수
        :param total: 전체 작업 수
        :param bar_length: 진행률 바의 길이 (기본값은 40)
        """
        progress = completed / total
        block = int(round(bar_length * progress))
        progress_bar = f"[{'#' * block}{'.' * (bar_length - block)}]"
        progress_percent = f"{progress * 100:.2f}%"

        print(f"\033[91m{work}진행 상황: {progress_bar} {progress_percent} "
              f"({completed}/{total})\033[0m", flush=True)
