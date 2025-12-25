import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
import base64
import os
from matplotlib.ticker import PercentFormatter

# Fragment decorator
try:
    fragment = st.fragment  # Streamlit >= 1.33
except AttributeError:
    fragment = st.experimental_fragment

# ============================================================
# HELPER FUNCTION - BASE64 IMAGE & COLUMN LABELS
# ============================================================

def get_base64_of_image(img_path: str) -> str:
    """Convert image to base64"""
    try:
        with open(img_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return ""

# ✅ Mapping tên cột sang tiếng Việt dễ hiểu
COLUMN_LABELS = {
    'HighBP': 'Huyết áp cao',
    'HighChol': 'Cholesterol cao',
    'CholCheck': 'Đã kiểm tra cholesterol',
    'Smoker': 'Hút thuốc',
    'Stroke': 'Đột quỵ',
    'HeartDiseaseorAttack': 'Bệnh tim mạch',
    'PhysActivity': 'Hoạt động thể chất',
    'HvyAlcoholConsump': 'Uống nhiều rượu',
    'AnyHealthcare': 'Có bảo hiểm y tế',
    'NoDocbcCost': 'Không đủ tiền khám bệnh',
    'DiffWalk': 'Khó khăn khi đi bộ',
    'Sex': 'Giới tính',
    'GenHlth': 'Sức khỏe tổng quát',
    'Education': 'Trình độ học vấn',
    'Income': 'Thu nhập',
    'Age': 'Độ tuổi',
    'BMI': 'Chỉ số BMI',
    'MentHlth': 'Sức khỏe tâm thần',
    'PhysHlth': 'Sức khỏe thể chất',
    'Diabetes': 'Tiểu đường'
}

# ✅ Mapping nhãn cho từng cột cụ thể
COLUMN_VALUE_LABELS = {
    'Sex': {0: 'Nữ', 1: 'Nam'},
    'HighBP': {0: 'Không', 1: 'Có'},
    'HighChol': {0: 'Không', 1: 'Có'},
    'CholCheck': {0: 'Chưa kiểm tra', 1: 'Đã kiểm tra'},
    'Smoker': {0: 'Không', 1: 'Có'},
    'Stroke': {0: 'Không', 1: 'Có'},
    'HeartDiseaseorAttack': {0: 'Không', 1: 'Có'},
    'PhysActivity': {0: 'Không', 1: 'Có'},
    'HvyAlcoholConsump': {0: 'Không', 1: 'Có'},
    'AnyHealthcare': {0: 'Không', 1: 'Có'},
    'NoDocbcCost': {0: 'Không', 1: 'Có'},
    'DiffWalk': {0: 'Không', 1: 'Có'},
    'GenHlth': {1: 'Xuất sắc', 2: 'Rất tốt', 3: 'Khá tốt', 4: 'Trung bình', 5: 'Kém'},
    'Education': {
        1: 'Chưa tốt nghiệp phổ thông',
        2: 'Tốt nghiệp tiểu học',
        3: 'Tốt nghiệp THCS',
        4: 'Tốt nghiệp THPT',
        5: 'Cao đẳng/ĐH (chưa TN)',
        6: 'Cao đẳng/ĐH (đã TN)'
    },
    'Income': {
        1: '< 10 triệu/năm',
        2: '10-15 triệu/năm',
        3: '15-20 triệu/năm',
        4: '20-25 triệu/năm',
        5: '25-35 triệu/năm',
        6: '35-50 triệu/năm',
        7: '50-75 triệu/năm',
        8: '> 75 triệu/năm'
    },
    'Age': {
        1: '18-24', 2: '25-29', 3: '30-34', 4: '35-39', 5: '40-44',
        6: '45-49', 7: '50-54', 8: '55-59', 9: '60-64', 10: '65-69',
        11: '70-74', 12: '75-79', 13: '80+'
    }
}

def get_column_label(col_name: str) -> str:
    """Lấy tên tiếng Việt của cột"""
    return COLUMN_LABELS.get(col_name, col_name)

def get_value_label(col_name: str, value) -> str:
    """Lấy nhãn tiếng Việt cho giá trị"""
    if col_name in COLUMN_VALUE_LABELS:
        return COLUMN_VALUE_LABELS[col_name].get(value, str(value))
    return str(value)

# ============================================================
# CACHE FUNCTIONS
# ============================================================

@st.cache_data
def describe_df(df: pd.DataFrame):
    return df.describe(include="all")


@st.cache_data
def compute_corr(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    return df[numeric_cols].corr()


@st.cache_data
def agg_sex_diabetes(df: pd.DataFrame):
    """Tính tổng hợp số ca Diabetes theo SexLabel"""
    sex_map = {0: "Nữ", 1: "Nam"}
    df = df.copy()
    df["SexLabel"] = df["Sex"].map(sex_map)

    counts = (
        df.groupby(["SexLabel", "Diabetes"])
        .size()
        .reset_index(name="Count")
    )
    return counts


@st.cache_data
def agg_age_sex_diabetes(df: pd.DataFrame):
    """Tính tỉ lệ Diabetes theo Age + SexLabel"""
    sex_map = {0: "Nữ", 1: "Nam"}
    df = df.copy()
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
    return pivot_df


@st.cache_data
def agg_feature_sex_diabetes(df: pd.DataFrame, feature: str):
    """Tính tỉ lệ Diabetes theo 1 feature + SexLabel"""
    sex_map = {0: "Nữ", 1: "Nam"}
    df = df.copy()
    df["SexLabel"] = df["Sex"].map(sex_map)

    agg = (
        df.groupby([feature, "SexLabel"])["Diabetes"]
        .mean()
        .reset_index()
        .rename(columns={"Diabetes": "Diabetes_rate"})
    )

    if agg.empty:
        return None

    agg["Diabetes_percent"] = agg["Diabetes_rate"] * 100
    agg = agg.sort_values(feature)
    pivot_df = agg.pivot(index=feature, columns="SexLabel", values="Diabetes_percent")
    return pivot_df


# ============================================================
# FRAGMENT - Feature vs Sex Chart (có selectbox)
# ============================================================

@fragment
def show_feature_vs_sex_chart(df: pd.DataFrame, numeric_cols: list[str]):
    """Block có selectbox → fragment để tránh reload toàn page"""
    st.subheader("Biểu đồ mối quan hệ giữa bệnh tiểu đường theo các giá trị khác và giới tính")

    required_cols = {"Diabetes", "Sex"}
    if not required_cols.issubset(df.columns):
        missing = required_cols.difference(df.columns)
        st.error(f"Thiếu các cột cần thiết cho biểu đồ: {missing}")
        return

    def is_binary_feature(series: pd.Series) -> bool:
        vals = series.dropna().unique()
        if len(vals) == 0:
            return False
        return len(vals) <= 2 and set(vals).issubset({0, 1})

    # Lọc features
    feature_candidates: list[str] = []
    for col in numeric_cols:
        if col in ["Diabetes", "Sex"]:
            continue
        if is_binary_feature(df[col]):
            continue
        feature_candidates.append(col)

    if len(feature_candidates) == 0:
        st.warning("Không còn thuộc tính số nào phù hợp để vẽ")
        return

    # ✅ Hiển thị tên tiếng Việt trong selectbox
    feature_labels = {col: get_column_label(col) for col in feature_candidates}
    selected_label = st.selectbox(
        "Chọn một thuộc tính để vẽ cùng Diabetes",
        options=list(feature_labels.values()),
        key="feature_vs_sex_select",
    )
    
    # Tìm tên cột gốc từ label
    selected_feature = [k for k, v in feature_labels.items() if v == selected_label][0]

    pivot_df = agg_feature_sex_diabetes(df, selected_feature)
    if pivot_df is None or pivot_df.empty:
        st.warning("Không có dữ liệu phù hợp để vẽ biểu đồ")
        return

    fig_line, ax_line = plt.subplots(figsize=(7, 3), facecolor="none", dpi=150)
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
            color=color_map.get(sex_value, "#ffffff"),
        )

    ax_line.set_xlabel(f"{get_column_label(selected_feature)}")
    ax_line.set_ylabel("Tỉ lệ mắc bệnh tiểu đường (%)")
    ax_line.set_title(
        f"Tỉ lệ mắc bệnh tiểu đường theo {get_column_label(selected_feature).lower()} và giới tính"
    )

    ax_line.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    ax_line.grid(True, alpha=0.3)
    ax_line.legend(title="Giới tính")

    for spine in ax_line.spines.values():
        spine.set_visible(False)

    st.pyplot(fig_line, use_container_width=False)
    plt.close(fig_line)


# ============================================================
# MAIN VIEW
# ============================================================

def show_visualize(user: dict | None = None):
    """Trang phân tích dữ liệu"""

    # CSS styling
    image_path = os.path.join(os.path.dirname(__file__), "..", "assets", "background.jpg")
    img_base64 = get_base64_of_image(image_path)

    st.markdown(
        f"""
        <style>
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

        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/jpeg;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        [data-testid="stAppViewContainer"] .main {{
            background: transparent !important;
        }}

        .block-container {{
            background: transparent !important;
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("☁️ DAJTA CLOUD: TRÍ TUỆ NHÂN TẠO VỀ SỨC KHỎE BỆNH TIỂU ĐƯỜNG")

    # 1. Load data
    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "Data", "merged_diabetes_dataset.csv")
    
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
    target_col = "Diabetes"

    if target_col not in numeric_cols:
        st.error("Cột Diabetes cần ở dạng số (0 và 1)")
        st.stop()

    # 2. Overview
    st.subheader("Tổng quan dữ liệu đã nhập")
    n_rows, n_cols = df.shape
    st.write(f"Dữ liệu đưa vào gồm {n_rows} dòng và {n_cols} cột")
    st.dataframe(df.head())

    # 3. Descriptive stats
    st.subheader("Thống kê mô tả")
    st.write(describe_df(df))

    # 4. Histogram
    st.subheader("Phân phối các thuộc tính dạng số")
    numeric_plot_cols = [c for c in numeric_cols if c != target_col]
    numeric_plot_cols = [col for col in numeric_plot_cols if df[col].nunique() > 2]

    if len(numeric_plot_cols) == 0:
        st.warning("Không có thuộc tính dạng số nào ngoài Diabetes")
    else:
        for col in numeric_plot_cols:
            num_unique = df[col].nunique()
            
            # ✅ Xử lý riêng cho MentHlth và PhysHlth (số ngày không khỏe)
            if col in ['MentHlth', 'PhysHlth']:
                st.markdown("---")
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig_health, ax_health = plt.subplots(figsize=(5, 3), facecolor="none")
                    fig_health.patch.set_alpha(0.0)
                    ax_health.set_facecolor("none")

                    # ✅ Histogram cho số ngày
                    sns.histplot(
                        df[col].dropna(),
                        bins=31,  # 0-30 ngày
                        kde=False,
                        ax=ax_health,
                        color="#4ecdc4" if col == 'MentHlth' else "#f9c74f",
                    )
                    
                    ax_health.set_title(f"{get_column_label(col)}", 
                                       fontsize=11, weight='bold')
                    ax_health.set_xlabel("Số ngày không khỏe (trong 30 ngày)", fontsize=9)
                    ax_health.set_ylabel("Tần số", fontsize=9)
                    ax_health.grid(True, alpha=0.3, axis='y')

                    for spine in ax_health.spines.values():
                        spine.set_visible(False)

                    plt.tight_layout()
                    st.pyplot(fig_health, use_container_width=False)
                    plt.close(fig_health)
                
                with col2:                    
                    
                    st.markdown("**📋 Phân loại mức độ:**")
                    
                    # ✅ Phân loại mức độ
                    good = len(df[df[col] == 0])
                    moderate = len(df[(df[col] > 0) & (df[col] <= 7)])
                    bad = len(df[(df[col] > 7) & (df[col] <= 14)])
                    very_bad = len(df[df[col] > 14])
                    total = len(df[col].dropna())
                    
                    category_data = [
                        {"Mức độ": "🟢 Khỏe (0 ngày)", "Số người": f"{good:,}", "Tỉ lệ": f"{(good/total*100):.1f}%"},
                        {"Mức độ": "🟡 Nhẹ (1-7 ngày)", "Số người": f"{moderate:,}", "Tỉ lệ": f"{(moderate/total*100):.1f}%"},
                        {"Mức độ": "🟠 Trung bình (8-14 ngày)", "Số người": f"{bad:,}", "Tỉ lệ": f"{(bad/total*100):.1f}%"},
                        {"Mức độ": "🔴 Nặng (>14 ngày)", "Số người": f"{very_bad:,}", "Tỉ lệ": f"{(very_bad/total*100):.1f}%"},
                    ]
                    
                    category_df = pd.DataFrame(category_data)
                    st.markdown(category_df.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            # ✅ Bar chart cho Age, GenHlth, Education, Income
            elif num_unique > 4 and col in COLUMN_VALUE_LABELS:
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    fig_hist, ax_hist = plt.subplots(figsize=(5, 3), facecolor="none")
                    fig_hist.patch.set_alpha(0.0)
                    ax_hist.set_facecolor("none")

                    # ✅ Lấy value counts và sort theo index
                    value_counts = df[col].value_counts().sort_index()
                    
                    # ✅ Tạo labels tiếng Việt cho x-axis
                    x_labels = [get_value_label(col, val) for val in value_counts.index]
                    
                    ax_hist.bar(
                        range(len(value_counts)),
                        value_counts.values,
                        color="#ff6b6b",
                        edgecolor="white",
                        linewidth=1.5
                    )
                    
                    ax_hist.set_title(get_column_label(col), fontsize=11, weight='bold')
                    ax_hist.set_xlabel("")
                    ax_hist.set_ylabel("Tần số", fontsize=9)
                    ax_hist.grid(True, alpha=0.3, axis='y')
                    
                    # ✅ Set x-ticks với labels tiếng Việt
                    if len(x_labels) <= 15:
                        ax_hist.set_xticks(range(len(value_counts)))
                        ax_hist.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=7)
                    else:
                        ax_hist.set_xticks(range(0, len(value_counts), 2))
                        ax_hist.set_xticklabels([x_labels[i] for i in range(0, len(value_counts), 2)], 
                                                rotation=45, ha='right', fontsize=7)

                    for spine in ax_hist.spines.values():
                        spine.set_visible(False)

                    plt.tight_layout()
                    st.pyplot(fig_hist, use_container_width=False)
                    plt.close(fig_hist)
                
                with col2:
                    st.markdown("**Chú thích nhóm:**")
                    
                    # ✅ Tạo bảng chú thích
                    legend_data = []
                    for val in value_counts.index:
                        count = value_counts[val]
                        percent = (count / value_counts.sum()) * 100
                        legend_data.append({
                            "Nhóm": int(val),
                            "Giá trị": get_value_label(col, val),
                            "Số lượng": f"{count:,}",
                            "Tỉ lệ": f"{percent:.1f}%"
                        })
                    
                    legend_df = pd.DataFrame(legend_data)
                    st.markdown(legend_df.to_html(escape=False, index=False), unsafe_allow_html=True)
                    
            else:
                # ✅ Histogram thông thường cho BMI
                fig_hist, ax_hist = plt.subplots(figsize=(3, 2), facecolor="none")
                fig_hist.patch.set_alpha(0.0)
                ax_hist.set_facecolor("none")

                sns.histplot(
                    df[col].dropna(),
                    bins=30,
                    kde=False,
                    ax=ax_hist,
                    color="#ff6b6b",
                )
                ax_hist.set_title(get_column_label(col), fontsize=9)
                ax_hist.set_xlabel("")
                ax_hist.set_ylabel("Tần số", fontsize=8)
                ax_hist.grid(True, alpha=0.3)

                for spine in ax_hist.spines.values():
                    spine.set_visible(False)

                st.pyplot(fig_hist, use_container_width=False)
                plt.close(fig_hist) 

    # 5. Pie charts
    st.subheader("Biểu đồ tròn cho các thuộc tính phân loại")
    categorical_cols = [c for c in df.columns if c not in numeric_plot_cols and c != target_col]

    if len(categorical_cols) == 0:
        st.warning("Không có thuộc tính phân loại")
    else:
        # ✅ Màu cho binary (0/1)
        binary_colors = ["#1f9a00", "#ff6b6b"]  # Xanh (Không), Đỏ (Có)
        
        # ✅ Màu cho Sex
        sex_colors = ["#f9c74f", "#4ecdc4"]  # Vàng (Nữ), Xanh dương (Nam)

        def plot_cat_pie(ax, col_name):
            value_counts = df[col_name].value_counts(dropna=False).sort_index()
            
            if value_counts.empty:
                ax.text(0.5, 0.5, "Không có dữ liệu",
                        ha="center", va="center", fontsize=7)
                ax.axis("off")
                return

            sizes = value_counts.values
            
            # ✅ Chọn màu dựa trên cột
            if col_name == 'Sex':
                colors_to_use = sex_colors[:len(sizes)]
            else:
                colors_to_use = binary_colors[:len(sizes)]

            # ✅ Tạo labels tiếng Việt
            labels = [get_value_label(col_name, val) for val in value_counts.index]

            wedges, texts, autotexts = ax.pie(
                sizes,
                labels=labels,
                startangle=90,
                autopct="%1.1f%%",
                pctdistance=0.8,
                colors=colors_to_use,
                wedgeprops={"edgecolor": "white", "linewidth": 1.5},
                textprops={"fontsize": 8, "weight": "bold"}
            )

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_weight('bold')

            ax.axis("equal")
            ax.set_title(get_column_label(col_name), fontsize=10, y=1.05, weight='bold')

        # Vẽ từng hàng, mỗi figure chứa tối đa 2 pie chart
        for i in range(0, len(categorical_cols), 2):
            cols_pair = categorical_cols[i:i + 2]
            n = len(cols_pair)

            fig, axes = plt.subplots(
                1,
                n,
                figsize=(3.5 * n, 3.0),
                dpi=180,
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
                top=0.90,
                bottom=0.05,
                wspace=0.4
            )

            st.pyplot(fig, use_container_width=False)
            plt.close(fig)

    # 6. Correlation matrix
    st.subheader("Ma trận tương quan giữa các feature và Diabetes")
    corr = compute_corr(df, numeric_cols)
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
    
    # ✅ Đổi labels sang tiếng Việt
    ax_corr.set_xticklabels([get_column_label(col) for col in cols], rotation=45, ha='right', fontsize=8)
    ax_corr.set_yticklabels([get_column_label(col) for col in cols], rotation=0, fontsize=8)
    
    for spine in ax_corr.spines.values():
        spine.set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig_corr)
    plt.close(fig_corr)

    # 7. Top features
    st.subheader("Chọn các feature có tương quan cao với Diabetes")
    target_corr = corr[target_col].drop(target_col)
    abs_target_corr = target_corr.abs().sort_values(ascending=False)
    max_features = len(abs_target_corr)

    top_n = st.slider(
        "Chọn số feature có độ tương quan tuyệt đối lớn nhất với Diabetes",
        min_value=1,
        max_value=max_features,
        value=min(5, max_features),
    )

    top_feature_names = abs_target_corr.index[:top_n]
    top_features_signed = target_corr.loc[top_feature_names]

    result_df = pd.DataFrame({
        "Thuộc tính": [get_column_label(col) for col in top_features_signed.index],
        "Độ tương quan": top_features_signed.values,
    })

    st.write("Các feature được chọn theo độ tương quan với bệnh tiểu đường")
    st.dataframe(result_df)

    # 8. Pie chart by Sex
    st.subheader("Biểu đồ tròn tỉ lệ mắc bệnh tiểu đường theo giới tính")

    required_cols = {"Diabetes", "Sex"}
    if not required_cols.issubset(df.columns):
        st.error(f"Thiếu cột: {required_cols.difference(df.columns)}")
    else:
        counts = agg_sex_diabetes(df)
        labels_legend = ["Có tiểu đường", "Không tiểu đường"]
        colors = ["#ff6b6b", "#1f9a00"]

        def get_sizes_for_sex(sex_label: str):
            data_sex = counts[counts["SexLabel"] == sex_label]
            if data_sex.empty:
                return None
            sizes = []
            for d in [1, 0]:
                val = data_sex.loc[data_sex["Diabetes"] == d, "Count"]
                sizes.append(int(val.iloc[0]) if not val.empty else 0)
            return sizes

        fig, axes = plt.subplots(1, 2, figsize=(6.0, 3.0), dpi=180, facecolor="none")
        fig.patch.set_alpha(0.0)

        for ax in axes:
            ax.set_facecolor("none")

        sizes_male = get_sizes_for_sex("Nam")
        if sizes_male is not None:
            wedges, texts, autotexts = axes[0].pie(
                sizes_male, 
                labels=labels_legend,
                startangle=90, 
                colors=colors,
                autopct="%1.1f%%", 
                pctdistance=0.7, 
                textprops={"fontsize": 8, "weight": "bold"},
                wedgeprops={"edgecolor": "white", "linewidth": 1.5}
            )
            for autotext in autotexts:
                autotext.set_color('white')
            axes[0].axis("equal")
            axes[0].set_title("Nam", fontsize=11, pad=8, weight='bold')
        else:
            axes[0].text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center", fontsize=7)
            axes[0].axis("off")

        sizes_female = get_sizes_for_sex("Nữ")
        if sizes_female is not None:
            wedges, texts, autotexts = axes[1].pie(
                sizes_female, 
                labels=labels_legend,
                startangle=90, 
                colors=colors,
                autopct="%1.1f%%", 
                pctdistance=0.7, 
                textprops={"fontsize": 8, "weight": "bold"},
                wedgeprops={"edgecolor": "white", "linewidth": 1.5}
            )
            for autotext in autotexts:
                autotext.set_color('white')
            axes[1].axis("equal")
            axes[1].set_title("Nữ", fontsize=11, pad=8, weight='bold')
        else:
            axes[1].text(0.5, 0.5, "Không có dữ liệu", ha="center", va="center", fontsize=7)
            axes[1].axis("off")

        fig.subplots_adjust(left=0.05, right=0.95, top=0.85, bottom=0.05, wspace=0.3)
        st.pyplot(fig, use_container_width=False)
        plt.close(fig)

    # 9. Line chart Age vs Diabetes
    st.subheader("Biểu đồ đường cho tỉ lệ mắc bệnh tiểu đường theo độ tuổi và giới tính")

    required_cols_age = {"Diabetes", "Age", "Sex"}
    if not required_cols_age.issubset(df.columns):
        st.error(f"Thiếu cột: {required_cols_age.difference(df.columns)}")
    else:
        pivot_df = agg_age_sex_diabetes(df)

        fig_line, ax_line = plt.subplots(figsize=(7, 3), facecolor="none", dpi=150)
        fig_line.patch.set_alpha(0.0)
        ax_line.set_facecolor("none")

        color_map = {"Nam": "#ff6b6b", "Nữ": "#f9c74f"}

        for sex_value in pivot_df.columns:
            ax_line.plot(
                pivot_df.index,
                pivot_df[sex_value],
                marker="o",
                label=f"Giới tính {sex_value}",
                color=color_map.get(sex_value, "#ffffff"),
            )

        ax_line.set_xlabel("Độ tuổi")
        ax_line.set_ylabel("Tỉ lệ mắc bệnh tiểu đường (%)")
        ax_line.set_title("Tỉ lệ mắc bệnh tiểu đường theo độ tuổi và giới tính")
        ax_line.yaxis.set_major_formatter(PercentFormatter(xmax=100))
        ax_line.grid(True, alpha=0.3)
        ax_line.legend(title="Giới tính")

        for spine in ax_line.spines.values():
            spine.set_visible(False)

        st.pyplot(fig_line, use_container_width=False)
        plt.close(fig_line)

    # 10. Fragment: Feature vs Sex
    show_feature_vs_sex_chart(df, numeric_cols)