import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage # AIMessageChunk 제거
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv
import os
import uuid
import asyncio
import time # time 모듈 추가

# .env 파일 로드 (파일이 존재할 경우)
load_dotenv()

# --- LLM 설정 (Claude 사용 및 dotenv 활용 - 페이지 3 기준) ---
try:
    # 환경 변수에서 API 키 가져오기
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        # secrets.toml 에서도 찾아보기
        anthropic_api_key = st.secrets.get("ANTHROPIC_API_KEY")

    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY가 환경 변수 또는 secrets.toml에 설정되지 않았습니다.")

    # Claude 모델 사용
    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-latest",
        temperature=0.7,
        api_key=anthropic_api_key,
        # streaming=True # LLMChain에서 stream을 사용하려면 이 옵션은 제거하거나, chain의 stream 메소드를 활용해야 합니다.
    )
except ValueError as e: # 명시적 오류 처리
    st.error(e)
    st.stop()
except Exception as e: # 기타 오류
    st.error(f"LLM 초기화 오류: {e}")
    st.stop()

# --- 프롬프트 템플릿 및 메모리 설정 ---
# 페이지별 고유 메모리 키
MEMORY_KEY = "no_tools_memory"
if MEMORY_KEY not in st.session_state:
    st.session_state[MEMORY_KEY] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

memory = st.session_state[MEMORY_KEY]

# 프롬프트 템플릿 정의 (메모리 포함)
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "당신은 사용자를 돕는 챗봇입니다. 사용자의 질문에 대답하고 대화 내용을 기억합니다. \
         **하지만 당신은 외부 도구가 없으므로, 현재 날씨나 특정 장소의 실시간 정보와 같은 최신 정보는 알 수 없습니다.** \
         출력은 이모지와 마크다운을 적극적으로 활용하여 사용자가 쉽게 읽을 수 있도록 하세요. \
         오직 당신이 학습한 내용과 이전 대화 기록을 바탕으로만 답변할 수 있습니다."),
        MessagesPlaceholder(variable_name="chat_history"), # 메모리 변수
        ("human", "{input}"), # 사용자 입력 변수
    ]
)

# LLMChain 생성
chain = LLMChain(llm=llm, prompt=prompt_template, memory=memory)


# --- Streamlit UI 설정 ---
st.title("도구 없는 AI 챗봇🚫")
st.write("학습된 정보와 프롬프트를 바탕으로 대답합니다. 외부 도구는 사용할 수 없습니다.")

# --- 채팅 기록 관리 (표시용 리스트 추가) ---
DISPLAY_MESSAGES_KEY = "no_tools_display_messages_v6"
if DISPLAY_MESSAGES_KEY not in st.session_state:
    st.session_state[DISPLAY_MESSAGES_KEY] = []

# --- 타이핑 효과 제너레이터 --- 
def typing_effect_generator(text: str, speed: float = 0.01):
    for char in text:
        yield char
        time.sleep(speed)

# --- 렌더링 함수 정의 --- 
def render_message_data(msg_data, is_new=False): # is_new 인자 추가
    role = msg_data.get("role")
    content = msg_data.get("content")
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant":
        with st.chat_message("assistant"):
             if content:
                 # is_new 플래그는 호출하는 곳에서 write_stream 사용 여부 결정
                 # 여기서는 항상 markdown (저장된 기록 표시용)
                 st.markdown(content)

# --- 이전 대화 기록 표시 ---
for msg_data in st.session_state[DISPLAY_MESSAGES_KEY]:
    render_message_data(msg_data, is_new=False) # 이전 기록은 is_new=False

# --- 사용자 입력 및 AI 응답 처리 (챗봇 2와 동일 로직) ---
if user_input := st.chat_input("내일 신촌에서 피크닉을 할 계획이야. 날씨와 맛집 정보를 바탕으로 계획을 세워줘"):
    # 1. 사용자 메시지 저장 및 즉시 렌더링
    user_msg = {"role": "user", "content": user_input}
    st.session_state[DISPLAY_MESSAGES_KEY].append(user_msg)
    render_message_data(user_msg) # is_new=False로 즉시 마크다운 렌더링
    # 메모리는 invoke 시점에 업데이트됨

    # 2. AI 응답 생성 및 즉시 렌더링 (타이핑 효과)
    with st.chat_message("assistant"):
            try:
                # invoke 사용하여 전체 응답 받기
                response = chain.invoke({"input": user_input})
                final_response_content = response.get('text', response.get('response', "응답 내용을 찾을 수 없습니다."))
                if not isinstance(final_response_content, str):
                     final_response_content = str(final_response_content)
                
                # 타이핑 효과로 즉시 렌더링하고 최종 내용 저장
                if final_response_content:
                     # st.write_stream 호출하여 즉시 렌더링
                     displayed_response = st.write_stream(typing_effect_generator(final_response_content))
                     # 최종 문자열 저장
                     st.session_state[DISPLAY_MESSAGES_KEY].append({"role": "assistant", "content": displayed_response})
                     # 메모리 자동 추가
                
            except Exception as e:
                 # 오류 메시지 렌더링 및 저장
                 error_message = f"LLM 응답 생성 중 오류 발생: {e}"
                 st.error(error_message) 
                 st.session_state[DISPLAY_MESSAGES_KEY].append({"role": "assistant", "content": error_message})

    # rerun 제거

# --- AI 응답 생성 별도 트리거 로직 제거 ---
