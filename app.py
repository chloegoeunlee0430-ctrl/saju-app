import streamlit as st
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 👇 [보안 수정 완료] API 키를 안전하게 가져옵니다.
# ==========================================
try:
    # Streamlit Cloud 배포 시에는 Secrets에서 가져옴
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
except FileNotFoundError:
    # ⚠️ 중요: 깃허브에 올릴 때는 여기를 비워둬야 안전합니다!
    # 로컬(내 컴퓨터)에서 테스트할 때만 잠시 넣고, 올릴 땐 지우세요.
    MY_API_KEY = "" 

# 모델 설정 (가장 안정적인 모델)
TARGET_MODEL = "gemini-flash-latest"
# ==========================================

# --- API 설정 ---
if not MY_API_KEY:
    # 키가 없을 때 에러 메시지를 예쁘게 보여줌
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets에 키를 추가해주세요!")
    st.stop() # 더 이상 실행하지 않고 멈춤

genai.configure(api_key=MY_API_KEY)
model = genai.GenerativeModel(TARGET_MODEL)

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 사주 상담소", page_icon="🔮")

st.title("🔮 AI 사주 상담소")
st.write("생년월일만 입력하면, AI가 운명을 분석해 줍니다.")

# --- 메인 입력 폼 ---
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("이름(선택)", "이고은")
    gender = st.selectbox("성별", ["여성", "남성"])
with col2:
    # 👇 [수정 1] 기본값을 1990년 1월 1일로 변경
    birth_date = st.date_input(
        "생년월일", 
        value=datetime(1987, 4, 30), 
        min_value=datetime(1900, 1, 1)
    )
    # 👇 [수정 2] 시간을 30분 단위(1800초)로 선택하게 변경
    birth_time = st.time_input(
        "태어난 시간", 
        value=datetime.strptime("12:00", "%H:%M"),
        step=1800 
    )

concern = st.text_area("요즘 가장 큰 고민은 무엇인가요? (구체적일 수록 정확하답니다.)", height=100)

# --- 사주 분석 버튼 ---
if st.button("✨ 사주 결과 보기"):
    try:
        # 프롬프트 구성
        prompt = f"""
        당신은 30년 경력의 정통 명리학자입니다. 아래 정보를 바탕으로 사주를 봐주세요. 말투는 깔끔하고 공손하고 겸손한 말투로 얘기해주세요.
        
        [사용자 정보]
        - 이름: {name} ({gender})
        - 생년월일: {birth_date.strftime('%Y년 %m월 %d일')}
        - 태어난 시간: {birth_time.strftime('%H시 %M분')}
        - 고민: {concern if concern else "특별한 고민 없음"}

        [지시사항]
        1. 사용자의 사주 원국(네 기둥)을 분석하여 타고난 기질과 성격을 설명하세요.
        2. 2025년의 운세(재물, 연애, 직업, 건강)를 흐름 위주로 구체적으로 서술하세요.
        3. 고민에 대해 명리학적 관점에서 위로가 되는 따뜻한 조언과 처세술을 알려주세요.
        4. 말투는 신비롭지만 친절하고, 어려운 한자는 쉽게 풀이하세요.
        5. 중요한 키워드는 굵게 표시하고, 가독성 좋게 줄바꿈하세요.
        """

        with st.spinner(f"{TARGET_MODEL} 모델이 운명을 읽고 있습니다..."):
            response = model.generate_content(prompt)
            st.success(f"{name}님의 사주 분석이 완료되었습니다!")
            st.markdown("---")
            st.markdown(response.text)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
