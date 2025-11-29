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
# 👇 요청하신 감성적인 문구 적용
st.write("마음이 복잡하거나 다가올 미래가 막막하게 느껴지시나요? 잠시 마음의 짐을 내려놓고 저에게 털어 놓아 보세요. 생년월일 정보만 입력하여도 사주 확인이 가능합니다.")

# --- 입력 폼 ---
with st.form("saju_form"):
    col1, col2 = st.columns(2)
    with col1:
        # 👇 이름을 선택사항으로 변경
        name = st.text_input("이름 (선택)", placeholder="입력하지 않아도 됩니다")
        gender = st.selectbox("성별", ["여성", "남성"])
        
        # 날짜 기준 선택
        calendar_type = st.radio(
            "알고 있는 날짜는?", 
            ("양력 (Solar)", "음력 (Lunar)"),
            horizontal=True,
            help="보통 주민등록상 생일은 양력입니다."
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

    # 👇 요청하신 고민 입력 예시 문구 적용
    concern = st.text_area("현재 고민을 최대한 구체적으로 적어주세요. (예시: 내년에 일이 어떻게 풀릴 지 궁금해요. 재물운은 어떨까요.)", height=80)
    submitted = st.form_submit_button("🔮 내 운명 확인하기", use_container_width=True)

# --- 로직 처리 ---
if submitted:
    # 이름이 없으면 기본 호칭 사용
    display_name = name if name else "방문자"

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

        # 3. 프롬프트 생성 (만세력 분석 강화)
        prompt = f"""
        당신은 30년 경력의 정통 명리학자입니다.
        
        [사용자 정보]
        - 이름/호칭: {display_name} ({gender})
        - 사주 기준일(양력): {final_solar_date} (절기력 기준일)
        - 참고(음력): {lunar_date_str}
        - 태어난 시간: {time_str}
        - 고민: {concern if concern else "없음"}

        [지시사항]
        1. **만세력 심층 분석:** - 사용자의 사주팔자(네 기둥: 년주, 월주, 일주, 시주)를 명확하게 제시하세요. (시간을 모를 경우 시주는 제외)
           - 각 기둥의 천간과 지지가 의미하는 바를 풀이하고, 오행(목, 화, 토, 금, 수)의 분포와 균형에 대해 자세히 설명해 주세요.
           - 본인을 상징하는 '일주(Day Pillar)'의 특성을 중심으로 타고난 기질과 잠재력을 깊이 있게 분석하세요.
           - 배우자 혹은 동료는 어떤 사람과 잘 맞는 지도 간단히 분석하여 설명해주세요.
           
        2. **2026년 운세:** - 2025년의 운세 흐름을 간략히 참고하여, 다가오는 2026년의 재물, 직업, 연애 운을 중점적으로 구체적인 흐름으로 서술하세요.
           
        3. **맞춤 조언:** - 사용자의 고민에 대해 따뜻하면서도 현실적인 조언을 해주세요.
           
        4. **형식:** - 전문 용어(갑자, 을축 등)는 괄호 안에 한자를 병기하거나 쉽게 풀어서 설명하세요.
           - 가독성 좋게 소제목을 사용하세요.
           - 어조는 신비로우면서도 내담자를 위로하는 따뜻한 말투를 유지하세요.
        """

        with st.spinner(f"{display_name}님의 사주를 분석 중입니다..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.subheader(f"📜 {display_name}님의 사주 풀이")
            st.markdown(response.text)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
