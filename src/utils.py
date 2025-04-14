import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import os
import uuid

def initialize_session():
    """Initialize session state variables."""
    load_dotenv()

    if "api_key" not in st.session_state:
        st.session_state.api_key = os.getenv("OPENAI_API_KEY") or ""

    if "temp_api_key" not in st.session_state:
        st.session_state.temp_api_key = st.session_state.api_key

    if "conversations" not in st.session_state:
        st.session_state.conversations = {}

    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None

    # Initialize selected_conversation for notification
    if "selected_conversation" not in st.session_state:
        st.session_state.selected_conversation = None

def get_next_conversation_number():
    """Get the next available conversation number."""
    used_numbers = []
    for conv_data in st.session_state.conversations.values():
        try:
            # Assuming names are like "Conversation X"
            number = int(conv_data["name"].split()[-1])
            used_numbers.append(number)
        except (ValueError, IndexError):
            continue
    next_number = 1
    while next_number in used_numbers:
        next_number += 1
    return next_number

def save_api_key():
    """Save the API key after validation."""
    try:
        test_client = OpenAI(api_key=st.session_state.temp_api_key)
        test_client.models.list()
        st.session_state.api_key = st.session_state.temp_api_key
        st.success("API Key saved successfully!")
    except Exception as e:
        st.error("Invalid API key! Please check and try again.")

def manage_conversations():
    """Handle conversation creation, selection, renaming, and deletion."""
    col1, col2 = st.columns([4, 1])
    with col1:
        st.header("Conversation")
    with col2:
        if st.session_state.api_key:
            if st.button("💬"):
                new_conversation_id = str(uuid.uuid4())
                next_number = get_next_conversation_number()
                st.session_state.conversations[new_conversation_id] = {
                    "name": f"Conversation {next_number}",
                    "messages": []
                }
                st.session_state.current_conversation_id = new_conversation_id
                st.session_state.selected_conversation = st.session_state.conversations[new_conversation_id]["name"]
                st.rerun()

    if st.session_state.conversations:
        for conv_id, conv_data in st.session_state.conversations.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                new_name = st.text_input("Rename", value=conv_data["name"], key=f"rename_{conv_id}", label_visibility="collapsed")
                if new_name != conv_data["name"]:
                    st.session_state.conversations[conv_id]["name"] = new_name
            with col2:
                if st.button("🟢", key=f"select_{conv_id}", use_container_width=True):
                    st.session_state.selected_conversation = conv_data["name"]
                    st.session_state.current_conversation_id = conv_id
                    st.rerun()
            with col3:
                if st.button("❌", key=f"delete_{conv_id}", use_container_width=True):
                    # Get the number of the deleted conversation
                    try:
                        deleted_number = int(conv_data["name"].split()[-1])
                    except (ValueError, IndexError):
                        deleted_number = float('-inf')  # Fallback if name is malformed

                    is_current = st.session_state.current_conversation_id == conv_id
                    del st.session_state.conversations[conv_id]

                    if is_current:
                        # Find the conversation with the smallest number greater than deleted_number
                        next_conv_id = None
                        min_number = float('inf')
                        for cid, cdata in st.session_state.conversations.items():
                            try:
                                num = int(cdata["name"].split()[-1])
                                if num > deleted_number and num < min_number:
                                    min_number = num
                                    next_conv_id = cid
                            except (ValueError, IndexError):
                                continue

                        st.session_state.current_conversation_id = next_conv_id
                        st.session_state.selected_conversation = (
                            st.session_state.conversations[next_conv_id]["name"]
                            if next_conv_id else None
                        )
                    st.rerun()

    if st.session_state.selected_conversation:
        st.info(f"Selected {st.session_state.selected_conversation}")

def display_chat_messages():
    """Display chat messages for the current conversation."""
    current_conv = st.session_state.conversations[st.session_state.current_conversation_id]
    for message in current_conv["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_user_input(client):
    """Handle user input and generate assistant response."""
    current_conv = st.session_state.conversations[st.session_state.current_conversation_id]

    if prompt := st.chat_input("Ask anything..."):
        current_conv["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""

            try:
                stream = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in current_conv["messages"]
                    ],
                    stream=True,
                )

                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)
                current_conv["messages"].append({"role": "assistant", "content": full_response})

            except Exception as e:
                st.error("Error fetching response. Please check your API key or try again.")

def chat(client):
    """Main chat function to control the chat flow."""
    if st.session_state.current_conversation_id and st.session_state.api_key:
        display_chat_messages()
        handle_user_input(client)