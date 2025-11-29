import streamlit as st
import google.generativeai as genai
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar

# ==========================================
# 👇 [보안 처리] Streamlit Secrets에서 API 키를 가져옵니다.
MY_API_KEY = st.secrets.get("GEMINI_API_KEY", "") 
TARGET_MODEL = "gemini-flash-latest"
# ==========================================

# --- API 설정 ---
if not MY_API_KEY:
    st.error("API 키가 설정되지 않았습니다. Streamlit Secrets에 키를 추가해주세요!")
    st.stop()

genai.configure(api_key=MY_API_KEY)
model = genai.GenerativeModel(TARGET_MODEL)

# --- 페이지 설정 ---
st.set_page_config(page_title="정통 AI 사주", page_icon="🌓")

st.title("🌓 AI 사주 상담소")
st.markdown("---")
st.write("요즘 마음이 복잡하거나 다가올 미래가 막막하게 느껴지시나요? 잠시 마음의 짐을 내려놓고 저에게 털어 놓아 보세요.")

# --- 입력 폼 ---
with st.form("saju_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름", placeholder="이름 입력")
        gender = st.selectbox("성별", ["여성", "남성"])
        
        # 날짜 기준 선택
        calendar_type = st.radio(
            "알고 있는 날짜는?", 
            ("양력 (Solar)", "음력 (Lunar)"),
            horizontal=True,
            help="보통 주민등록 상의 생일은 양력입니다."
        )
        
        # 윤달 체크 (음력 선택 시에만 보임)
        is_yun = False
        if "음력" in calendar_type:
            is_yun = st.checkbox("윤달입니까? (모르면 해제)", value=False)

    with col2:
        birth_date = st.date_input(
            "생년월일", 
            value=datetime(1990, 1, 1), 
            min_value=datetime(1900, 1, 1),
            help="연도를 클릭하여 빠르게 이동할 수 있습니다."
        )
        
        # 태어난 시간 입력 (모를 경우 체크)
        birth_time = st.time_input(
            "태어난 시간", 
            value=datetime.strptime("12:00", "%H:%M"),
            step=1800,
            disabled=st.session_state.get("unknown_time_check", False)
        )
        unknown_time = st.checkbox("태어난 시간을 모릅니다", key="unknown_time_check")

    concern = st.text_area("현재 고민을 최대한 구체적으로 적어주세요. (예시: 내년에 일이 어떻게 풀릴 지 궁금해요. 재물운은 어떨까요.)", height=80)
    submitted = st.form_submit_button("🔮 내 운명 확인하기", use_container_width=True)

# --- 로직 처리 ---
if submitted:
    if not name:
        st.error("이름을 입력해주세요.")
    else:
        try:
            calendar = KoreanLunarCalendar()
            
            # 1. 날짜 변환 로직
            if "음력" in calendar_type:
                # 음력 -> 양력 변환 (사주 계산용)
                calendar.setLunarDate(birth_date.year, birth_date.month, birth_date.day, is_yun)
                
                solar_date_str = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay).strftime('%Y년 %m월 %d일')
                lunar_date_str = f"{birth_date.year}년 {birth_date.month}월 {birth_date.day}일" + ("(윤달)" if is_yun else "")
                
                # 안내 메시지
                st.info(f"💡 입력하신 **음력 {lunar_date_str}**을 **양력 {solar_date_str}**로 변환하여 분석합니다.")
                final_solar_date = solar_date_str 

            else:
                # 양력 -> 음력 변환 (사용자 참고용)
                calendar.setSolarDate(birth_date.year, birth_date.month, birth_date.day)
                
                solar_date_str = birth_date.strftime('%Y년 %m월 %d일')
                lunar_date_str = calendar.LunarIsoFormat() 
                
                st.success(f"💡 **양력 {solar_date_str}**에 태어나셨군요! (음력으로는 **{lunar_date_str}** 입니다)")
                final_solar_date = solar_date_str

            # 2. 시간 문자열 처리
            if unknown_time:
                time_str = "모름 (시간을 제외한 삼주(Year, Month, Day)로만 분석해주세요)"
            else:
                time_str = birth_time.strftime('%H시 %M분')

            # 3. 프롬프트 생성
            prompt = f"""
            당신은 30년 경력의 정통 명리학자입니다.
            
            [사용자 정보]
            - 이름: {name} ({gender})
            - 사주 기준일(양력): {final_solar_date} (절기력 기준일)
            - 참고(음력): {lunar_date_str}
            - 태어난 시간: {time_str}
            - 고민: {concern if concern else "없음"}

            [지시사항]
            1. **기질 분석:** 위 '양력 날짜'를 기준으로 명리학적 사주(오행)를 분석하여 타고난 성향을 설명하세요. (시간을 모를 경우 삼주로만 분석하세요)
            2. **2026년 운세:** 2025년의 운세 흐름을 간략히 참고하여, 다가오는 2026년의 재물, 직업, 연애 운을 중점적으로 구체적인 흐름으로 서술하세요.
            3. **조언:** 고민에 대해 따뜻하면서도 현실적인 조언을 해주세요.
            4. **말투:** 전문적이지만 이해하기 쉽게 풀어서 설명하세요.
            """

            with st.spinner(f"{name}님의 사주를 분석 중입니다..."):
                response = model.generate_content(prompt)
                st.markdown("---")
                st.subheader(f"📜 {name}님의 사주 풀이")
                st.markdown(response.text)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
