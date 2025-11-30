"""
Risk Result Dialog Component
"""
import streamlit as st
from utils.helpers import get_risk_level_info, format_risk_score

def show_risk_result_dialog(prediction_result):
    """
    Display risk assessment result in a dialog-style UI
    
    Args:
        prediction_result: Dict containing prediction data
    
    Returns:
        None (uses session state instead)
    """
    
    # Extract data
    risk_level = prediction_result.get('risk_level', 'low')
    risk_score = prediction_result.get('risk_score', 0)
    prediction = prediction_result.get('prediction', 0)
    
    # Get styling info
    risk_info = get_risk_level_info(risk_level)
    
    # Display result card
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {risk_info['bg_color']} 0%, {risk_info['color']}22 100%);
        border-radius: 20px;
        padding: 2.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        text-align: center;
        margin: 2rem 0;
        animation: slideIn 0.5s ease-out;
    ">
        <div style="font-size: 4rem; margin-bottom: 1rem;">
            {risk_info['icon']}
        </div>
        <div style="
            font-size: 2rem;
            font-weight: bold;
            color: {risk_info['color']};
            margin-bottom: 1rem;
        ">
            {risk_info['label']}
        </div>
        <div style="
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 1.5rem;
        ">
            Điểm nguy cơ: <strong>{format_risk_score(risk_score)}</strong>
        </div>
        <div style="
            font-size: 1rem;
            color: #555;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
        ">
            {risk_info['description']}
        </div>
    </div>
    
    <style>
        @keyframes slideIn {{
            from {{
                opacity: 0;
                transform: translateY(-20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # ✅ FIX: Button sets session state directly
        if st.button(
            "💡 Nhận lời khuyên từ AI",
            type="primary",
            use_container_width=True,
            key="get_advice_button"
        ):
            # ✅ Set flags in session state
            st.session_state.advice_requested = True
            st.session_state.show_streaming = True
            st.session_state.current_page = "Chatbot AI"
            st.rerun()