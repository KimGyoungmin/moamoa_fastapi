# langchain 라이브러리
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
# 장고 라이브러리
from django.conf import settings
# 시간 관련 라이브러리
from datetime import date
from .chat_history import get_current_korea_date
# 캡슐 라이브러리
from .prompts import chat_prompt
from .chat_history import get_message_history
from .models import FinanceDiary



llm = ChatOpenAI(model="gpt-4o-mini", api_key=settings.OPENAI_API_KEY)

runnable = chat_prompt | llm | StrOutputParser()

with_message_history = RunnableWithMessageHistory(
    runnable,
    get_message_history,
    input_messages_key="input",
    history_messages_key="chat_history",
)
    
# 프롬프트 전달 데이터
prompt_data = {
    "limit" : "<strong>사용하기에는 너무 많은 금액이에요!<br> 100만원 밑으로 입력해보는게 어때요?</strong>🤗",
    "chat_format" : """입력하신 내용을 바탕으로 전체 기록을 정리해 보았어요!<br>  
1. <strong>날짜</strong>: 2024-10-15
2. <strong>금액</strong>: 5000원
3. <strong>사용 내역</strong>: 탕후루를 샀음
4. <strong>분류</strong>: 음식
5. <strong>거래 유형</strong>: 지출<br>
위 내용이 맞는지 확인해 주세요!
1. 맞아요! <br> 2. 아니요, 다시 수정할래요!""",
    "notice" : "<strong>용돈기입장과 관련된 정보를 입력해 주세요!<br> 지출 또는 용돈 날짜와 금액 그리고 어떻게 사용했는지 꼭 입력하셔야되요! <br> 입력하지 않으면 모아모아는 알아듣지를 못한답니다</strong>🥺",
}

# 다중 입력 예시 (리스트 형태의 JSON 객체)
entries = [
    {"date": "2024-10-20", "amount": 100000, "details": "아빠가 주신 용돈", "category": "용돈", "transaction_type": "수입"},
    {"date": "2024-10-20", "amount": 20000, "details": "동생한테 준 돈", "category": "기타/지출", "transaction_type": "지출"},
    {"date": "2024-10-20", "amount": 20000, "details": "치킨 시킨 돈", "category": "음식", "transaction_type": "지출"}
]

# 각 항목을 순서대로 포맷팅한 후 결과에 추가
formatted_responses = []

for entry in entries:
    # prompt_data["chat_format"]를 사용하여 각 항목 데이터를 교체 (번호는 고정된 상태로 유지)
    formatted_response = prompt_data["chat_format"].format(
        date=entry["date"],
        amount=entry["amount"],
        details=entry["details"],
        category=entry["category"],
        transaction_type=entry["transaction_type"]
    )
    
    # 각 항목 사이에 개행 추가
    formatted_responses.append(formatted_response + "<br>")  # 각 항목 간 개행 처리

# 모든 항목을 합친 후 확인 메시지 추가
final_output = "".join(formatted_responses) 

# Views.py와 함수 연결
def chat_with_bot(user_input, user_id):
    try:
        session_id = f"user_{user_id}"
        current_date = get_current_korea_date()
        response = with_message_history.invoke(
            {"limit":prompt_data.get("limit"), "chat_format":final_output,"answer_check": prompt_data.get("answer_check"), "notice": prompt_data.get("notice"), "recent_day": current_date, "input": user_input},
            config={"configurable": {"session_id": session_id}}
        )

        # 수입/지출 관련 모든 영단어를 한글로 변환
        if isinstance(response, str):
            response = (
                response.replace("income", "수입")
                        .replace("earnings", "수입")
                        .replace("revenue", "수입")
                        .replace("profit", "수입")
                        .replace("expense", "지출")
                        .replace("expenditure", "지출")
                        .replace("spending", "지출")
                        .replace("cost", "지출")
            )
        return response
    except Exception as e:
        print(f"챗봇 오류: {str(e)}")
        return "죄송합니다. 채팅 서비스에 일시적인 문제가 발생했습니다."

# 생년월일을 이용한 나이 계산 함수
def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


# 잔액 업데이트 함수 정의
def update_remaining_balance(child):
    # 해당 child의 모든 finance_diary 기록을 today 날짜 기준으로 정렬해서 불러옵니다.
    finance_entries = FinanceDiary.objects.filter(child=child).order_by('today')
    
    total_balance = 0
    for entry in finance_entries:
        if entry.transaction_type == "수입":
            total_balance += entry.amount
        elif entry.transaction_type == "지출":
            total_balance -= entry.amount
        
        # 각 항목의 remaining을 업데이트
        entry.remaining = total_balance
        entry.save()

    # child.total 업데이트
    child.total = total_balance
    child.save()
