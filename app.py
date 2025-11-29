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

# 👇 [디자인 업그레이드] 버튼을 고급스럽게 꾸미는 CSS 스타일
st.markdown("""
<style>
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        color: white;
        font-size: 18px;
        font-weight: bold;
        border: none;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #2575fc 0%, #6a11cb 100%);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

st.title("🌓 AI 사주 상담소")
st.markdown("---")
st.write("마음이 복잡하거나 다가올 미래가 막막하게 느껴지시나요? 잠시 마음의 짐을 내려놓고 저에게 털어놓아 보세요 ☺️\n\n생년월일 정보만 입력하여도 사주 확인이 가능합니다.")

# --- 입력 폼 ---
with st.form("saju_form"):
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("이름 (선택사항)", placeholder="입력하지 않아도 됩니다")
        gender = st.selectbox("성별", ["여성", "남성"])
        
        calendar_type = st.radio(
            "알고 있는 날짜는?", 
            ("양력 (Solar)", "음력 (Lunar)"),
            horizontal=True,
            help="보통 주민등록 상의 생일은 양력입니다."
        )
        
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
        
        birth_time = st.time_input(
            "태어난 시간", 
            value=datetime.strptime("12:00", "%H:%M"),
            step=1800,
            disabled=st.session_state.get("unknown_time_check", False)
        )
        unknown_time = st.checkbox("태어난 시간을 모릅니다", key="unknown_time_check")

    concern = st.text_area("현재 고민을 최대한 구체적으로 적어주세요.\n(예시: 내년에 일이 어떻게 풀릴 지 궁금해요. 재물운은 어떨까요.)", height=80)
    submitted = st.form_submit_button("🌌 천기누설! 내 운명 확인하기", use_container_width=True)

# --- 로직 처리 ---
if submitted:
    display_name = name if name else "방문자"

    try:
        calendar = KoreanLunarCalendar()
        
        # 1. 날짜 변환 및 '정확한 간지(Gapja)' 계산
        if "음력" in calendar_type:
            calendar.setLunarDate(birth_date.year, birth_date.month, birth_date.day, is_yun)
            lunar_date_str = f"{birth_date.year}년 {birth_date.month}월 {birth_date.day}일" + ("(윤달)" if is_yun else "")
        else:
            calendar.setSolarDate(birth_date.year, birth_date.month, birth_date.day)
            lunar_date_str = calendar.LunarIsoFormat()

        # 양력 날짜 문자열
        solar_date_str = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay).strftime('%Y년 %m월 %d일')
        
        # 👇 [핵심 수정] 라이브러리가 직접 계산한 정확한 사주(간지) 가져오기
        # 예: "갑자년 을축월 병인일" 형태로 반환됨 (AI가 계산할 필요 없음!)
        saju_ganji = calendar.getGapJaString() 

        # 사용자에게 안내
        st.info(f"💡 분석 기준: 양력 **{solar_date_str}** / 사주: **{saju_ganji}**")
        
        # 2. 시간 처리
        if unknown_time:
            time_str = "모름 (시간을 제외한 삼주로만 분석)"
        else:
            time_str = birth_time.strftime('%H시 %M분')

        # 3. 프롬프트 생성 (AI에게 정답 사주를 알려줌)
        prompt = f"""
        당신은 30년 경력의 정통 명리학자입니다.
        제가 이미 정확한 만세력 정보를 계산해서 제공하니, **당신은 별도의 날짜 계산을 하지 말고 아래 제공된 [확정된 사주] 정보를 그대로 해석**만 하세요.
        
        [사용자 정보]
        - 이름/호칭: {display_name} ({gender})
        - 사주 기준일(양력): {solar_date_str}
        - **[확정된 사주(년월일)]: {saju_ganji}** (이 정보가 절대적인 기준입니다. 다른 계산 하지 마세요.)
        - 태어난 시간: {time_str}
        - 고민: {concern if concern else "없음"}

        [지시사항]
        1. **일주(Day Pillar) 분석:** 위 [확정된 사주]에서 '일주(태어난 날의 기둥)'를 찾아, 그 일주가 가진 타고난 기질과 특성을 깊이 있게 분석하세요. (예: 갑자일주라면 갑자일주의 특성 설명)
        2. **오행 분석:** 사주팔자 전체의 오행(목화토금수) 구성을 살펴보고 과하거나 부족한 기운에 대해 조언하세요.
        3. **2026년 운세:** 2025년의 흐름을 참고하여 2026년(병오년)의 재물, 직업, 연애 운을 구체적으로 예측하세요.
        4. **맞춤 조언:** 사용자의 고민에 대해 따뜻하고 현실적인 조언을 해주세요.
        
        [말투 가이드]
        - "~입니다", "~합니다" 체를 기본으로 하되, 신비롭고 따뜻한 멘토의 느낌을 주세요.
        - 전문 용어는 쉽게 풀어서 설명하세요.
        """

        with st.spinner(f"{display_name}님의 사주({saju_ganji})를 분석 중입니다..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.subheader(f"📜 {display_name}님의 사주 풀이")
            st.markdown(response.text)

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
