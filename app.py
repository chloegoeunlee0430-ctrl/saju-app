import streamlit as st
import google.generativeai as genai
from datetime import datetime
from korean_lunar_calendar import KoreanLunarCalendar
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# 👇 [설정] API 키 및 구글 시트 설정
# ==========================================
try:
    # 1. Gemini API 키 가져오기
    MY_API_KEY = st.secrets["GEMINI_API_KEY"]
    
    # 2. 구글 시트 연동 키 가져오기
    # (Streamlit Secrets에 [gcp_service_account]가 있어야 합니다)
    GCP_SECRETS = st.secrets["gcp_service_account"]
    
except Exception:
    st.error("⚠️ Secrets 설정이 완벽하지 않습니다. (API Key 또는 GCP 서비스 계정 키 확인 필요)")
    st.stop()

TARGET_MODEL = "gemini-flash-latest"
SHEET_NAME = "saju_database" # ⚠️ 구글 시트 제목과 똑같아야 합니다!
# ==========================================


# --- 구글 시트 연결 함수 (캐싱 적용) ---
@st.cache_resource
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(GCP_SECRETS), scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# --- 시트 저장 함수 ---
def save_to_sheet(name, gender, birth, time, concern, result):
    try:
        sheet = get_google_sheet()
        # 저장할 데이터: [시간, 이름, 성별, 생년월일, 시간, 고민, 결과요약]
        sheet.append_row([
            str(datetime.now()), 
            name, 
            gender, 
            birth, 
            time, 
            concern, 
            result[:1000] # 엑셀 셀 용량 고려해서 1000자까지만 저장
        ])
        return True
    except Exception as e:
        print(f"저장 실패: {e}")
        return False


# --- 기본 설정 ---
genai.configure(api_key=MY_API_KEY)
model = genai.GenerativeModel(TARGET_MODEL)

st.set_page_config(page_title="정통 AI 사주", page_icon="🌓")

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
    
    # 버튼 (기본 스타일)
    submitted = st.form_submit_button("🔮 내 운명 확인하기", use_container_width=True)

# --- 로직 처리 ---
if submitted:
    display_name = name if name else "방문자"

    try:
        calendar = KoreanLunarCalendar()
        
        # 1. 날짜 변환 및 간지 계산
        if "음력" in calendar_type:
            calendar.setLunarDate(birth_date.year, birth_date.month, birth_date.day, is_yun)
            lunar_date_str = f"{birth_date.year}년 {birth_date.month}월 {birth_date.day}일" + ("(윤달)" if is_yun else "")
        else:
            calendar.setSolarDate(birth_date.year, birth_date.month, birth_date.day)
            lunar_date_str = calendar.LunarIsoFormat()

        solar_date_str = datetime(calendar.solarYear, calendar.solarMonth, calendar.solarDay).strftime('%Y년 %m월 %d일')
        saju_ganji = calendar.getGapJaString() 

        st.info(f"💡 분석 기준: 양력 **{solar_date_str}** / 사주: **{saju_ganji}**")
        
        # 2. 시간 처리
        if unknown_time:
            time_str = "모름 (시간을 제외한 삼주로만 분석)"
        else:
            time_str = birth_time.strftime('%H시 %M분')

        # 3. 프롬프트 생성
        prompt = f"""
        당신은 30년 경력의 정통 명리학자입니다.
        제가 이미 정확한 만세력 정보를 계산해서 제공하니, **당신은 별도의 날짜 계산을 하지 말고 아래 제공된 [확정된 사주] 정보를 그대로 해석**만 하세요.
        
        [사용자 정보]
        - 이름/호칭: {display_name} ({gender})
        - 사주 기준일(양력): {solar_date_str}
        - **[확정된 사주(년월일)]: {saju_ganji}** (이 정보가 절대적인 기준입니다.)
        - 태어난 시간: {time_str}
        - 고민: {concern if concern else "없음"}

        [지시사항]
        1. **일주(Day Pillar) 분석:** 위 [확정된 사주]에서 '일주(태어난 날의 기둥)'를 찾아, 그 일주가 가진 타고난 기질과 특성을 설명하세요.
        
        2. **오행 분석 (핵심만):** 사주 전체의 오행 구성을 보고 가장 특징적인 부분만 아주 짧게 언급하세요. (길게 설명하지 마세요)
        
        3. **나에게 필요한 사람 (귀인):** - 본인의 사주에 부족한 기운을 채워주거나 인생에 도움이 되는 '귀인'의 특징을 설명해 주세요.
           - 구체적으로 어떤 띠, 혹은 어떤 성향의 사람을 가까이하면 좋은지 현실적인 조언을 주세요.
        
        4. **2025년 vs 2026년 운세 흐름 (중점 사항):** - 먼저 **2025년(을사년)**의 운세가 어떠했는지(또는 어떠할지) 핵심 키워드로 요약하세요.
           - 이를 바탕으로 **2026년(병오년)**에는 운의 흐름이 어떻게 변화하는지 비교하여 상세히 설명하세요. 
           - 재물, 직업, 연애 측면에서 구체적인 변화를 서술하세요.
        
        5. **맞춤 조언:** 사용자의 고민에 대해 따뜻하고 현실적인 조언을 해주세요.
        
        [말투 가이드]
        - "~입니다", "~합니다" 체를 기본으로 하되, 신비롭고 따뜻한 멘토의 느낌을 주세요.
        - 전문 용어는 쉽게 풀어서 설명하세요.
        """

        with st.spinner(f"{display_name}님의 사주({saju_ganji})를 분석 중입니다..."):
            response = model.generate_content(prompt)
            
            # 👇 [핵심] 구글 시트에 자동 저장
            if 'gcp_service_account' in st.secrets:
                save_success = save_to_sheet(display_name, gender, solar_date_str, time_str, concern, response.text)
                if save_success:
                    st.toast("✅ 상담 내용이 데이터베이스에 안전하게 기록되었습니다.", icon="💾")
            
            # 결과 출력
            st.markdown("---")
            st.subheader(f"📜 {display_name}님의 사주 풀이")
            st.markdown(response.text)
            
            # 텍스트 파일 다운로드 버튼
            st.download_button(
                label="📄 결과 파일로 저장하기",
                data=response.text,
                file_name=f"{display_name}_사주풀이.txt",
                mime="text/plain"
            )

    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
