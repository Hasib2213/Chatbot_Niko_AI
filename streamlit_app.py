"""Streamlit Frontend for Nikoo AI Chat Application"""

import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"

# Streamlit page configuration
st.set_page_config(
    page_title="Nikoo AI Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS - Mobile-like design
st.markdown("""
    <style>
        /* Main container */
        .main {
            background: #1a1a1a;
            color: #fff;
        }
        
        /* Chat session cards */
        .session-card {
            background: linear-gradient(135deg, #8B0000 0%, #DC143C 100%);
            padding: 16px;
            margin: 12px 0;
            border-radius: 12px;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }
        
        .session-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        
        .session-title {
            font-size: 16px;
            font-weight: 600;
            color: white;
            margin: 0;
        }
        
        .session-meta {
            font-size: 12px;
            color: rgba(255,255,255,0.7);
            margin-top: 4px;
        }
        
        /* Chat messages */
        .user-msg {
            background: #DCF8C6;
            padding: 12px 16px;
            border-radius: 12px;
            margin: 8px 0 8px 40px;
            max-width: 80%;
            color: #000;
        }
        
        .assistant-msg {
            background: #E3F2FD;
            padding: 12px 16px;
            border-radius: 12px;
            margin: 8px 0 8px 0;
            max-width: 80%;
            color: #000;
        }
        
        /* Header */
        .header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 2px solid #333;
        }
        
        /* Button styles */
        .action-btn {
            background: #DC143C;
            color: white;
            border: none;
            padding: 10px 16px;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
        }
        
        .message-input {
            background: #2a2a2a;
            color: white;
            border: 1px solid #444;
            padding: 12px 16px;
            border-radius: 24px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "user_id" not in st.session_state:
    st.session_state.user_id = "default_user"

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "threads" not in st.session_state:
    st.session_state.threads = []

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

# Function to load messages from database
def load_thread_messages(thread_id, user_id):
    """Load all messages from a specific thread"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/threads/{thread_id}/{user_id}/messages",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("messages", [])
    except Exception as e:
        st.error(f"Error loading messages: {str(e)}")
    return []

# Main Header
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    if st.button("☰", key="menu_btn", help="Menu"):
        st.session_state.show_menu = True

with col2:
    st.markdown("<h1 style='text-align: center; margin: 0;'>💬 Conversations</h1>", unsafe_allow_html=True)

with col3:
    if st.button("➕", key="new_thread_btn", help="New Conversation"):
        st.session_state.thread_id = None
        st.session_state.messages = []
        st.rerun()

st.markdown("---")

# Two column layout
col_threads, col_chat = st.columns([1, 2.5])

# Left sidebar - Threads/Conversations
with col_threads:
    st.subheader("📋 Conversations")
    
    # Settings
    with st.expander("⚙️ Settings"):
        st.session_state.user_id = st.text_input(
            "User ID",
            value=st.session_state.user_id
        )
        
        if st.button("🔄 Refresh", use_container_width=True):
            try:
                response = requests.get(f"{API_BASE_URL}/api/threads/{st.session_state.user_id}")
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.threads = data.get("threads", [])
                    st.success(f"✅ Found {len(st.session_state.threads)} conversations")
                else:
                    st.error("Failed to fetch threads")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        if st.button("🏥 Health Check", use_container_width=True):
            try:
                response = requests.get(f"{API_BASE_URL}/health")
                if response.status_code == 200:
                    st.success("✅ API Connected")
                else:
                    st.error("❌ API Error")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Load threads on first load
    if not st.session_state.threads:
        try:
            response = requests.get(f"{API_BASE_URL}/api/threads/{st.session_state.user_id}")
            if response.status_code == 200:
                data = response.json()
                st.session_state.threads = data.get("threads", [])
        except:
            pass
    
    # Display threads as cards
    if st.session_state.threads:
        for i, thread in enumerate(st.session_state.threads):
            with st.container():
                col_card, col_delete = st.columns([0.85, 0.15])
                
                with col_card:
                    if st.button(
                        f"💬 {thread['thread_id']}\n📊 {thread['message_count']} messages",
                        key=f"thread_{i}",
                        use_container_width=True
                    ):
                        st.session_state.thread_id = thread['thread_id']
                        st.session_state.messages = load_thread_messages(
                            thread['thread_id'],
                            st.session_state.user_id
                        )
                        st.rerun()
                
                with col_delete:
                    if st.button("🗑️", key=f"del_{i}", help="Delete"):
                        try:
                            response = requests.delete(
                                f"{API_BASE_URL}/api/threads/{thread['thread_id']}/{st.session_state.user_id}"
                            )
                            if response.status_code == 200:
                                st.session_state.threads = [
                                    t for t in st.session_state.threads 
                                    if t['thread_id'] != thread['thread_id']
                                ]
                                if st.session_state.thread_id == thread['thread_id']:
                                    st.session_state.thread_id = None
                                    st.session_state.messages = []
                                st.success("✅ Deleted")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
    else:
        st.info("📭 No conversations yet\n\nClick ➕ to start a new conversation")

# Right side - Chat area
with col_chat:
    if not st.session_state.thread_id:
        st.markdown("""
            <div style='text-align: center; padding: 40px;'>
                <h2>👋 Welcome!</h2>
                <p>Select a conversation or click ➕ to start a new one</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader(f"💬 {st.session_state.thread_id}")
        
        # Load messages on thread selection
        if st.session_state.auto_refresh:
            st.session_state.messages = load_thread_messages(
                st.session_state.thread_id,
                st.session_state.user_id
            )
            st.session_state.auto_refresh = False
        
        # Display messages
        chat_container = st.container()
        with chat_container:
            if st.session_state.messages:
                for message in st.session_state.messages:
                    if message["role"] == "user":
                        st.markdown(f"""
                            <div class='user-msg'>
                                <b>You:</b> {message['content']}
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                            <div class='assistant-msg'>
                                <b>AI:</b> {message['content']}
                            </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("💬 Start the conversation\nSend a message to begin")
        
        # Message input
        st.markdown("---")
        col_input, col_send = st.columns([0.9, 0.1])
        
        with col_input:
            user_input = st.text_input("Type your message...", key="msg_input")
        
        with col_send:
            send_btn = st.button("📤", help="Send", use_container_width=True)
        
        # Process message
        if send_btn and user_input and st.session_state.thread_id:
            try:
                with st.spinner("⏳ Thinking..."):
                    payload = {
                        "messages": [{"role": "user", "content": user_input}],
                        "user_id": st.session_state.user_id,
                        "thread_id": st.session_state.thread_id
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/api/chat-context",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data.get("success"):
                            st.session_state.messages.append({
                                "role": "user",
                                "content": user_input
                            })
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": data.get("response", "No response")
                            })
                            st.rerun()
                        else:
                            st.error(f"Error: {data.get('error')}")
                    else:
                        st.error(f"API Error: {response.status_code}")
            
            except requests.exceptions.Timeout:
                st.error("❌ Request timeout")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        
        elif send_btn and not st.session_state.thread_id:
            st.warning("⚠️ Please select a conversation first!")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.8rem;'>
        🚀 Nikoo AI | Powered by Groq & MongoDB | v1.0
    </div>
""", unsafe_allow_html=True)
