import streamlit as st

st.set_page_config(page_title="Test Router", initial_sidebar_state="collapsed")

if "count" not in st.session_state:
    st.session_state.count = 0

st.write("Session count:", st.session_state.count)
if st.button("Increment"):
    st.session_state.count += 1
    st.rerun()

st.markdown("""
<div style="display: none;" id="hidden-routers">
""", unsafe_allow_html=True)
st.page_link("app.py", label="App")
st.page_link("pages/upload.py", label="Upload")
st.markdown("""
</div>
""", unsafe_allow_html=True)

st.markdown("""
<button onclick="
    const links = window.parent.document.querySelectorAll('a');
    let target = Array.from(links).find(a => a.href.endsWith('/upload'));
    if (target) { target.click(); } else { alert('not found'); }
">Test Router Javascript</button>
""", unsafe_allow_html=True)
