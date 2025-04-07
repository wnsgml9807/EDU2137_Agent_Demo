# tools.py
import streamlit as st
from langchain_core.tools import tool
import json # json 임포트 추가

# === Agent용 도구 정의 ===
@tool
def get_weather(location: str):
    """Agent가 사용할 함수: 서울 내 특정 지역의 현재 날씨 정보를 가져옵니다."""
    # 실제 API 호출 대신 고정값 반환
    return "맑음"

@tool
def search_restaurants():
    """Agent가 사용할 함수: 주변 맛집이나 특정 종류의 리스트를 출력합니다."""
    # 풍부한 맛집 정보 반환
    return [
        {
            "name": "서호김밥",
            "main_menu": "김밥 (다시마, 소고기 등)",
            "rating": 4.5,
            "location": "서울 서초구 방배동"
        },
        {
            "name": "오월의 김밥",
            "main_menu": "김밥 (밥도둑, 오월 등 특색 메뉴)",
            "rating": 4.6,
            "location": "서울 서대문구 연희동"
        },
        {
            "name": "리김밥",
            "main_menu": "프리미엄 김밥 (에그튜너, 매콤견과류 등)",
            "rating": 4.3,
            "location": "서울 서대문구 연희동"
        },
        {
            "name": "소풍가는날",
            "main_menu": "다양한 종류의 김밥, 유부초밥",
            "rating": 4.2,
            "location": "서울 서대문구 신촌동"
        },
         {
            "name": "카페 마마스",
            "main_menu": "리코타치즈 샐러드, 파니니",
            "rating": 4.4,
            "location": "서울 중구 시청역 (여러 지점)"
        },
        {
            "name": "써브웨이",
            "main_menu": "샌드위치 (커스텀 가능)",
            "rating": 4.1,
            "location": "서울 전역 (매우 많음)"
        },
        {
            "name": "보울룸",
            "main_menu": "포케 (샐러드볼)",
            "rating": 4.7,
            "location": "서울 강남구 신사동"
        },
        {
            "name": "키친 마이야르",
            "main_menu": "잠봉뵈르 샌드위치, 파스타",
            "rating": 4.8, # 예약 어려움
            "location": "서울 마포구 공덕동"
        },
         {
            "name": "랜위치",
            "main_menu": "샌드위치 (랜위치, 에그 베이컨 등)",
            "rating": 4.5,
            "location": "서울 성동구 성수동"
        },
         {
            "name": "마녀김밥",
            "main_menu": "김밥 (마녀, 교리 등), 떡볶이",
            "rating": 4.0,
            "location": "서울 강남구 청담동 (여러 지점)"
        }
    ]

# === 페이지 2 시뮬레이션용 데이터 함수 ===

def get_seoul_weather_data():
    """페이지 2에서 사용할 함수: 고정된 서울 날씨 데이터('맑음')를 반환합니다."""
    return "맑음"

def get_picnic_restaurant_data():
    """페이지 2에서 사용할 함수: 고정된 피크닉 맛집 목록 데이터를 반환합니다."""
    # 위 search_restaurants와 동일한 목록 반환
    return [
        {
            "name": "서호김밥",
            "main_menu": "김밥 (다시마, 소고기 등)",
            "rating": 4.5,
            "location": "서울 서초구 방배동"
        },
        {
            "name": "오월의 김밥",
            "main_menu": "김밥 (밥도둑, 오월 등 특색 메뉴)",
            "rating": 4.6,
            "location": "서울 종로구 낙원동"
        },
        {
            "name": "리김밥",
            "main_menu": "프리미엄 김밥 (에그튜너, 매콤견과류 등)",
            "rating": 4.3,
            "location": "서울 강남구 압구정동 (여러 지점)"
        },
        {
            "name": "소풍가는날",
            "main_menu": "다양한 종류의 김밥, 유부초밥",
            "rating": 4.2,
            "location": "서울 동작구 사당동"
        },
         {
            "name": "카페 마마스",
            "main_menu": "리코타치즈 샐러드, 파니니",
            "rating": 4.4,
            "location": "서울 중구 시청역 (여러 지점)"
        },
        {
            "name": "써브웨이",
            "main_menu": "샌드위치 (커스텀 가능)",
            "rating": 4.1,
            "location": "서울 전역 (매우 많음)"
        },
        {
            "name": "보울룸",
            "main_menu": "포케 (샐러드볼)",
            "rating": 4.7,
            "location": "서울 강남구 신사동"
        },
        {
            "name": "키친 마이야르",
            "main_menu": "잠봉뵈르 샌드위치, 파스타",
            "rating": 4.8, # 예약 어려움
            "location": "서울 강남구 압구정동"
        },
         {
            "name": "랜위치",
            "main_menu": "샌드위치 (랜위치, 에그 베이컨 등)",
            "rating": 4.5,
            "location": "서울 성동구 성수동"
        },
         {
            "name": "마녀김밥",
            "main_menu": "김밥 (마녀, 교리 등), 떡볶이",
            "rating": 4.0,
            "location": "서울 강남구 청담동 (여러 지점)"
        }
    ]


# 실행 확인용 (선택적)
if __name__ == '__main__':
    print("--- Agent용 도구 테스트 ---")
    print("* get_weather:", get_weather(location="무시되는값1"))
    print("* search_restaurants:", json.dumps(search_restaurants(query="무시되는값2"), indent=2, ensure_ascii=False))
    print("\n--- 페이지 2 시뮬레이션용 데이터 함수 테스트 ---")
    print("* get_seoul_weather_data:", get_seoul_weather_data())
    print("* get_picnic_restaurant_data:", json.dumps(get_picnic_restaurant_data(), indent=2, ensure_ascii=False))
