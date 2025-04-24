
import streamlit as st
st.set_page_config(page_title="Chatbot Rangdong 🤖", layout="wide")
st.title("💬 Chatbot Rangdong")

import os
import json
import sys
os.environ["STREAMLIT_WATCH_USE_POLLING"] = "true"

import asyncio
from utils import *
from api import agent
import requests

# Initialize session state for the chat agent
if "agent" not in st.session_state:
    st.session_state.agent = agent

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat messages
for sender, message in st.session_state.chat_history:
    with st.chat_message(sender):
        st.markdown(message)

# Streamlit chat input
user_input = st.chat_input("Nhập tin nhắn của bạn...")
if user_input:
    if user_input.lower() == 'reset':
        st.session_state.chat_history = []
        st.session_state.chat_history.append(("assistant", "🔄 Cuộc trò chuyện đã được đặt lại!"))
        st.rerun()
    else:
    # Add user input
        st.session_state.chat_history.append(("user", user_input))

        with st.spinner("🤖 Đang xử lý..."):
            try:
                chat_history = [{"role": sender, "content": message} for sender, message in st.session_state.chat_history]
                api_response = requests.post("http://localhost:8000/chat", json={"message": user_input, "history": chat_history})
                response = api_response.json().get("response")
            except Exception as e:
                response = f"❌ Error contacting backend: {str(e)}"
            st.session_state.chat_history.append(("assistant", response))
    st.rerun()
    