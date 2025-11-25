import streamlit as st
from datetime import datetime

# -----------------------
# CONFIG
# -----------------------
st.set_page_config(
    page_title="Diabetes Risk Assistant",
    layout="wide",
)

# Dummy data
DUMMY_SESSIONS = [
    {"id": "sess_001", "title": "Tư vấn lần đo 01/11", "time": "2025-11-01 10:20"},
    {"id": "sess_002", "title": "Nhập chỉ số mới", "time": "2025-11-05 09:05"},
    {"id": "sess_003", "title": "Đọc kết quả mô hình", "time": "2025-11-10 14:30"},
]

# -----------------------
# STATE
# -----------------------
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = DUMMY_SESSIONS[0]["id"]

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Xin chào, mình là trợ lý đánh giá nguy cơ tiểu đường 👋"},
        {"role": "user", "content": "Cho mình xem lại kết quả lần gần nhất."},
    ]


# -----------------------
# SIDEBAR BÊN TRÁI
# (ẩn/hiện bằng nút > mặc định của Streamlit)
# -----------------------
with st.sidebar:
    st.markdown("## 📊 Menu")

    # Chọn Dashboard / Overview
    page = st.radio(
        "Trang",
        options=["Dashboard", "Overview"],
        index=0 if st.session_state.current_page == "Dashboard" else 1,
    )
    st.session_state.current_page = page

    st.markdown("---")
    st.markdown("## 💬 Chat sessions")

    for sess in DUMMY_SESSIONS:
        is_active = sess["id"] == st.session_state.current_session_id
        label = f"{sess['title']}  \n🕒 {sess['time']}"
        if st.button(label, key=f"sess_{sess['id']}"):
            st.session_state.current_session_id = sess["id"]
            # chỗ này sau này bạn load messages theo session
            # st.session_state.messages = load_messages(sess["id"])
            st.experimental_rerun()

    st.markdown("---")
    if st.button("➕ New chat"):
        st.session_state.current_session_id = f"sess_{len(DUMMY_SESSIONS)+1:03d}"
        st.session_state.messages = [
            {"role": "assistant", "content": "Chào bạn, mình là trợ lý đánh giá nguy cơ tiểu đường."}
        ]
        st.experimental_rerun()

# -----------------------
# MAIN AREA
# -----------------------
st.title("Diabetes Risk Assistant")

# Phần trên: Dashboard / Overview
if st.session_state.current_page == "Dashboard":
    st.subheader("Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Số lần đánh giá", "8", "+1 so với tháng trước")
    with col2:
        st.metric("Lần đánh giá gần nhất", "5 ngày trước")
    with col3:
        st.metric("Nguy cơ hiện tại", "Trung bình", "ổn định")

    st.markdown("---")
    st.write("Khu vực biểu đồ / thống kê… (sau này bạn nhúng plotly/matplotlib vào đây).")

elif st.session_state.current_page == "Overview":
    st.subheader("Overview")
    st.write("Tóm tắt các lần đo gần đây:")
    st.markdown("- 2025-11-10: Nguy cơ **trung bình**, HbA1c = 5.8")
    st.markdown("- 2025-11-01: Nguy cơ **thấp**, HbA1c = 5.6")
    st.markdown("- 2025-10-15: Nguy cơ **trung bình**, HbA1c = 5.9")
    st.markdown("---")

# Phần dưới: Chat giống ChatGPT
st.subheader("Chat")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Nhập câu hỏi hoặc yêu cầu của bạn...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    # reply demo
    reply = f"Mình đã nhận: **{user_input}** (ở đây bạn sẽ gọi model / logic thật)."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.experimental_rerun()

# -----------------------
# CSS CHO NÚT SESSION GỌN HƠN
# -----------------------
st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] button {
        width: 100%;
        text-align: left;
        white-space: pre-line;
        font-size: 0.9rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
