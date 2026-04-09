import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Heritage Lens Agent",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ Heritage Lens Agent")
st.subheader("AI-powered cultural heritage exploration")

st.markdown("""
Welcome to Heritage Lens Agent! This application helps you explore
cultural heritage through AI-powered insights and vector search.
""")

# Sidebar
with st.sidebar:
    st.header("Configuration")

    # OpenClaw Gateway status
    gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://localhost:18789")
    st.text_input("OpenClaw Gateway URL", gateway_url, key="gateway_url")

    # Qdrant status
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    st.text_input("Qdrant URL", qdrant_url, key="qdrant_url")

    st.divider()
    st.info("Docker-based deployment with Streamlit + Qdrant")

# Main content
st.divider()

col1, col2 = st.columns(2)

with col1:
    st.header("🔍 Search Heritage")
    query = st.text_input("Enter your search query:")
    if query:
        st.info(f"Searching for: {query}")
        st.warning("Vector search integration pending - connect to Qdrant")

with col2:
    st.header("🤖 AI Assistant")
    prompt = st.text_area("Ask the AI about cultural heritage:")
    if st.button("Send"):
        if prompt:
            st.info(f"Prompt: {prompt}")
            st.warning("OpenClaw integration pending - connect to gateway")

# System status
st.divider()
st.header("📊 System Status")

status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    st.metric("Streamlit", "✅ Running", "v1.32+")

with status_col2:
    st.metric("Qdrant", "⏳ Check Status", "Pending")

with status_col3:
    st.metric("OpenClaw", "⏳ Check Status", "Pending")

st.divider()
st.caption("Heritage Lens Agent | Built with OpenClaw, LlamaIndex & Streamlit")
