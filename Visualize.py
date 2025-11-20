import streamlit as st
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import base64

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from matplotlib.ticker import PercentFormatter

st.set_page_config(
    page_title="Phân tích dữ liệu tiểu đường",
    layout="wide",
)

def get_base64_of_image(img_path: str) -> str:
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()
    
IMAGE_PATH = "./background.jpg"

# Đọc ảnh và mã hóa base64
img_base64 = get_base64_of_image(IMAGE_PATH)

st.markdown(
    f"""
    <style>
    /* Sidebar gradient trắng sang xanh dương nhạt */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #ffffff, #63d1f2);
        color: black;
    }}
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span {{
        color: black !important;
    }}
    [data-testid="stSidebar"] .stRadio > label {{
        font-weight: 600;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1rem;
    }}

    /* Ảnh nền cho toàn bộ vùng app chính */
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpeg;base64,{img_base64}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}

    /* Xóa nền trắng mặc định của phần main và block bên trong */
    [data-testid="stAppViewContainer"] .main {{
        background: transparent !important;
    }}

    .block-container {{
        background: transparent !important;
    }}

    /* Header trong suốt để không che ảnh nền */
    [data-testid="stHeader"] {{
        background: transparent;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

st.title("☁️DJAT CLOUD: TRÍ TUỆ NHÂN TẠO VỀ SỨC KHỎE BỆNH TIỂU ĐƯỜNG")



# 1. Chọn file dữ liệu
st.subheader("Hãy chọn file dữ liệu")
st.markdown("**Chọn hoặc kéo thả file dữ liệu dạng csv vào ô bên dưới giúp mình nhé**")
st.markdown("**⚠️Lưu ý⚠️: File dữ liệu phải có cột `Diabetes` được mã hóa nhị phân (giá trị 0 và 1).**")

uploaded_file = st.file_uploader(
    label="",
    type=["csv"]
)

# Nếu chưa chọn file thì dừng tại đây
if uploaded_file is None:
    st.info("Hãy chọn một file dữ liệu csv để tiếp tục")
    st.stop()

# Đọc dữ liệu từ file người dùng đã chọn
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Lỗi khi đọc file dữ liệu csv. Chi tiết lỗi: {e}")
    st.stop()

# Xác định cột mục tiêu và các cột số
target_col = "Diabetes"
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

if target_col not in numeric_cols:
    st.error("Cột Diabetes cần ở dạng số, ví dụ 0 và 1")
    st.stop()


st.sidebar.title("📚MENU")
mode = st.sidebar.radio(
    "Chọn nội dung bạn quan tâm",
    ("Tổng quan về dữ liệu", "AI tư vấn sức khỏe về tiểu đường")
)

# =========================
# MỤC 1: TỔNG QUAN VỀ DỮ LIỆU
# =========================
if mode == "Tổng quan về dữ liệu":
    # Thông tin dữ liệu
    st.subheader("Tổng quan dữ liệu đã nhập")
    n_rows, n_cols = df.shape
    st.write(f"Dữ liệu đưa vào gồm {n_rows} dòng và {n_cols} cột")
    st.dataframe(df.head())

    # 2. Thống kê mô tả
    st.subheader("Thống kê mô tả")
    st.write(df.describe(include="all"))

    # 3. Ma trận tương quan với biến mục tiêu
    st.subheader("3. Ma trận tương quan giữa các feature và Diabetes")
    corr = df[numeric_cols].corr()
    cols = [target_col] + [c for c in corr.columns if c != target_col]
    corr = corr.loc[cols, cols]

    fig_corr, ax_corr = plt.subplots(
        figsize=(1.0 * len(cols) + 2, 1.0 * len(cols) + 2)
    )

    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        vmin=-1,
        vmax=1,
        cmap="coolwarm",
        square=True,
        cbar=True,
        ax=ax_corr
    )

    ax_corr.set_title("Biểu đồ nhiệt ma trận tương quan các feature và Diabetes")
    ax_corr.set_xlabel("Feature")
    ax_corr.set_ylabel("Feature")
    st.pyplot(fig_corr)

    # Thanh lựa chọn số feature có độ tương quan lớn nhất với Diabetes
    st.subheader("Chọn các feature có tương quan cao với Diabetes")
    target_corr = corr[target_col].drop(target_col)
    abs_target_corr = target_corr.abs().sort_values(ascending=False)
    max_features = len(abs_target_corr)

    top_n = st.slider(
        "Chọn số feature có độ tương quan tuyệt đối lớn nhất với Diabetes",
        min_value=1,
        max_value=max_features,
        value=min(5, max_features)
    )

    top_feature_names = abs_target_corr.index[:top_n]
    top_features_signed = target_corr.loc[top_feature_names]

    result_df = pd.DataFrame({
        "Thuộc tính": top_features_signed.index,
        "Độ tương quan": top_features_signed.values
    })

    st.write("Các feature được chọn theo độ tương quan với bệnh tiểu đường")
    st.dataframe(result_df)

    # 4. Biểu đồ đường cho Diabetes theo độ tuổi và giới tính
    st.subheader("Biểu đồ đường cho tỉ lệ mắc bệnh tiểu đường theo độ tuổi và giới tính")

    required_cols = {"Diabetes", "Age", "Sex"}
    if not required_cols.issubset(df.columns):
        missing = required_cols.difference(df.columns)
        st.error(f"Thiếu các cột cần thiết cho biểu đồ: {missing}")
    else:
        sex_map = {0: "Nữ", 1: "Nam"}
        df["SexLabel"] = df["Sex"].map(sex_map)
        agg = (
            df.groupby(["Age", "SexLabel"])["Diabetes"]
            .mean()
            .reset_index()
            .rename(columns={"Diabetes": "Diabetes_rate"})
        )

        agg["Diabetes_percent"] = agg["Diabetes_rate"] * 100
        agg = agg.sort_values("Age")
        agg["Age"] = agg["Age"] * 5

        pivot_df = agg.pivot(index="Age", columns="SexLabel", values="Diabetes_percent")

        fig_line, ax_line = plt.subplots(figsize=(7, 3))

        for sex_value in pivot_df.columns:
            ax_line.plot(
                pivot_df.index,
                pivot_df[sex_value],
                marker="o",
                label=f"Giới tính {sex_value}"
            )

        ax_line.set_xlabel("Độ tuổi")
        ax_line.set_ylabel("Tỉ lệ mắc bệnh tiểu đường (%)")
        ax_line.set_title("Tỉ lệ mắc bệnh tiểu đường theo độ tuổi và giới tính")

        ax_line.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax_line.grid(True)
        ax_line.legend(title="Giới tính")

        st.pyplot(fig_line)

    # 5. Biểu đồ mối quan hệ giữa Diabetes theo thuộc tính khác và giới tính
    st.subheader("Biểu đồ mối quan hệ giữa bệnh tiểu đường theo các giá trị khác và giới tính")

    required_cols = {"Diabetes", "Sex"}
    if not required_cols.issubset(df.columns):
        missing = required_cols.difference(df.columns)
        st.error(f"Thiếu các cột cần thiết cho biểu đồ: {missing}")
    else:
        sex_map = {0: "Nữ", 1: "Nam"}
        df["SexLabel"] = df["Sex"].map(sex_map)

        def is_binary_feature(series):
            vals = series.dropna().unique()
            if len(vals) == 0:
                return False
            return len(vals) <= 2 and set(vals).issubset({0, 1})

        feature_candidates = []
        for col in numeric_cols:
            if col in ["Diabetes", "Sex"]:
                continue
            if is_binary_feature(df[col]):
                continue
            feature_candidates.append(col)

        if len(feature_candidates) == 0:
            st.warning("Không còn thuộc tính số nào phù hợp để vẽ")
        else:
            selected_feature = st.selectbox(
                "Chọn một thuộc tính để vẽ cùng Diabetes",
                feature_candidates
            )

            agg = (
                df.groupby([selected_feature, "SexLabel"])["Diabetes"]
                .mean()
                .reset_index()
                .rename(columns={"Diabetes": "Diabetes_rate"})
            )

            if agg.empty:
                st.warning("Không có dữ liệu phù hợp để vẽ biểu đồ")
            else:
                agg["Diabetes_percent"] = agg["Diabetes_rate"] * 100
                agg = agg.sort_values(selected_feature)
                pivot_df = agg.pivot(
                    index=selected_feature,
                    columns="SexLabel",
                    values="Diabetes_percent"
                )

                fig_line, ax_line = plt.subplots(figsize=(7, 3))

                for sex_value in pivot_df.columns:
                    ax_line.plot(
                        pivot_df.index,
                        pivot_df[sex_value],
                        marker="o",
                        label=f"Giới tính {sex_value}"
                    )

                ax_line.set_xlabel(f"Giá trị thuộc tính {selected_feature}")
                ax_line.set_ylabel("Tỉ lệ mắc bệnh tiểu đường (%)")
                ax_line.set_title(
                    f"Tỉ lệ mắc bệnh tiểu đường theo {selected_feature} và giới tính"
                )

                ax_line.yaxis.set_major_formatter(PercentFormatter(xmax=100))
                ax_line.grid(True)
                ax_line.legend(title="Giới tính")

                st.pyplot(fig_line)

# =========================
# MỤC 2: AI TƯ VẤN SỨC KHỎE
# =========================
elif mode == "AI tư vấn sức khỏe về tiểu đường":
    st.subheader("AI tư vấn sức khỏe về tiểu đường")
    st.write("Phần này đang chờ bạn phát triển thêm chức năng sử dụng mô hình AI.")
