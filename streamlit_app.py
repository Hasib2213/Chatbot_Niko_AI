import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Nikoo AI Chat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URL
API_BASE_URL = "http://localhost:8000"

# Streamlit session state initialization
if "user_id" not in st.session_state:
    st.session_state.user_id = ""
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
if "threads" not in st.session_state:
    st.session_state.threads = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_thread" not in st.session_state:
    st.session_state.current_thread = None

# Header
st.title("💬 Nikoo AI Assistant")
st.markdown("---")

# Sidebar for user management
with st.sidebar:
    st.header("👤 User Settings")
    
    # User ID input
    user_id = st.text_input(
        "Enter User ID:",
        value=st.session_state.user_id,
        placeholder="e.g., user_123"
    )
    
    if user_id:
        st.session_state.user_id = user_id
    
    if st.session_state.user_id:
        st.success(f"✅ Logged in as: {st.session_state.user_id}")
        
        st.markdown("---")
        st.header("📚 Threads")
        
        # Load threads button
        if st.button("🔄 Load Threads", use_container_width=True):
            try:
                response = requests.get(f"{API_BASE_URL}/api/threads/{st.session_state.user_id}")
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.threads = data.get("threads", [])
                    st.success(f"✅ Loaded {len(st.session_state.threads)} threads")
                else:
                    st.error("Failed to load threads")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Display threads
        if st.session_state.threads:
            st.subheader(f"Your Threads ({len(st.session_state.threads)})")
            
            for thread in st.session_state.threads:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    # Thread title
                    thread_title = thread.get("title", "Untitled")[:50]
                    if st.button(
                        f"💬 {thread_title}",
                        key=f"thread_{thread['thread_id']}",
                        use_container_width=True
                    ):
                        st.session_state.thread_id = thread["thread_id"]
                        st.session_state.current_thread = thread
                        st.rerun()
                
                with col2:
                    # Message count
                    st.caption(f"📊 {thread.get('message_count', 0)} msgs")
                
                with col3:
                    # Delete button
                    if st.button(
                        "🗑️",
                        key=f"delete_{thread['thread_id']}",
                        help="Delete thread"
                    ):
                        try:
                            response = requests.delete(
                                f"{API_BASE_URL}/api/threads/{thread['thread_id']}/{st.session_state.user_id}"
                            )
                            if response.status_code == 200:
                                st.success("✅ Thread deleted")
                                st.session_state.threads = [
                                    t for t in st.session_state.threads 
                                    if t["thread_id"] != thread["thread_id"]
                                ]
                                if st.session_state.thread_id == thread["thread_id"]:
                                    st.session_state.thread_id = None
                                    st.session_state.current_thread = None
                                st.rerun()
                            else:
                                st.error("Failed to delete thread")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            st.markdown("---")
        
        # New chat button
        if st.button("➕ New Chat", use_container_width=True, key="new_chat_btn"):
            st.session_state.thread_id = "new_chat"  # Mark as new chat
            st.session_state.current_thread = None
            st.session_state.messages = []
            st.rerun()
    
    else:
        st.warning("⚠️ Please enter a User ID to continue")

# Main content area
if st.session_state.user_id:
    # New Chat Mode
    if st.session_state.thread_id == "new_chat":
        st.header("✨ Start New Conversation")
        st.info("👈 Type your message below to begin a new chat")
        
        st.markdown("---")
        st.subheader("💬 Your Message")
        
        user_message = st.text_area("Type here...", height=120, key="new_message_input")
        
        if st.button("Send", use_container_width=True, key="send_new_chat"):
            if user_message.strip():
                try:
                    # Prepare request to /api/chat (creates new thread)
                    payload = {
                        "messages": [
                            {"role": "user", "content": user_message}
                        ],
                        "user_id": st.session_state.user_id
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/api/chat",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        new_thread_id = data.get("thread_id")
                        
                        st.success("✅ Chat created successfully!")
                        st.info(f"🤖 **Assistant**: {data.get('response', '')}")
                        
                        # Create thread object to display in UI
                        new_thread = {
                            "thread_id": new_thread_id,
                            "user_id": st.session_state.user_id,
                            "title": data.get("response", "New Chat")[:50],
                            "message_count": 2,  # 1 user + 1 assistant
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                        
                        # Store thread info - switch to thread mode for continuous chatting
                        st.session_state.thread_id = new_thread_id
                        st.session_state.current_thread = new_thread
                        st.session_state.messages = [
                            {"role": "user", "content": data.get("user_message", "")},
                            {"role": "assistant", "content": data.get('response', '')}
                        ]
                        
                        st.info("💬 Now you can send more messages to continue the conversation!")
                        st.rerun()
                    else:
                        error_detail = response.json().get('detail', 'Unknown error') if response.text else 'Connection error'
                        st.error(f"❌ Error: {error_detail}")
                
                except Exception as e:
                    st.error(f"❌ Error creating chat: {str(e)}")
            else:
                st.warning("⚠️ Please enter a message")
    
    elif st.session_state.current_thread:
        # Show current thread info
        thread = st.session_state.current_thread
        st.subheader(f"📖 {thread.get('title', 'Chat')}")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Messages", thread.get("message_count", 0))
        with col2:
            created = thread.get("created_at", "N/A")
            st.metric("Created", created[:10] if created else "N/A")
        with col3:
            updated = thread.get("updated_at", "N/A")
            st.metric("Updated", updated[:10] if updated else "N/A")
        with col4:
            st.metric("Thread ID", thread.get("thread_id", "N/A")[:8] + "...")
        
        st.markdown("---")
        
        # Load and display messages
        if st.button("📥 Load Messages"):
            try:
                response = requests.get(
                    f"{API_BASE_URL}/api/threads/{thread['thread_id']}/{st.session_state.user_id}/messages"
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.messages = data.get("messages", [])
                    st.success(f"✅ Loaded {len(st.session_state.messages)} messages")
                else:
                    st.error("Failed to load messages")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Display messages
        if st.session_state.messages:
            st.subheader("💬 Messages")
            for i, msg in enumerate(st.session_state.messages):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                if role == "user":
                    st.info(f"👤 **User**: {content}")
                elif role == "assistant":
                    st.success(f"🤖 **Assistant**: {content}")
                else:
                    st.write(f"**{role}**: {content}")
        
        st.markdown("---")
        
        # New message input
        st.subheader("✍️ Send Message")
        user_message = st.text_area("Your message:", height=100)
        
        if st.button("Send", use_container_width=True):
            if user_message.strip():
                try:
                    # Prepare request
                    payload = {
                        "messages": [
                            {"role": "user", "content": user_message}
                        ]
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/api/threads/{thread['thread_id']}/{st.session_state.user_id}/messages",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success("✅ Message sent!")
                        
                        # Display AI response
                        if "response" in data:
                            st.info(f"🤖 **Assistant**: {data['response']}")
                        
                        # Show summary if available
                        if data.get("summary"):
                            with st.expander("📝 Thread Summary"):
                                st.write(data["summary"])
                        
                        # Reload messages
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error sending message: {str(e)}")
            else:
                st.warning("Please enter a message")
    
    elif st.session_state.threads:
        # No thread selected
        st.info("👈 Select a thread from the sidebar to view messages")
    
    else:
        # No threads available
        st.info("📭 No threads yet. Click 'Load Threads' or 'New Chat' to get started!")
        
        st.markdown("---")
        st.subheader("➕ Start New Chat")
        
        user_message = st.text_area("Your message:", height=100, key="first_message")
        
        if st.button("Send", use_container_width=True, key="first_send"):
            if user_message.strip():
                try:
                    # Prepare request
                    payload = {
                        "messages": [
                            {"role": "user", "content": user_message}
                        ],
                        "user_id": st.session_state.user_id
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/api/chat",
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        new_thread_id = data.get("thread_id")
                        
                        st.success("✅ New chat created!")
                        st.info(f"🤖 **Assistant**: {data.get('response', '')}")
                        
                        # Store thread info
                        st.session_state.thread_id = new_thread_id
                        
                        # Reload threads
                        st.rerun()
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"Error creating chat: {str(e)}")
            else:
                st.warning("Please enter a message")

else:
    st.warning("⚠️ Please enter a User ID in the sidebar to continue")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <small>Nikoo AI Assistant • Powered by Groq API</small>
</div>
""", unsafe_allow_html=True)
