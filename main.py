import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("영화진흥위원회(KOBIS) 일일 박스오피스")


# --------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 계산
# --------------------------------------------------
# Streamlit Cloud 서버의 시간이 한국 시간이 아닐 수 있으므로
# 서버의 현재 시간 대신 한국(KST) 시간대를 명시적으로 사용합니다.

KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API에서 사용하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여 줄 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 3. KOBIS API 주소
# --------------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# --------------------------------------------------
# 4. API에서 데이터 가져오기
# --------------------------------------------------
# @st.cache_data(ttl=3600)
# → 같은 날짜의 데이터를 1시간 동안 기억합니다.
# → 1시간 안에 앱을 다시 실행해도 API를 다시 호출하지 않습니다.

@st.cache_data(ttl=3600)
def get_boxoffice(api_key, target_date):
    """KOBIS에서 해당 날짜의 박스오피스 데이터를 가져옵니다."""

    params = {
        "key": api_key,
        "targetDt": target_date
    }

    # API 요청
    response = requests.get(
        API_URL,
        params=params,
        timeout=10
    )

    # HTTP 오류가 발생하면 예외 발생
    response.raise_for_status()

    # JSON 데이터로 변환
    data = response.json()

    return data


# --------------------------------------------------
# 5. Secrets에서 인증키 가져오기
# --------------------------------------------------

try:
    # Streamlit Cloud의 Secrets에
    # KOBIS_KEY = "발급받은 인증키"
    # 형태로 저장해야 합니다.
    api_key = st.secrets["KOBIS_KEY"]

except Exception:
    st.error("🔐 KOBIS 인증키를 찾을 수 없습니다.")

    st.info(
        """
        다음 내용을 확인해 주세요.

        1. Streamlit Cloud의 앱 설정에서 **Secrets**를 열었는지 확인하세요.
        2. Secret 이름이 정확히 `KOBIS_KEY`인지 확인하세요.
        3. 인증키를 따옴표 안에 정상적으로 입력했는지 확인하세요.

        예:
        `KOBIS_KEY = "발급받은_인증키"`
        """
    )

    st.stop()


# --------------------------------------------------
# 6. API 호출
# --------------------------------------------------

try:
    data = get_boxoffice(api_key, target_date)

except requests.exceptions.Timeout:
    st.error("⏱️ KOBIS API 응답 시간이 초과되었습니다.")

    st.info(
        "잠시 후 다시 실행해 보세요. "
        "인터넷 연결이나 KOBIS 서버 상태도 확인해 주세요."
    )

    st.stop()

except requests.exceptions.RequestException as e:
    st.error("🌐 KOBIS API에 접속하지 못했습니다.")

    st.info(
        "인터넷 연결, KOBIS API 주소, KOBIS 서버 상태 등을 확인해 주세요."
    )

    st.stop()

except Exception:
    st.error("❗ 박스오피스 데이터를 불러오는 중 오류가 발생했습니다.")

    st.info(
        "KOBIS API 응답 형식이나 인증키 설정을 확인해 주세요."
    )

    st.stop()


# --------------------------------------------------
# 7. KOBIS의 오류 정보(faultInfo) 확인
# --------------------------------------------------
# KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
# 따라서 상태코드만 확인하면 안 되고 faultInfo를 직접 확인해야 합니다.

if "faultInfo" in data:

    fault_info = data["faultInfo"]

    # 오류 메시지가 있으면 화면에 표시
    error_message = fault_info.get(
        "message",
        "KOBIS API에서 오류가 발생했습니다."
    )

    st.error(f"🚨 KOBIS API 오류: {error_message}")

    st.info(
        """
        다음 내용을 확인해 주세요.

        • Streamlit Secrets의 `KOBIS_KEY`가 정확한지 확인
        • KOBIS에서 발급받은 인증키가 활성화되어 있는지 확인
        • API 요청 날짜가 올바른지 확인
        • KOBIS API 서버에 문제가 없는지 확인
        """
    )

    st.stop()


# --------------------------------------------------
# 8. boxOfficeResult 확인
# --------------------------------------------------

if "boxOfficeResult" not in data:

    st.error("📭 박스오피스 결과를 찾을 수 없습니다.")

    st.info(
        "KOBIS API의 응답 형식이 예상과 다른지 확인해 주세요."
    )

    st.stop()


boxoffice_result = data["boxOfficeResult"]


# --------------------------------------------------
# 9. 영화 목록 가져오기
# --------------------------------------------------

movie_list = boxoffice_result.get("dailyBoxOfficeList", [])


# 영화 목록이 비어 있는 경우
if not movie_list:

    st.warning("📭 해당 날짜의 영화 목록이 없습니다.")

    st.info(
        f"""
        조회 날짜: {display_date}

        다음 내용을 확인해 주세요.

        • KOBIS에 해당 날짜의 박스오피스 자료가 등록되었는지 확인
        • 조회 날짜가 올바른지 확인
        • KOBIS API가 정상적으로 응답했는지 확인
        • 인증키가 정상적으로 작동하는지 확인
        """
    )

    st.stop()


# --------------------------------------------------
# 10. DataFrame으로 변환
# --------------------------------------------------

df = pd.DataFrame(movie_list)


# --------------------------------------------------
# 11. 숫자 데이터 변환
# --------------------------------------------------
# KOBIS API에서는 숫자도 문자열로 전달됩니다.
# 예: "12345" → 12345
#
# 숫자로 변환해야 정렬과 그래프에서 제대로 사용할 수 있습니다.

number_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

for column in number_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).fillna(0).astype(int)


# 순위 기준으로 정렬
df = df.sort_values("rank")


# --------------------------------------------------
# 12. 조회 날짜 표시
# --------------------------------------------------

st.subheader(f"📅 {display_date} 박스오피스")


# --------------------------------------------------
# 13. 1위 영화 정보
# --------------------------------------------------

first_movie = df.iloc[0]

st.markdown("## 🏆 오늘의 1위 영화")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🎟️ 당일 관객수",
        value=f"{first_movie['audiCnt']:,}명"
    )

with col2:
    st.metric(
        label="👥 누적 관객수",
        value=f"{first_movie['audiAcc']:,}명"
    )

with col3:
    st.metric(
        label="🎬 스크린수",
        value=f"{first_movie['scrnCnt']:,}개"
    )

st.markdown(
    f"### 🥇 {first_movie['movieNm']}"
)

st.caption(
    f"개봉일: {first_movie['openDt']}"
)


# --------------------------------------------------
# 14. 박스오피스 전체 표
# --------------------------------------------------

st.subheader("📊 전체 박스오피스")

# 화면에 보여 줄 열만 선택
table_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()


# 열 이름을 한국어로 변경
table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# 숫자에 천 단위 쉼표 적용
table_df["관객수"] = table_df["관객수"].map(
    lambda x: f"{x:,}"
)

table_df["누적관객"] = table_df["누적관객"].map(
    lambda x: f"{x:,}"
)

table_df["스크린수"] = table_df["스크린수"].map(
    lambda x: f"{x:,}"
)


st.dataframe(
    table_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 15. 관객수 상위 5편 막대그래프
# --------------------------------------------------

st.subheader("🎟️ 관객수 상위 5편")

top5 = (
    df
    .sort_values("audiCnt", ascending=False)
    .head(5)
    .copy()
)

# 그래프용 데이터는 숫자 그대로 유지
# 영화명이 긴 경우에도 그래프가 보기 쉽도록 순위를 함께 표시
top5["표시명"] = (
    top5["rank"].astype(str)
    + "위 "
    + top5["movieNm"]
)

# Streamlit의 기본 bar chart 사용
chart_df = top5.set_index("표시명")[["audiCnt"]]

st.bar_chart(
    chart_df,
    x_label="영화",
    y_label="관객수"
)


# --------------------------------------------------
# 16. 데이터 기준 안내
# --------------------------------------------------

st.caption(
    f"※ 조회 기준일: {display_date} · "
    "KOBIS 일일 박스오피스 · 데이터는 약 1시간 동안 캐시됩니다."
)
