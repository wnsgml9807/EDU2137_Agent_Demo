import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage # AIMessageChunk 제거
from langchain.memory import ConversationBufferMemory # 메모리 추가
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder # 프롬프트 추가
from langchain.chains import LLMChain # LLMChain 추가
import json
import uuid # uuid 임포트
import sys
import os
import asyncio
import re # 키워드 검색을 위해 추가
from dotenv import load_dotenv # dotenv 임포트
import time # time 모듈 추가

# .env 파일 로드
load_dotenv()

# tools.py 경로 설정 (다시 추가)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
# Agent용 @tool 함수 대신 시뮬레이션용 일반 함수 임포트
from tools import get_seoul_weather_data, get_picnic_restaurant_data

# --- LLM 설정 (기존과 동일) ---
try:
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        anthropic_api_key = st.secrets["ANTHROPIC_API_KEY"]
        print("접근 성공")  
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY가 환경 변수 또는 secrets.toml에 설정되지 않았습니다.")

    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-latest",
        temperature=0.7,
        api_key=anthropic_api_key
    )
except ValueError as e:
    print("접근 실패")
    st.error(e)
    st.stop()
except Exception as e:
    st.error(f"LLM 초기화 오류: {e}")
    st.stop()

# --- 프롬프트 및 메모리 설정 (기존과 동일) ---
# 페이지별 고유 메모리 키
MEMORY_KEY = "explicit_memory"
if MEMORY_KEY not in st.session_state:
    st.session_state[MEMORY_KEY] = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

memory = st.session_state[MEMORY_KEY]

# 시스템 프롬프트 (사이드바나 버튼 언급 제거)
system_prompt_manual_tools = """당신은 사용자의 피크닉 계획을 돕는 챗봇입니다.
**당신은 스스로 현재 날씨나 실시간 맛집 정보를 알 수 없습니다. 오직 학습된 지식과 대화 기록에만 의존합니다.**
**[응답 규칙]**
1. 만약 사용자 질문과 함께 추가 정보(`[날씨 정보 (서울)]` 또는 `[맛집 정보 (피크닉 음식)]`)가 주어진다면, **반드시 그 정보를 답변에 활용**하세요.
2. 만약 추가 정보가 주어지지 않았다면, **당신은 최신 정보를 모른다는 점을 사용자에게 명확히 인지**시키고, 학습된 지식과 대화 기록만을 바탕으로 답변하세요. 이 경우, 실시간 정보가 필요한 질문에는 답할 수 없다고 솔직하게 말하는 것이 좋습니다.
3. 출력은 이모지와 마크다운을 적극적으로 활용하여 사용자가 쉽게 읽을 수 있도록 하세요.
"""

# 프롬프트 템플릿 정의 (MessagesPlaceholder 사용)
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_manual_tools),
        MessagesPlaceholder(variable_name="chat_history"), # 메모리
        ("human", "{input}"), # 사용자의 최종 입력 (질문 + 도구 결과 포함 가능)
    ]
)

# LLMChain 생성
chain = LLMChain(llm=llm, prompt=prompt_template, memory=memory)


# --- Streamlit UI 설정 (기존과 동일) ---
st.title("RAG Chatbot🔧")
st.write("""
프롬프트 입력 시 추가적인 도구를 사용할 수 있습니다. \n
**사이드바의 토글 버튼**을 이용해 미리 준비된 정보를 질문에 첨부해 보세요.""")

# --- 채팅 기록 관리 (표시용 리스트 추가) ---
DISPLAY_MESSAGES_KEY = "explicit_display_messages_v6"
if DISPLAY_MESSAGES_KEY not in st.session_state:
    st.session_state[DISPLAY_MESSAGES_KEY] = []

# --- 타이핑 효과 제너레이터 --- 
def typing_effect_generator(text: str, speed: float = 0.01):
    for char in text:
        yield char
        time.sleep(speed)

# --- 렌더링 함수 정의 (수정) ---
def render_message_data(msg_data):
    role = msg_data.get("role")
    content = msg_data.get("content")
    name = msg_data.get("name")

    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant":
        # 저장된 기록은 항상 마크다운으로 표시
        with st.chat_message("assistant"):
            if content:
                 st.markdown(content)
    elif role == "tool_result": 
         with st.expander(f"첨부된 {name} 정보", expanded=True):
              is_restaurant_tool = name and ("맛집" in name or "restaurant" in name.lower())
              try:
                  parsed_content = json.loads(content) if isinstance(content, str) else content
                  if is_restaurant_tool and isinstance(parsed_content, list):
                       st.dataframe(parsed_content)
                  else:
                      st.code(json.dumps(parsed_content, indent=2, ensure_ascii=False, default=str), language='json')
              except (json.JSONDecodeError, TypeError):
                  st.code(str(content), language='text')

# --- 이전 대화 기록 표시 ---
for msg_data in st.session_state[DISPLAY_MESSAGES_KEY]:
    render_message_data(msg_data)

# --- 도구 활성화 버튼 (사이드바) ---
with st.sidebar:
    st.header("도구 옵션")
    if 'activate_weather' not in st.session_state:
        st.session_state.activate_weather = False
    st.session_state.activate_weather = st.toggle("서울 날씨 확인", value=st.session_state.activate_weather, key="weather_toggle", help="활성화하고 질문하면 미리 준비된 서울 날씨 정보를 함께 전달합니다.")

    if 'activate_restaurants' not in st.session_state:
        st.session_state.activate_restaurants = False
    st.session_state.activate_restaurants = st.toggle("맛집 검색", value=st.session_state.activate_restaurants, key="resto_toggle", help="활성화하고 질문하면 미리 준비된 '피크닉 음식' 맛집 정보를 함께 전달합니다.")

# --- 사용자 입력 및 AI 응답 처리 (즉시 렌더링) ---
if prompt := st.chat_input("내일 신촌에서 피크닉을 할 계획이야. 날씨와 맛집 정보를 바탕으로 계획을 세워줘."):
    # 1. 사용자 메시지 저장 및 즉시 렌더링
    user_msg = {"role": "user", "content": prompt}
    st.session_state[DISPLAY_MESSAGES_KEY].append(user_msg)
    render_message_data(user_msg)

    tool_results_text = "" # LLM 입력용

    # 2. 활성화된 도구 실행 및 결과 저장/즉시 렌더링
    if st.session_state.activate_weather:
        try:
            weather_result = get_seoul_weather_data()
            result_str = json.dumps(weather_result, ensure_ascii=False)
            tool_results_text += f"\n\n[날씨 정보 (서울)]\n{result_str}"
            tool_data = {"role": "tool_result", "name": "날씨 (서울)", "content": result_str}
            st.session_state[DISPLAY_MESSAGES_KEY].append(tool_data)
            render_message_data(tool_data) # 도구 결과 즉시 렌더링
        except Exception as e:
            st.error(f"날씨 정보 확인 중 오류: {e}") 
        st.session_state.activate_weather = False

    if st.session_state.activate_restaurants:
        try:
             resto_result = get_picnic_restaurant_data()
             result_str = json.dumps(resto_result, indent=2, ensure_ascii=False)
             tool_results_text += f"\n\n[맛집 정보 (피크닉 음식)]\n{result_str}"
             tool_data = {"role": "tool_result", "name": "맛집 (피크닉 음식)", "content": result_str}
             st.session_state[DISPLAY_MESSAGES_KEY].append(tool_data)
             render_message_data(tool_data) # 도구 결과 즉시 렌더링
        except Exception as e:
            st.error(f"맛집 정보 검색 중 오류: {e}")
        st.session_state.activate_restaurants = False

    # 3. LLM 입력 구성 및 응답 생성/렌더링/저장
    final_input_for_llm = prompt + tool_results_text
    # 메모리 자동 추가됨 (invoke 사용 시)
    with st.chat_message("assistant"):
            try:
                # invoke로 전체 응답 받기
                response = chain.invoke({"input": final_input_for_llm})
                final_response_content = response.get('text', response.get('response', "응답 내용을 찾을 수 없습니다."))
                if not isinstance(final_response_content, str): final_response_content = str(final_response_content)
                
                if final_response_content:
                     # 타이핑 효과로 즉시 렌더링
                     displayed_response = st.write_stream(typing_effect_generator(final_response_content))
                     # 최종 내용 저장
                     st.session_state[DISPLAY_MESSAGES_KEY].append({"role": "assistant", "content": displayed_response})
                     # 메모리 자동 추가
            
            except Exception as e:
                 error_message = f"LLM 응답 생성 중 오류 발생: {e}"
                 st.error(error_message) 
                 st.session_state[DISPLAY_MESSAGES_KEY].append({"role": "assistant", "content": error_message})
