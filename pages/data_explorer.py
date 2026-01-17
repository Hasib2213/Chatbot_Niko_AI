"""Data Explorer for MongoDB Collections"""

import streamlit as st
import pandas as pd
from config import settings
from app.database import db_client

st.set_page_config(
    page_title="Database Explorer",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ Database Explorer")

if not db_client or not db_client.is_connected():
    st.error("❌ Database NOT connected!")
    st.stop()

st.success("✅ Connected to MongoDB Atlas")

# Tabs
tab1, tab2, tab3 = st.tabs(["📝 Messages", "🧵 Threads", "📊 Statistics"])

with tab1:
    st.subheader("Messages Collection")
    
    try:
        # Get messages
        messages = list(db_client.messages_collection.find().sort("created_at", -1).limit(100))
        
        if messages:
            # Convert to DataFrame
            messages_data = []
            for msg in messages:
                messages_data.append({
                    "Thread ID": msg.get("thread_id"),
                    "User ID": msg.get("user_id"),
                    "Role": msg.get("role"),
                    "Content": msg.get("content")[:100],  # First 100 chars
                    "Created At": msg.get("created_at"),
                })
            
            df = pd.DataFrame(messages_data)
            st.dataframe(df, use_container_width=True)
            
            st.info(f"📊 Total messages: {db_client.messages_collection.count_documents({})}")
        else:
            st.warning("⚠️ No messages in database")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

with tab2:
    st.subheader("Threads Collection")
    
    try:
        # Get threads
        threads = list(db_client.threads_collection.find().sort("updated_at", -1).limit(100))
        
        if threads:
            # Convert to DataFrame
            threads_data = []
            for thread in threads:
                threads_data.append({
                    "Thread ID": thread.get("thread_id"),
                    "User ID": thread.get("user_id"),
                    "Title": thread.get("title", ""),
                    "Message Count": thread.get("message_count"),
                    "Created At": thread.get("created_at"),
                    "Updated At": thread.get("updated_at"),
                })
            
            df = pd.DataFrame(threads_data)
            st.dataframe(df, use_container_width=True)
            
            st.info(f"📊 Total threads: {db_client.threads_collection.count_documents({})}")
        else:
            st.warning("⚠️ No threads in database")
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

with tab3:
    st.subheader("Database Statistics")
    
    try:
        message_count = db_client.messages_collection.count_documents({})
        thread_count = db_client.threads_collection.count_documents({})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("📝 Total Messages", message_count)
        
        with col2:
            st.metric("🧵 Total Threads", thread_count)
        
        st.markdown("---")
        
        # Get messages by user
        st.subheader("Messages by User")
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$user_id",
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            result = list(db_client.messages_collection.aggregate(pipeline))
            
            if result:
                df = pd.DataFrame([
                    {"User ID": r["_id"], "Message Count": r["count"]}
                    for r in result
                ])
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not aggregate: {str(e)}")
        
        st.markdown("---")
        
        # Get threads by user
        st.subheader("Threads by User")
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$user_id",
                        "count": {"$sum": 1},
                        "total_messages": {"$sum": "$message_count"}
                    }
                },
                {"$sort": {"count": -1}}
            ]
            
            result = list(db_client.threads_collection.aggregate(pipeline))
            
            if result:
                df = pd.DataFrame([
                    {
                        "User ID": r["_id"],
                        "Thread Count": r["count"],
                        "Total Messages": r["total_messages"]
                    }
                    for r in result
                ])
                st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not aggregate: {str(e)}")
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

st.markdown("---")
st.caption(f"📍 Database: {settings.DATABASE_NAME} | MongoDB Atlas")
