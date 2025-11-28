import streamlit as st
import google.generativeai as genai
from datetime import datetime

# ==========================================
# 👇 1. 여기 따옴표 안에 본인의 API 키를 붙여넣으세요!
# 스트림릿 클라우드 설정(Secrets)에서 키를 가져오게 변경
try:
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # 내 컴퓨터에서 돌릴 때를 위해 임시로 넣어둠 (배포 시엔 무시됨)
    MY_API_KEY = "AIzaSyAPVd7IaNzMaG_m2wdKkXGe-ZgAT1Dvrlc" 



# 👇 2. 모델 이름을 수정했습니다. (일단 이걸로 하면 무조건 됩니다!)
TARGET_MODEL = "gemini-flash-latest"
# ==========================================

# --- API 설정 ---
genai.configure(api_key=MY_API_KEY)
model = genai.GenerativeModel(TARGET_MODEL)

# --- 페이지 설정 ---
st.set_page_config(page_title="AI 사주 상담소", page_icon="🔮")

st.title("🔮 고성능 AI 사주 상담소")
st.write("친구의 생년월일만 입력하면, AI가 운명을 분석해 줍니다.")

# --- 메인 입력 폼 ---
col1, col2 = st.columns(2)
with col1:
    name = st.text_input("이름 (또는 별명)", "친구")
    gender = st.selectbox("성별", ["남성", "여성"])
with col2:
    birth_date = st.date_input("생년월일", min_value=datetime(1900, 1, 1))
    birth_time = st.time_input("태어난 시간")

concern = st.text_area("요즘 가장 큰 고민은? (구체적일수록 정확함)", height=100)

# --- 사주 분석 버튼 ---
if st.button("✨ 사주 결과 보기"):
    try:
        # 프롬프트 구성
        prompt = f"""
        당신은 30년 경력의 정통 명리학자입니다. 아래 정보를 바탕으로 사주를 봐주세요.
        
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
        # 에러가 나면 화면에 빨간색으로 보여줍니다.
        st.error(f"오류가 발생했습니다: {e}")