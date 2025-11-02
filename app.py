import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import FinanceDataReader as fdr
import streamlit as st

st.set_page_config(layout="wide")
st.title("📈 주가 추세 및 외국인 동향 분석")

# 종목 선택
st.sidebar.header("종목 선택")
ticker = st.sidebar.text_input("티커 입력 (예: AAPL, TSLA, 005930.KS, 000660.KS)", "005930.KS")

# 기간 선택
period = st.sidebar.selectbox("기간 선택", ["1y", "6mo", "3mo", "1mo", "5y", "max"], index=0)

# 데이터 가져오기
df = yf.download(ticker, period=period)
df.dropna(inplace=True)

# 이동평균선 계산
df["MA20"] = df["Close"].rolling(20).mean()
df["MA60"] = df["Close"].rolling(60).mean()

# 주가 차트
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
    name="Candlestick"
))
fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], line=dict(color='orange', width=1.5), name="MA20"))
fig.add_trace(go.Scatter(x=df.index, y=df["MA60"], line=dict(color='green', width=1.5), name="MA60"))
fig.update_layout(title=f"{ticker} 주가 추세", xaxis_rangeslider_visible=False, height=600)

st.plotly_chart(fig, use_container_width=True)

# --- 외국인 동향 ---
if ticker.endswith(".KS") or ticker.endswith(".KQ"):
    st.subheader("외국인 / 기관 / 개인 투자자 추세")
    try:
        code = ticker.replace(".KS", "").replace(".KQ", "")
        df_inv = fdr.DataReader(code)
        df_inv = df_inv[['ForeignInvestors', 'Individual', 'Institution']]
        df_inv = df_inv.tail(120)  # 최근 6개월

        fig2 = go.Figure()
        for col, color in zip(df_inv.columns, ['blue', 'orange', 'green']):
            fig2.add_trace(go.Scatter(x=df_inv.index, y=df_inv[col], name=col, line=dict(color=color)))
        fig2.update_layout(title="투자자 매매 추이 (최근 6개월)", height=400)
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.warning(f"외국인 동향 데이터를 불러오지 못했습니다: {e}")
else:
    st.info("외국인 동향 데이터는 한국 주식(‘.KS’, ‘.KQ’)에만 지원됩니다.")
