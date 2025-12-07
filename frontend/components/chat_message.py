"""
Chat Message Component - Gemini-like style
"""
import streamlit as st
from utils.helpers import format_datetime

def render_chat_message_gemini(sender_type, content, timestamp=""):
    """
    Render chat message in Gemini style
    
    Args:
        sender_type: 'user' or 'agent'
        content: Message text
        timestamp: ISO datetime string
    """
    if sender_type == 'user':
        st.markdown(f"""
        <div class="user-message">
            <div style="text-align: right;">
                <strong>Bạn</strong>
                {f'<span style="color: #999; font-size: 0.85rem; margin-left: 10px;">{format_datetime(timestamp)}</span>' if timestamp else ''}
            </div>
            <div style="margin-top: 0.5rem;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="agent-message">
            <div>
                <strong>🤖 AI Tư vấn</strong>
                {f'<span style="color: #999; font-size: 0.85rem; margin-left: 10px;">{format_datetime(timestamp)}</span>' if timestamp else ''}
            </div>
            <div style="margin-top: 0.5rem; line-height: 1.6;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)