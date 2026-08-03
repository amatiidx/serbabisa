import streamlit as st
import os

st.set_page_config(page_title="Stock Scanner Monitor", layout="wide")
st.title("📈 Stock Scanner Dashboard Monitor")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Master Engine Log")
    if os.path.exists("engine.log"):
        with open("engine.log", "r") as f:
            st.text_area("Engine Output", f.read(), height=400)
    else:
        st.info("Log belum tersedia.")

with col2:
    st.subheader("Auto Scanner Log")
    if os.path.exists("auto.log"):
        with open("auto.log", "r") as f:
            st.text_area("Auto Output", f.read(), height=400)
    else:
        st.info("Log belum tersedia.")

with col3:
    st.subheader("Bandar Accumulation Log")
    if os.path.exists("bandar.log"):
        with open("bandar.log", "r") as f:
            st.text_area("Bandar Output", f.read(), height=400)
    else:
        st.info("Log belum tersedia.")
