import streamlit as st
import asyncio
from utils import *
from api import agent
import requests
st.set_page_config(page_title="Chatbot Rangdong 🤖", layout="wide")
st.title("💬 Chatbot Rangdong")

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
    if user_input.lower() in ['quit', 'exit']:
        st.session_state.chat_history.append(("assistant", "👋 Goodbye! Have a great day!"))
        st.rerun()
    elif user_input.lower() == 'reset':
        st.session_state.agent.reset()
        st.session_state.chat_history = []
        st.session_state.chat_history.append(("assistant", "🔄 Cuộc trò chuyện đã được đặt lại!"))
        st.rerun()
    else:
    # Add user input
        st.session_state.chat_history.append(("user", user_input))

        with st.spinner("🤖 Đang xử lý..."):
            try:
                api_response = requests.post("http://localhost:8000/chat", json={"message": user_input})
                response = api_response.json().get("response")
                
            except Exception as e:
                response = f"❌ Error contacting backend: {str(e)}"
            st.session_state.chat_history.append(("assistant", response))
    st.rerun()