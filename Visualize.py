import streamlit as st
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import base64
import matplotlib.patches as mpatches

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
data_path = "./Data/merged_diabetes_dataset.csv"

st.info(f"Đang đọc dữ liệu từ: `{data_path}`")

try:
    df = pd.read_csv(data_path)
except FileNotFoundError:
    st.error(
        f"Không tìm thấy file tại đường dẫn: {data_path}\n"
        "Hãy kiểm tra lại xem file đã tồn tại ở đúng vị trí chưa."
    )
    st.stop()
except Exception as e:
    st.error(f"Lỗi khi đọc file dữ liệu csv. Chi tiết lỗi: {e}")
    st.stop()

numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# Xác định cột mục tiêu và các cột số
target_col = "Diabetes"

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
    df["Age"] = df["Age"] * 5
    st.subheader("Tổng quan dữ liệu đã nhập")
    n_rows, n_cols = df.shape
    st.write(f"Dữ liệu đưa vào gồm {n_rows} dòng và {n_cols} cột")
    st.dataframe(df.head())

    # 2. Thống kê mô tả
    st.subheader("Thống kê mô tả")
    st.write(df.describe(include="all"))
    
    # Histogram cho các thuộc tính dạng số
    st.subheader("Phân phối các thuộc tính dạng số")

    numeric_plot_cols = [c for c in numeric_cols if c != target_col]
    
    numeric_plot_cols = [col for col in numeric_plot_cols if df[col].nunique() > 2]

    if len(numeric_plot_cols) == 0:
        st.warning("Không có thuộc tính dạng số nào ngoài cột Diabetes.")
    else:
        num_plots = len(numeric_plot_cols)
        num_cols = 2 
        num_rows = (num_plots // num_cols) + (num_plots % num_cols > 0)  

        for row in range(num_rows):
            cols_hist = st.columns(num_cols)
        
            for i, col in enumerate(numeric_plot_cols[row * num_cols:(row + 1) * num_cols]):
                with cols_hist[i]:
                    fig_hist, ax_hist = plt.subplots(figsize=(3, 2), facecolor="none")
                    fig_hist.patch.set_alpha(0.0)
                    ax_hist.set_facecolor("none")

                    sns.histplot(
                    df[col].dropna(),
                    bins=30,
                    kde=False,
                    ax=ax_hist,
                    color="#ff6b6b"
                    )

                    ax_hist.set_title(col, fontsize=9)
                    ax_hist.set_xlabel("")
                    ax_hist.set_ylabel("Tần số", fontsize=8)
                    ax_hist.grid(True, alpha=0.3)

                    for spine in ax_hist.spines.values():
                        spine.set_visible(False)

                    st.pyplot(fig_hist, use_container_width=False)

    # Pie chart cho các thuộc tính phân loại
    st.subheader("Biểu đồ tròn cho các thuộc tính phân loại")
    categorical_cols = [c for c in df.columns if c not in numeric_plot_cols]

    if len(categorical_cols) == 0:
        st.warning("Không có thuộc tính phân loại nào trong dữ liệu.")
    else:
        base_colors = ["#ff6b6b", "#1f9a00"]  

        def plot_cat_pie(ax, col_name):
            value_counts = df[col_name].value_counts(dropna=False)
            if value_counts.empty:
                ax.text(0.5, 0.5, "Không có dữ liệu",
                        ha="center", va="center", fontsize=7)
                ax.axis("off")
                return

            sizes = value_counts.values

        # Nếu đúng 2 nhóm dùng 2 màu cố định, nếu nhiều hơn thì lặp lại cho đủ
            if len(sizes) <= 2:
                colors_to_use = base_colors[:len(sizes)]
            else:
                colors_to_use = (base_colors * ((len(sizes) + 1) // 2))[:len(sizes)]

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=None,               # không hiện nhãn loại
                startangle=90,
                autopct="%1.1f%%",         # hiện phần trăm
                pctdistance=1.20,          # đẩy số ra ngoài lát
                colors=colors_to_use,
                wedgeprops={"edgecolor": "black"},
                textprops={"fontsize": 7}
            )

            for t in autotexts:
                t.set_ha("center")
                t.set_va("center")

            ax.axis("equal")
            ax.set_title(col_name, fontsize=9, y=1.10)

    # Vẽ từng hàng, mỗi figure chứa tối đa 2 pie chart nên bán kính bằng nhau
        for i in range(0, len(categorical_cols), 2):
            cols_pair = categorical_cols[i:i + 2]
            n = len(cols_pair)

            fig, axes = plt.subplots(
                1,
                n,
                figsize=(3.0 * n, 2.4),   # figure nhỏ, mỗi pie cùng kích thước
                dpi=200,
                facecolor="none"
            )
            fig.patch.set_alpha(0.0)

            if n == 1:
                axes = [axes]

            for ax, col_name in zip(axes, cols_pair):
                ax.set_facecolor("none")
                plot_cat_pie(ax, col_name)

            fig.subplots_adjust(
                left=0.05,
                right=0.95,
                top=0.85,
                bottom=0.10,
                wspace=0.4
            )

            st.pyplot(fig, use_container_width=False)
            plt.close(fig)

    # Legend chung bên dưới
        labels_legend = ["Có tiểu đường", "Không tiểu đường"]
        colors = ["#ff6b6b", "#1f9a00"]

        handles = [
            mpatches.Patch(color=c, label=l)
            for c, l in zip(colors, labels_legend)
        ]

        fig_leg, ax_leg = plt.subplots(figsize=(2.0, 0.5), dpi=180, facecolor="none")
        fig_leg.patch.set_alpha(0.0)
        ax_leg.axis("off")
        ax_leg.legend(
            handles=handles,
            loc="center",
            ncol=2,
            frameon=False,
            fontsize=8
        )
        fig_leg.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

        st.pyplot(fig_leg, use_container_width=False)
        plt.close(fig_leg)

    # 3. Ma trận tương quan với biến mục tiêu
    st.subheader("Ma trận tương quan giữa các feature và Diabetes")
    corr = df[numeric_cols].corr()
    cols = [target_col] + [c for c in corr.columns if c != target_col]
    corr = corr.loc[cols, cols]

    fig_corr, ax_corr = plt.subplots(
        figsize=(1.0 * len(cols) + 2, 1.0 * len(cols) + 2),
        facecolor="none",
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
    
    for spine in ax_corr.spines.values():
        spine.set_visible(False)
    
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
    
    # 6. Biểu đồ tròn tỉ lệ mắc bệnh tiểu đường theo giới tính
    st.subheader("Biểu đồ tròn tỉ lệ mắc bệnh tiểu đường theo giới tính")

    required_cols = {"Diabetes", "Sex"}
    if not required_cols.issubset(df.columns):
        missing = required_cols.difference(df.columns)
        st.error(f"Thiếu các cột cần thiết cho biểu đồ: {missing}")
    else:
        sex_map = {0: "Nữ", 1: "Nam"}
        df["SexLabel"] = df["Sex"].map(sex_map)

    counts = (
        df.groupby(["SexLabel", "Diabetes"])
        .size()
        .reset_index(name="Count")
    )

    labels_legend = ["Có tiểu đường", "Không tiểu đường"]
    colors = ["#ff6b6b", "#1f9a00"]  # đỏ cam, xanh ngọc

    def get_sizes_for_sex(sex_label):
        data_sex = counts[counts["SexLabel"] == sex_label]
        if data_sex.empty:
            return None
        sizes = []
        for d in [1, 0]:
            val = data_sex.loc[data_sex["Diabetes"] == d, "Count"]
            sizes.append(int(val.iloc[0]) if not val.empty else 0)
        return sizes

    # Tạo figure nhỏ, dpi cao để nhìn nét
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(3.0, 1.5),   # rất nhỏ
        dpi=300,
        facecolor="none"
    )
    fig.patch.set_alpha(0.0)

    for ax in axes:
        ax.set_facecolor("none")

    # Nam bên trái
    sizes_male = get_sizes_for_sex("Nam")
    if sizes_male is not None:
        axes[0].pie(
            sizes_male,
            labels=None,
            startangle=90,
            colors=colors,
            autopct="%1.1f%%",
            pctdistance=0.7,
            textprops={"fontsize": 7}
        )
        axes[0].axis("equal")
        axes[0].set_title("Nam", fontsize=9, pad=1)
    else:
        axes[0].text(0.5, 0.5, "Không có dữ liệu",
                     ha="center", va="center", fontsize=7)
        axes[0].axis("off")

    # Nữ bên phải
    sizes_female = get_sizes_for_sex("Nữ")
    if sizes_female is not None:
        axes[1].pie(
            sizes_female,
            labels=None,
            startangle=90,
            colors=colors,
            autopct="%1.1f%%",
            pctdistance=0.7,
            textprops={"fontsize": 7}
        )
        axes[1].axis("equal")
        axes[1].set_title("Nữ", fontsize=9, pad=1)
    else:
        axes[1].text(0.5, 0.5, "Không có dữ liệu",
                     ha="center", va="center", fontsize=7)
        axes[1].axis("off")

    # Siết khoảng trắng
    fig.subplots_adjust(
        left=0.02,
        right=0.98,
        top=0.88,
        bottom=0.05,
        wspace=0.3
    )

    # Vẽ figure mà không cho kéo full chiều ngang
    st.pyplot(fig, use_container_width=False)

    handles = [
        mpatches.Patch(color=c, label=l)
        for c, l in zip(colors, labels_legend)
    ]

    fig_leg, ax_leg = plt.subplots(figsize=(2.2, 0.5), dpi=300, facecolor="none")
    fig_leg.patch.set_alpha(0.0)
    ax_leg.axis("off")
    ax_leg.legend(
        handles=handles,
        loc="center",
        ncol=2,
        frameon=False,
        fontsize=8
    )
    fig_leg.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)

    st.pyplot(fig_leg, use_container_width=False)

    
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

        pivot_df = agg.pivot(index="Age", columns="SexLabel", values="Diabetes_percent")

        fig_line, ax_line = plt.subplots(figsize=(7, 3), facecolor="none")
        fig_line.patch.set_alpha(0.0)
        ax_line.set_facecolor("none")

        color_map = {
            "Nam": "#ff6b6b",   # đỏ cam
            "Nữ": "#f9c74f",    # vàng
        }

        for sex_value in pivot_df.columns:
            ax_line.plot(
                pivot_df.index,
                pivot_df[sex_value],
                marker="o",
                label=f"Giới tính {sex_value}",
                color=color_map.get(sex_value, "#ffffff")
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

                fig_line, ax_line = plt.subplots(figsize=(7, 3), facecolor="none")
                fig_line.patch.set_alpha(0.0)
                ax_line.set_facecolor("none")

                color_map = {
                    "Nam": "#ff6b6b",
                    "Nữ": "#f9c74f",
                }

                for sex_value in pivot_df.columns:
                    ax_line.plot(
                        pivot_df.index,
                        pivot_df[sex_value],
                        marker="o",
                        label=f"Giới tính {sex_value}",
                        color=color_map.get(sex_value, "#ffffff")
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
