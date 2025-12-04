"""
Chatbot View - AI conversation with streaming
"""
import streamlit as st
import time
import traceback
import base64
import os

from services.assessment_service import get_user_assessments, get_assessment_by_id
from services.chat_service import send_message, get_messages_by_assessment
from utils.helpers import format_date, get_risk_level_info, format_risk_score
from utils.session_state import get_current_assessment_id, set_current_assessment_id

def get_base64_image(image_path):
    """Convert image to base64"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Không thể load ảnh: {e}")
        return None

def show_chatbot(user):
    """Display chatbot interface with Gemini-like UI and streaming"""
    
    # Get background image
    image_path = os.path.join(os.path.dirname(__file__), "..", "assets", "background.jpg")
    base64_image = get_base64_image(image_path)
    
    # Custom CSS for background and styling
    background_css = f"""
    <style>
    /* Background image */
    .stApp {{
        background-image: url('data:image/jpeg;base64,{base64_image}');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    
    /* Make containers transparent */
    .main {{
        background-color: transparent !important;
    }}
    
    .block-container {{
        background-color: transparent !important;
        padding-top: 2rem;
    }}
    
    [data-testid="stVerticalBlock"] {{
        background-color: transparent !important;
    }}
    
    [data-testid="stHorizontalBlock"] {{
        background-color: transparent !important;
    }}
    
    /* Add overlay for better readability */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.3);
        z-index: 0;
        pointer-events: none;
    }}
    
    .main > div {{
        position: relative;
        z-index: 1;
    }}
    
    /* Style for content */
    .element-container {{
        background-color: transparent !important;
    }}
    
    /* Chat input styling */
    .stChatInput {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-radius: 25px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
    }}
    
    /* Animation for typing indicator */
    @keyframes wave {{
        0%, 60%, 100% {{ transform: translateY(0); }}
        30% {{ transform: translateY(-10px); }}
    }}
    </style>
    """ if base64_image else ""
    
    st.markdown(background_css, unsafe_allow_html=True)
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4; text-shadow: 2px 2px 4px rgba(255,255,255,0.8);">💬 Chatbot AI</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # ✅ CHECK: If user came from assessment form with advice request
    show_advice = st.session_state.get('show_streaming', False) and st.session_state.get('prediction_result')
    
    if show_advice:
        st.info("🤖 Đang tạo lời khuyên từ AI...")
        
        prediction_result = st.session_state.prediction_result
        
        from services.api_client import api_client
        
        try:
            payload = {
                'validated_data': prediction_result['validated_data'],
                'prediction': prediction_result['prediction'],
                'risk_score': prediction_result['risk_score'],
                'user_id': user['id']
            }
            
            response = api_client.post('/get_advice', json=payload)
            result = api_client.handle_response(response)
            
            if result['success']:
                advice = result['data']['advice']
                new_assessment_id = result['data'].get('assessment_id')
                
                st.markdown("### 💬 Lời khuyên từ AI")
                
                # Stream the advice
                advice_placeholder = st.empty()
                streamed_text = ""
                
                for i, char in enumerate(advice):
                    streamed_text += char
                    
                    if i % 10 == 0 or i == len(advice) - 1:
                        advice_placeholder.markdown(f"""
                        <div style="
                            background: rgba(255, 255, 255, 0.95);
                            border-radius: 18px;
                            padding: 1.5rem;
                            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                            line-height: 1.8;
                        ">
                            {streamed_text}
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(0.01)
                
                # Update current assessment
                if new_assessment_id:
                    set_current_assessment_id(new_assessment_id)
                
                # ✅ Clear flags AFTER streaming
                del st.session_state.show_streaming
                del st.session_state.prediction_result
                if 'advice_requested' in st.session_state:
                    del st.session_state.advice_requested
                
                st.success("✅ Lời khuyên đã được lưu! Bạn có thể tiếp tục chat phía dưới.")
                st.markdown("---")
                
            else:
                st.error(f"❌ Lỗi: {result['error']}")
                return
                
        except Exception as e:
            st.error(f"❌ Lỗi: {str(e)}")
            return
    
    # ✅ Continue with normal chatbot flow
    result = get_user_assessments(user['id'], valid_only=True)
    
    if not result['success']:
        st.error(f"❌ Lỗi: {result['error']}")
        return
    
    valid_assessments = result['data']
    
    if not valid_assessments:
        st.warning("⚠️ Bạn chưa có đánh giá sức khỏe nào.")
        from utils.session_state import navigate_to
        if st.button("📝 Tạo đánh giá mới", type="primary", key="chatbot_create_assessment"):
            navigate_to("Đánh giá mới")
            st.rerun()
        return
    
    # Get current assessment
    current_assessment_id = get_current_assessment_id()
    
    if not current_assessment_id or current_assessment_id not in [a['id'] for a in valid_assessments]:
        current_assessment_id = valid_assessments[0]['id']
        set_current_assessment_id(current_assessment_id)
    
    # ✅ Assessment selector - Show list of assessments
    st.markdown("### 📋 Chọn đánh giá để xem lịch sử chat")
    
    # Create columns for assessment cards
    cols = st.columns(min(len(valid_assessments), 3))
    
    for idx, assessment in enumerate(valid_assessments):
        col_idx = idx % 3
        with cols[col_idx]:
            assessment_id = assessment['id']
            measured_at = assessment.get('measured_at', '')
            prediction = assessment.get('prediction', {})
            risk_level = prediction.get('risk_level', 'low')
            risk_info = get_risk_level_info(risk_level)
            
            # Check if this is current assessment
            is_current = assessment_id == current_assessment_id
            border_color = risk_info['color'] if is_current else "#e0e0e0"
            bg_opacity = "0.95" if is_current else "0.85"
            
            # Display as clickable card
            if st.button(
                f"{'🔹' if is_current else '⚪'} {format_date(measured_at)}\n{risk_info['label']}",
                key=f"select_assessment_{assessment_id}",
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                if not is_current:
                    set_current_assessment_id(assessment_id)
                    st.rerun()
    
    st.markdown("---")
    
    # Get full assessment for current selection
    assessment_result = get_assessment_by_id(current_assessment_id)
    if not assessment_result['success']:
        st.error("❌ Không thể tải assessment")
        return
    
    assessment = assessment_result['data']
    
    # Assessment header
    prediction_data = assessment.get('prediction', {})
    
    if isinstance(prediction_data, dict):
        risk_level = prediction_data.get('risk_level', 'low')
        risk_score = prediction_data.get('risk_score', 0)
    else:
        risk_level = 'high' if prediction_data == 1 else 'low'
        risk_score = float(prediction_data)
    
    measured_at = assessment.get('measured_at', '')
    risk_info = get_risk_level_info(risk_level)
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {risk_info['bg_color']} 0%, {risk_info['color']}22 100%);
        border-left: 5px solid {risk_info['color']};
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    ">
        <h3 style="margin: 0; color: {risk_info['color']};">
            📊 Đánh giá đang xem: {risk_info['label']}
        </h3>
        <p style="margin: 0.5rem 0 0 0; color: #666;">
            🕐 {format_date(measured_at)} | 📊 Điểm nguy cơ: {format_risk_score(risk_score)}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load chat history for selected assessment
    messages_result = get_messages_by_assessment(current_assessment_id)
    
    if messages_result['success']:
        messages = messages_result['data']
    else:
        messages = []
    
    # Display messages
    if messages:
        st.markdown("### 📜 Lịch sử trò chuyện")
        
        for msg in messages:
            sender_type = msg['sender_type']
            content = msg['content']
            timestamp = msg.get('created_at', '')
            
            if sender_type == 'user':
                st.markdown(f"""
                <div style="
                    background: rgba(241, 243, 244, 0.95);
                    border-radius: 18px;
                    padding: 1rem 1.5rem;
                    margin: 0.5rem 0 0.5rem auto;
                    max-width: 80%;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                ">
                    <p style="margin: 0; font-size: 0.85rem; color: #666; text-align: right;">
                        <strong>Bạn</strong> • {format_date(timestamp) if timestamp else ''}
                    </p>
                    <p style="margin: 0.5rem 0 0 0; color: #202124;">
                        {content}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 18px;
                    padding: 1rem 1.5rem;
                    margin: 0.5rem 0;
                    max-width: 85%;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.12);
                ">
                    <p style="margin: 0; font-size: 0.85rem; color: #666;">
                        <strong>🤖 AI Bác sĩ</strong> • {format_date(timestamp) if timestamp else ''}
                    </p>
                    <div style="margin: 0.5rem 0 0 0; color: #202124; line-height: 1.8;">
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("💬 Chưa có cuộc trò chuyện nào cho đánh giá này. Hãy bắt đầu chat phía dưới!")
    
    # Chat input
    st.markdown("---")
    st.markdown("### 💭 Hỏi đáp với AI")
    
    if 'chat_input_key' not in st.session_state:
        st.session_state.chat_input_key = 0
    
    user_message = st.chat_input(
        "Nhập câu hỏi của bạn...",
        key=f"chat_input_{st.session_state.chat_input_key}"
    )
    
    if user_message:
        st.session_state.chat_input_key += 1
        
        # Show user message
        st.markdown(f"""
        <div style="
            background: rgba(241, 243, 244, 0.95);
            border-radius: 18px;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0 0.5rem auto;
            max-width: 80%;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
        ">
            <p style="margin: 0; color: #202124;">
                {user_message}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show typing
        typing_placeholder = st.empty()
        typing_placeholder.markdown("""
        <div style="
            background: rgba(255, 255, 255, 0.95);
            border-radius: 18px;
            padding: 1rem 1.5rem;
            max-width: 100px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.12);
        ">
            <div style="display: flex; gap: 5px;">
                <span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: wave 1.3s ease-in-out infinite;"></span>
                <span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: wave 1.3s ease-in-out 0.2s infinite;"></span>
                <span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: wave 1.3s ease-in-out 0.4s infinite;"></span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Send message
        result = send_message(current_assessment_id, user_message)
        typing_placeholder.empty()
        
        if result['success']:
            st.rerun()
        else:
            st.error(f"❌ Lỗi: {result['error']}")