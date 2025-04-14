import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from utils import initialize_session, get_next_conversation_number, chat, save_api_key, manage_conversations
import os
import uuid
import json


def main():
    st.title("🤖 Local Chatbot with API")

    initialize_session()
    with st.sidebar:
        st.header("Settings")
        st.session_state.temp_api_key = st.text_input("OpenAI API Key", value=st.session_state.temp_api_key, type="password")

        if st.session_state.api_key != "":
            save_api_key()
        else:
            if st.button("Save API Key"):
                save_api_key()
        manage_conversations()

    client = None
    if st.session_state.api_key:
        try:
            client = OpenAI(api_key=st.session_state.api_key)
        except Exception as e:
            st.error("Invalid API key. Please check and try again.")
    else:
        st.warning("Please enter and save your OpenAI API key in the sidebar to start chatting.")

    chat(client)


if __name__ == '__main__':
    main()