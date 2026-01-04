import streamlit as st

st.set_page_config(page_title="Testing...")
st.title("🚀 The Server is Working!")
st.write("If you can see this, the environment is fine.")

if st.button("Click me"):
    st.balloons()