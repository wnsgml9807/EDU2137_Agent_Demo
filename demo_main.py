# lecture_main.py
import streamlit as st

st.set_page_config(
    page_title="AI Agent 유형 비교",
    page_icon="🧠",
    layout="wide"
)

pg = st.navigation([
    st.Page("pages/1_🚫_No_Tools.py", title="No Tools"),
    st.Page("pages/2_🔧_RAG_Chatbot.py", title="RAG Chatbot"),
    st.Page("pages/3_🤖_Agent.py", title="Agent"),
])

st.sidebar.info(
    """교육학과 권준희
    (wnsgml9807@naver.com)"""
)
# pages/ 폴더의 파일들이 자동으로 네비게이션 메뉴에 추가됩니다. 
pg.run()