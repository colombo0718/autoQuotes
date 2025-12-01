import streamlit as st
import pandas as pd
import numpy as np

# 頁面標題
st.title("Streamlit 範例：按一下就跑 Python")

st.write("這是一個最小範例：有按鈕、有表格、有圖表。")

# 範例按鈕
if st.button("執行一個 Python 函式"):
    st.write("✅ 按鈕被按下了，我在這裡做一些事（例如：結帳、寫入資料庫、呼叫 API）")

# 做一個假資料表：每月營業額
months = ["1月", "2月", "3月", "4月", "5月", "6月"]
revenue = np.random.randint(100, 300, size=len(months))

df = pd.DataFrame({
    "月份": months,
    "營業額": revenue
})

st.subheader("假裝是營業額報表")
st.dataframe(df)

# 繪製簡單長條圖
st.bar_chart(df.set_index("月份"))
