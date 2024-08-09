from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class NewsReview:
    def __init__(self, api_key):
        self.llm = ChatOpenAI(api_key=api_key, model="gpt-3.5-turbo", temperature=0.2)

    def generate_one_line_review(self, merged_content):
        daily_summary_system_message = (
            """"
                요구사항:
                    - 주어지는 오늘자 뉴스 기사에 대한 감상평을 남겨주세요.
                    - 모든 뉴스를 언급할 필요는 없습니다. 주요한 뉴스에 대한 평만 남겨도 됩니다.    
                    - 결과값은 한 문단이어야 합니다.
                    - 100자를 넘지 않아야 합니다.
                    - 문장의 어미는 반드시 친근하고 캐주얼한 말투(~군, ~야, ~겠어, ~바래)를 사용해야 합니다.
                    - 각 문장은 격식 없는 대화체로 작성해야 합니다.
                    - 뉴스를 기반으로 예상한 전망에 대한 내용을 포함해야 합니다.

                예시 1. 태풍 때문에 사건 사고가 많은 날이군. 대신 태풍으로 인해 날씨가 제법 선선해질듯해
                예시 2. 전쟁 위험이 점점 심각해지고 있어서 걱정이야. 전쟁이 일어난다면 경제가 침체되고 주가가 폭락할것으로 예상돼
                예시 3. 올림픽으로 인해 국위 선양에 대한 내용이 많아. 금메달을 꽤 많이 획득해서 한국의 브랜드 가치가 높아질 전망이야 
                예시 4. 오늘은 IT 와 관련된 호재가 많군. 반도체 관련 주식이 많이 오를듯한데 매수해보는건 어떨까?  
            """
        )
        daily_summary_prompt_template = """
                {text}
                """
        prompt_set = ChatPromptTemplate.from_messages([
            ("system", daily_summary_system_message),
            ("human", daily_summary_prompt_template)
        ])
        prompt = prompt_set.format(text=merged_content)
        summary = self.llm.invoke(prompt).content
        print(f"\033[95m뉴스 한줄평 생성 완료\033[0m")
        return summary
