import streamlit as st
from langchain_anthropic import ChatAnthropic # 또는 다른 ChatModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage # 필요한 메시지 타입 다시 임포트
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver # 간단한 메모리
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import json
import uuid # uuid 임포트
import sys
import os
import asyncio # 비동기 처리를 위해 추가
import dotenv
import time # time 모듈 추가

dotenv.load_dotenv()

anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    anthropic_api_key = st.secrets.get("ANTHROPIC_API_KEY")

# tools.py 경로 설정 (현재 파일 기준 상위 폴더)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from tools import get_weather, search_restaurants

# --- LLM 및 도구 설정 --- 
# API 키 설정 (st.secrets 사용 권장)
try:
    llm = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0.7, api_key=anthropic_api_key)
except Exception as e:
    st.error(f"LLM 초기화 오류: {e}. API 키를 Streamlit secrets에 설정했는지 확인하세요.")
    st.stop()

tools = [get_weather, search_restaurants]

# --- 시스템 프롬프트 정의 --- 
system_prompt_template_react = """
당신은 피크닉 준비라는 간단한 예시를 통해, AI 에이전트의 작동 과정을 보여 줘야 합니다.
1. 사용자가 요청을 입력하면, 먼저 구체적인 도구 활용 계획을 설명해 주세요.
2. 그리고 이후에는 계획을 실행해 가는 과정을 보여 주세요. 
출력은 이모지와 마크다운을 적극적으로 활용하여 사용자가 쉽게 읽을 수 있도록 해 주세요.
주어진 목표를 달성하기 위해, 당신은 다음 도구들을 **스스로 판단하여 적극적으로 활용**해야 합니다:
- `get_weather`: 특정 장소의 날씨 정보를 얻습니다. (예: 피크닉 당일 날씨 확인)
- `search_restaurants`: 주변 맛집이나 특정 종류의 식당 정보를 얻습니다. (예: 피크닉 음식 포장 또는 주변 식당 검색)
"""

# LangGraph 에이전트 생성
try:
    # prompt = ChatPromptTemplate.from_messages(...) # 기존 프롬프트 정의는 create_react_agent 내부 로직과 충돌할 수 있으므로 주석 처리하거나 제거합니다.
    
    # 페이지별 메모리 관리
    if 'memory_react' not in st.session_state:
        st.session_state.memory_react = MemorySaver()
    memory = st.session_state.memory_react

    # create_react_agent 호출 시 system_message 인자를 사용하여 명확하게 시스템 프롬프트를 전달합니다.
    agent_executor = create_react_agent(
        llm, 
        tools, 
        prompt=system_prompt_template_react,
        checkpointer=memory
    )
except Exception as e:
    st.error(f"에이전트 생성 오류: {e}")
    st.stop()

# --- Streamlit UI 설정 --- 
st.title("AI Agent 🤖")
st.write("""
AI 에이전트가 스스로 **도구를 인지하고 활용**할 수 있습니다.\n 
에이전트에게 요청을 부여하고 작동 과정을 관찰해보세요.""")

# --- 채팅 기록 관리 (표시용 리스트 추가, checkpointer와 별개) ---
DISPLAY_MESSAGES_KEY = "react_display_messages_v4"
if DISPLAY_MESSAGES_KEY not in st.session_state:
    st.session_state[DISPLAY_MESSAGES_KEY] = []

# --- 스레드 ID 관리 (기존과 동일) --- 
THREAD_ID_KEY = "react_agent_thread_id_v2"
if THREAD_ID_KEY not in st.session_state:
    st.session_state[THREAD_ID_KEY] = f"react_thread_{uuid.uuid4()}"

config = {"configurable": {"thread_id": st.session_state[THREAD_ID_KEY]}}

# --- 타이핑 효과 제너레이터 --- 
def typing_effect_generator(text: str, speed: float = 0.01):
    for char in text:
        yield char
        time.sleep(speed)

# --- 렌더링 함수 정의 (수정) ---
def render_message_data(msg_data, is_new=False):
    role = msg_data.get("role") or msg_data.get("type")
    content = msg_data.get("content") or msg_data.get("text")
    name = msg_data.get("name") or msg_data.get("tool_name")
    tool_input = msg_data.get("input")

    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    elif role == "assistant": # 저장된 assistant 턴 렌더링 (is_new=False)
        with st.chat_message("assistant"):
            if isinstance(content, list):
                for item in content:
                    render_message_data(item, is_new=False) # 하위 항목 렌더링
            elif content:
                 st.markdown(content) # 단순 문자열 content 경우
                 
    elif role == "ai": # 스트리밍 중 AI 텍스트 청크 (is_new=True)
        # 이미 chat_message("assistant") 컨텍스트 안에 있음
        if content:
             # is_new가 True일 때만 타이핑 효과 적용
             if is_new:
                 st.write_stream(typing_effect_generator(content))
             else: # 혹시 모르니 추가 (보통 저장된 기록은 assistant role로)
                 st.markdown(content)
                 
    elif role == "tool_start":
         st.info(f"🛠️ **{name or '?'}** 도구 호출 중...", icon="🔄")
         if tool_input:
             with st.expander("도구 입력 보기", expanded=False):
                try:
                    st.code(json.dumps(tool_input, indent=2, ensure_ascii=False), language="json")
                except Exception:
                    st.code(str(tool_input), language='text')
    elif role == "tool_end":
         # 맛집 검색 결과인지 확인
         is_restaurant_tool = name and ("맛집" in name or "restaurant" in name.lower())
         
         try:
             # content가 문자열이면 JSON 파싱 시도, 아니면 그대로 사용
             parsed_output = json.loads(content) if isinstance(content, str) else content
             
             # 맛집 검색 결과이고, 파싱 결과가 리스트면 데이터프레임으로 표시
             if is_restaurant_tool and isinstance(parsed_output, list):
                  st.dataframe(parsed_output)
             else:
                  # 그 외의 경우는 JSON 코드 블록으로 표시
                  st.code(json.dumps(parsed_output, indent=2, ensure_ascii=False, default=str), language='json')
                  
         except (json.JSONDecodeError, TypeError):
             # 파싱 실패하거나 JSON 변환 불가 시 텍스트로 표시
             st.code(str(content), language=None)
    elif role == "error":
         st.error(content)

# --- 이전 대화 기록 표시 (표시용 리스트 사용) ---
for msg_data in st.session_state[DISPLAY_MESSAGES_KEY]:
    # 저장된 각 턴(user 또는 assistant) 렌더링
    render_message_data(msg_data, is_new=False)

# --- 사용자 입력 처리 --- 
if prompt := st.chat_input("내일 신촌에서 피크닉을 할 계획이야. 날씨와 맛집 정보를 바탕으로 계획을 세워줘"):
    # 사용자 메시지 저장 및 즉시 렌더링
    user_msg = {"role": "user", "content": prompt, "id": f"user_{uuid.uuid4()}"}
    st.session_state[DISPLAY_MESSAGES_KEY].append(user_msg)
    render_message_data(user_msg)
    # Checkpointer가 메모리에 HumanMessage 추가

    # --- AI 응답 스트리밍 (astream + 즉시 렌더링, 완료 후 저장) ---
    with st.chat_message("assistant"): # 스트리밍 출력을 위한 컨텍스트
        current_turn_messages = [] # 이번 턴 렌더링 데이터 수집

        async def stream_and_render_chunks():
            # 청크 분석 및 렌더링 데이터 생성 함수
            def get_render_data_from_chunk(chunk):
                render_data_list = []
                if isinstance(chunk, dict):
                    if agent_messages := chunk.get("agent", {}).get("messages", []):
                        msg = agent_messages[-1]
                        if isinstance(msg, AIMessage):
                            content_val = msg.content
                            ai_text_content = ""
                            if isinstance(content_val, str): ai_text_content = content_val
                            elif isinstance(content_val, list): texts = [p.get('text', '') for p in content_val if isinstance(p, dict) and p.get('type') == 'text']; ai_text_content = "".join(texts)
                            else: ai_text_content = str(content_val)
                            
                            # 텍스트 내용이 있으면 ai 타입 데이터 추가
                            if ai_text_content:
                                render_data_list.append({"type": "ai", "content": ai_text_content})
                                
                            # 도구 호출 정보가 있으면 tool_start 타입 데이터 추가
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                tool_call = msg.tool_calls[0]
                                render_data_list.append({"type": "tool_start", "name": tool_call.get('name'), "input": tool_call.get('args')})
                                
                    elif tool_messages := chunk.get("tools", {}).get("messages", []):
                        msg = tool_messages[-1]
                        if isinstance(msg, ToolMessage):
                            # tool_end 타입 데이터 추가
                            render_data_list.append({"type": "tool_end", "name": msg.name, "content": msg.content})
                return render_data_list

            # --- astream 루프 --- 
            try:
                async for chunk in agent_executor.astream({"messages": [HumanMessage(content=prompt)]}, config=config, stream_mode="updates"):
                    # --- 수신된 청크를 콘솔에 출력 (디버깅용 유지) --- 
                    print("\n--- Raw Chunk Received ---")
                    print(chunk)
                    print("--------------------------\n")
                    # --------------------------------
                    
                    render_data_list = get_render_data_from_chunk(chunk)
                    for data_to_render in render_data_list:
                        if data_to_render: 
                            # is_new=True 전달하여 타이핑 효과 적용
                            render_message_data(data_to_render, is_new=True) # 즉시 렌더링
                            current_turn_messages.append(data_to_render) # 턴 기록에 추가
                            
            except Exception as e:
                error_data = {"type": "error", "content": f"Agent 스트리밍 중 오류 발생: {e}"}
                render_message_data(error_data, is_new=True) # 오류 즉시 렌더링
                current_turn_messages.append(error_data) # 오류도 턴 기록에 추가
            
            # 스트림 종료 후 전체 턴 기록을 세션에 저장
            if current_turn_messages:
                 st.session_state[DISPLAY_MESSAGES_KEY].append({"role": "assistant", "content": current_turn_messages, "id": f"assistant_{uuid.uuid4()}"})

        # 비동기 함수 실행
        asyncio.run(stream_and_render_chunks())

    # rerun 제거
