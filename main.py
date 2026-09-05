import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="서울의 100년 기온",
    page_icon="🌡️",
    layout="wide"
)

# 제목
st.title("🌡️ 서울의 100년 기온 변화")
st.write("서울의 일별 기온 데이터를 이용하여 연평균 기온의 변화를 살펴봅니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"])

    # 평균기온을 숫자형으로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    return df


# 데이터 불러오기
df = load_data()

# 연도별 평균기온 계산
yearly_temp = (
    df.dropna(subset=["평균기온"])
    .groupby("연도")["평균기온"]
    .mean()
    .reset_index()
)

# 소수점 둘째 자리까지 표시
yearly_temp["평균기온"] = yearly_temp["평균기온"].round(2)

# 기간 정보
start_year = yearly_temp["연도"].min()
end_year = yearly_temp["연도"].max()

st.subheader(f"📈 {start_year}년~{end_year}년 연평균 기온 변화")

# 그래프
fig = px.line(
    yearly_temp,
    x="연도",
    y="평균기온",
    markers=True,
    labels={
        "연도": "연도",
        "평균기온": "연평균 기온(℃)"
    }
)

fig.update_layout(
    hovermode="x unified",
    height=550,
    xaxis=dict(
        dtick=10
    ),
    yaxis=dict(
        title="연평균 기온(℃)"
    )
)

st.plotly_chart(fig, use_container_width=True)

# 간단한 정보
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "분석 기간",
        f"{start_year}~{end_year}"
    )

with col2:
    st.metric(
        "가장 낮은 연평균 기온",
        f"{yearly_temp['평균기온'].min():.2f} ℃"
    )

with col3:
    st.metric(
        "가장 높은 연평균 기온",
        f"{yearly_temp['평균기온'].max():.2f} ℃"
    )

st.caption("자료: 서울 기상관측 데이터")

# 일별 평균기온 분포
st.subheader("🌡️ 일별 평균기온 분포")
st.write("전체 관측일의 평균기온이 어느 온도 구간에 얼마나 많이 나타났는지 보여줍니다.")

fig_hist = px.histogram(
    df.dropna(subset=["평균기온"]),
    x="평균기온",
    nbins=30,
    labels={
        "평균기온": "평균기온(℃)",
        "count": "관측일 수"
    }
)

fig_hist.update_layout(
    height=500,
    xaxis_title="평균기온(℃)",
    yaxis_title="관측일 수"
)

st.plotly_chart(fig_hist, use_container_width=True)
