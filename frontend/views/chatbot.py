"""
Chatbot View - AI conversation with streaming
"""
import streamlit as st
import time
import traceback

from services.assessment_service import get_user_assessments, get_assessment_by_id
from services.chat_service import send_message, get_messages_by_assessment
from utils.helpers import format_date, get_risk_level_info, format_risk_score
from utils.session_state import get_current_assessment_id, set_current_assessment_id

def show_chatbot(user):
    """Display chatbot interface with Gemini-like UI and streaming"""
    
    st.markdown('<h1 style="text-align: center; color: #1f77b4;">💬 Chatbot AI</h1>', unsafe_allow_html=True)
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
                            background: white;
                            border-radius: 18px;
                            padding: 1.5rem;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
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
    
    # Get full assessment
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
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <h3 style="margin: 0; color: {risk_info['color']};">
            📊 Đánh giá hiện tại: {risk_info['label']}
        </h3>
        <p style="margin: 0.5rem 0 0 0; color: #666;">
            🕐 {format_date(measured_at)} | 📊 Điểm nguy cơ: {format_risk_score(risk_score)}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load chat history
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
                    background: #f1f3f4;
                    border-radius: 18px;
                    padding: 1rem 1.5rem;
                    margin: 0.5rem 0 0.5rem auto;
                    max-width: 80%;
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
                    background: white;
                    border-radius: 18px;
                    padding: 1rem 1.5rem;
                    margin: 0.5rem 0;
                    max-width: 85%;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                ">
                    <p style="margin: 0; font-size: 0.85rem; color: #666;">
                        <strong>🤖 AI Bác sĩ</strong> • {format_date(timestamp) if timestamp else ''}
                    </p>
                    <div style="margin: 0.5rem 0 0 0; color: #202124; line-height: 1.8;">
                        {content}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
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
            background: #f1f3f4;
            border-radius: 18px;
            padding: 1rem 1.5rem;
            margin: 0.5rem 0 0.5rem auto;
            max-width: 80%;
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
            background: white;
            border-radius: 18px;
            padding: 1rem 1.5rem;
            max-width: 100px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        ">
            <div style="display: flex; gap: 5px;">
                <span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: wave 1.3s ease-in-out infinite;"></span>
                <span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: wave 1.3s ease-in-out 0.2s infinite;"></span>
                <span style="width: 8px; height: 8px; background: #667eea; border-radius: 50%; animation: wave 1.3s ease-in-out 0.4s infinite;"></span>
            </div>
        </div>
        <style>
            @keyframes wave {{
                0%, 60%, 100% {{ transform: translateY(0); }}
                30% {{ transform: translateY(-10px); }}
            }}
        </style>
        """, unsafe_allow_html=True)
        
        # Send message
        result = send_message(current_assessment_id, user_message)
        typing_placeholder.empty()
        
        if result['success']:
            st.rerun()
        else:
            st.error(f"❌ Lỗi: {result['error']}")