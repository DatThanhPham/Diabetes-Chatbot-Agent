import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.patches as mpatches
from matplotlib.ticker import PercentFormatter

# Fragment decorator: use st.fragment if its available, fallback to experimental
try:
    fragment = st.fragment  # Streamlit >= 1.33
except AttributeError:
    fragment = st.experimental_fragment  

@st.cache_data
def describe_df(df: pd.DataFrame):
    return df.describe(include="all")


@st.cache_data
def compute_corr(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    return df[numeric_cols].corr()


@st.cache_data
def agg_sex_diabetes(df: pd.DataFrame):
    """
    Tính tổng hợp số ca Diabetes theo SexLabel để vẽ pie chart.
    Trả về: counts DataFrame + mapping SexLabel.
    """
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
    """
    Tính tỉ lệ Diabetes theo Age + SexLabel để vẽ line chart.
    """
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
    agg["Age"] = agg["Age"] * 5  # Hệ số nhóm tuổi như bạn dùng

    pivot_df = agg.pivot(index="Age", columns="SexLabel", values="Diabetes_percent")
    return pivot_df


@st.cache_data
def agg_feature_sex_diabetes(df: pd.DataFrame, feature: str):
    """
    Tính tỉ lệ Diabetes theo 1 feature (liên tục) + SexLabel để vẽ line chart.
    """
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


# ------------------------------------------------------------
# FRAGMENT 1 – Biểu đồ mối quan hệ Diabetes vs 1 feature + giới tính (CÓ selectbox)
# ------------------------------------------------------------

@fragment
def show_feature_vs_sex_chart(df: pd.DataFrame, numeric_cols: list[str]):
    """
    Block này có selectbox → tách thành fragment để thay đổi option
    chỉ khiến block này rerun, hạn chế cảm giác “reload cả page”.
    """
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

    # Lọc các feature ứng viên
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

    # 🔥 Widget nằm trong fragment
    selected_feature = st.selectbox(
        "Chọn một thuộc tính để vẽ cùng Diabetes",
        feature_candidates,
        key="feature_vs_sex_select",
    )

    pivot_df = agg_feature_sex_diabetes(df, selected_feature)
    if pivot_df is None or pivot_df.empty:
        st.warning("Không có dữ liệu phù hợp để vẽ biểu đồ")
        return

    fig_line, ax_line = plt.subplots(figsize=(6, 3), dpi=150)
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

    ax_line.set_xlabel(f"Giá trị thuộc tính {selected_feature}")
    ax_line.set_ylabel("Tỉ lệ mắc bệnh tiểu đường (%)")
    ax_line.set_title(
        f"Tỉ lệ mắc bệnh tiểu đường theo {selected_feature} và giới tính"
    )

    ax_line.yaxis.set_major_formatter(PercentFormatter(xmax=100))
    ax_line.grid(True)
    ax_line.legend(title="Giới tính")

    st.pyplot(fig_line, use_container_width=False)
    plt.close(fig_line)


# ------------------------------------------------------------
# HÀM CHÍNH – VIEW
# ------------------------------------------------------------

def show_visualize(user: dict | None = None):
    """
    Trang phân tích dữ liệu – gọi từ app.py:
        from views.visualize import show_visualize
        ...
        elif current_page == "Phân tích dữ liệu":
            show_visualize(user)
    """

    st.title("☁️ DJAT CLOUD: TRÍ TUỆ NHÂN TẠO VỀ SỨC KHỎE BỆNH TIỂU ĐƯỜNG")

    # 1. Chọn / tải file dữ liệu, lưu vào session
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
    target_col = "Diabetes"

    if target_col not in numeric_cols:
        st.error("Cột Diabetes cần ở dạng số, ví dụ 0 và 1")
        st.stop()

    # 1. Tổng quan + head
    st.subheader("Tổng quan dữ liệu đã nhập")
    n_rows, n_cols = df.shape
    st.write(f"Dữ liệu đưa vào gồm {n_rows} dòng và {n_cols} cột")
    st.dataframe(df.head())

    # 2. Thống kê mô tả (CACHE)
    st.subheader("Thống kê mô tả")
    st.write(describe_df(df))

    # 3. Histogram cho các thuộc tính dạng số
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
                    fig_hist, ax_hist = plt.subplots(figsize=(3, 2))
                    sns.histplot(
                        df[col].dropna(),
                        bins=30,
                        kde=False,
                        ax=ax_hist,
                        color="#ff6b6b",
                    )
                    ax_hist.set_title(col, fontsize=9)
                    ax_hist.set_xlabel("")
                    ax_hist.set_ylabel("Tần số", fontsize=8)
                    ax_hist.grid(True, alpha=0.3)
                    st.pyplot(fig_hist, use_container_width=False)

    # 4. Pie chart cho các thuộc tính phân loại
    with st.container():
        st.subheader("Biểu đồ tròn cho các thuộc tính phân loại")
        categorical_cols = [c for c in df.columns if c not in numeric_plot_cols]

        if len(categorical_cols) == 0:
            st.warning("Không có thuộc tính phân loại nào trong dữ liệu.")
        else:
            base_colors = ["#ff6b6b", "#1f9a00"]

            def plot_cat_pie(col_name: str):
                value_counts = df[col_name].value_counts(dropna=False)
                if value_counts.empty:
                    return None

                sizes = value_counts.values
                if len(sizes) <= 2:
                    colors_to_use = base_colors[:len(sizes)]
                else:
                    colors_to_use = (base_colors * ((len(sizes) + 1) // 2))[:len(sizes)]

                fig, ax = plt.subplots(figsize=(3.0, 3.0), dpi=160)
                fig.patch.set_alpha(0.0)
                ax.set_facecolor("none")

                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=value_counts.index.astype(str),
                    startangle=90,
                    autopct="%1.1f%%",
                    pctdistance=0.8,
                    colors=colors_to_use,
                    wedgeprops={"edgecolor": "white"},
                    textprops={"fontsize": 8},
                )
                for t in autotexts:
                    t.set_ha("center")
                    t.set_va("center")

                ax.axis("equal")
                ax.set_title(col_name, fontsize=11, pad=8)
                return fig

            # 👉 Mỗi cột phân loại = 1 dòng, pie nằm giữa
            for col_name in categorical_cols:
                center_col = st.columns([1, 2, 1])[1]
                with center_col:
                    fig = plot_cat_pie(col_name)
                    if fig is not None:
                        st.pyplot(fig, use_container_width=False)
                        plt.close(fig)

            # Legend chung
            labels_legend = ["Có tiểu đường", "Không tiểu đường"]
            colors = ["#ff6b6b", "#1f9a00"]

            handles = [
                mpatches.Patch(color=c, label=l)
                for c, l in zip(colors, labels_legend)
            ]

            fig_leg, ax_leg = plt.subplots(figsize=(3, 0.8), dpi=160)
            fig_leg.patch.set_alpha(0.0)
            ax_leg.axis("off")
            ax_leg.legend(
                handles=handles,
                loc="center",
                ncol=2,
                frameon=False,
                fontsize=8,
            )
            fig_leg.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
            st.pyplot(fig_leg, use_container_width=False)
            plt.close(fig_leg)


    # 5. Ma trận tương quan (CACHE)
    with st.container():
        st.subheader("Ma trận tương quan giữa các feature và Diabetes")
        corr = compute_corr(df, numeric_cols)
        cols = [target_col] + [c for c in corr.columns if c != target_col]
        corr = corr.loc[cols, cols]

        n = len(cols)
        # Giảm kích thước + tăng dpi cho nét
        fig_corr, ax_corr = plt.subplots(
            figsize=(min(0.5 * n + 2, 8), min(0.5 * n + 2, 6)),
            dpi=160,
        )
        fig_corr.patch.set_alpha(0.0)
        ax_corr.set_facecolor("none")

        # Nếu quá nhiều cột thì tắt annot cho đỡ rối
        show_annot = n <= 15

        sns.heatmap(
            corr,
            annot=show_annot,
            annot_kws={"size": 7} if show_annot else None,
            fmt=".2f",
            vmin=-1,
            vmax=1,
            cmap="coolwarm",
            square=True,
            cbar=True,
            ax=ax_corr,
        )
        ax_corr.set_title("Biểu đồ nhiệt ma trận tương quan các feature và Diabetes", fontsize=11, pad=8)
        ax_corr.set_xlabel("Feature")
        ax_corr.set_ylabel("Feature")
        for spine in ax_corr.spines.values():
            spine.set_visible(False)

        plt.tight_layout()
        st.pyplot(fig_corr, use_container_width=False)
        plt.close(fig_corr)

    # 6. Chọn top feature tương quan
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
        "Thuộc tính": top_features_signed.index,
        "Độ tương quan": top_features_signed.values,
    })

    st.write("Các feature được chọn theo độ tương quan với bệnh tiểu đường")
    st.dataframe(result_df)

    # 7. Biểu đồ pie tỉ lệ tiểu đường theo giới (CACHE)
    with st.container():
        st.subheader("Biểu đồ tròn tỉ lệ mắc bệnh tiểu đường theo giới tính")

        required_cols = {"Diabetes", "Sex"}
        if not required_cols.issubset(df.columns):
            missing = required_cols.difference(df.columns)
            st.error(f"Thiếu các cột cần thiết cho biểu đồ: {missing}")
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

            fig, axes = plt.subplots(
                1,
                2,
                figsize=(5, 2.4),   # nhỏ hơn
                dpi=160,
            )
            fig.patch.set_alpha(0.0)

            # Nam
            sizes_male = get_sizes_for_sex("Nam")
            if sizes_male is not None:
                axes[0].pie(
                    sizes_male,
                    labels=None,
                    startangle=90,
                    colors=colors,
                    autopct="%1.1f%%",
                    pctdistance=0.7,
                    textprops={"fontsize": 8},
                )
                axes[0].axis("equal")
                axes[0].set_title("Nam", fontsize=10, pad=2)
            else:
                axes[0].text(0.5, 0.5, "Không có dữ liệu",
                             ha="center", va="center", fontsize=8)
                axes[0].axis("off")

            # Nữ
            sizes_female = get_sizes_for_sex("Nữ")
            if sizes_female is not None:
                axes[1].pie(
                    sizes_female,
                    labels=None,
                    startangle=90,
                    colors=colors,
                    autopct="%1.1f%%",
                    pctdistance=0.7,
                    textprops={"fontsize": 8},
                )
                axes[1].axis("equal")
                axes[1].set_title("Nữ", fontsize=10, pad=2)
            else:
                axes[1].text(0.5, 0.5, "Không có dữ liệu",
                             ha="center", va="center", fontsize=8)
                axes[1].axis("off")

            fig.subplots_adjust(
                left=0.08,
                right=0.92,
                top=0.88,
                bottom=0.15,
                wspace=0.3,
            )
            st.pyplot(fig, use_container_width=False)
            plt.close(fig)

            handles = [
                mpatches.Patch(color=c, label=l)
                for c, l in zip(colors, labels_legend)
            ]

            fig_leg, ax_leg = plt.subplots(figsize=(3, 0.8), dpi=160)
            fig_leg.patch.set_alpha(0.0)
            ax_leg.axis("off")
            ax_leg.legend(
                handles=handles,
                loc="center",
                ncol=2,
                frameon=False,
                fontsize=8,
            )
            fig_leg.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
            st.pyplot(fig_leg, use_container_width=False)
            plt.close(fig_leg)


    # 8. Biểu đồ đường Diabetes theo độ tuổi & giới (CACHE)
    with st.container():
        st.subheader("Biểu đồ đường cho tỉ lệ mắc bệnh tiểu đường theo độ tuổi và giới tính")

        required_cols_age = {"Diabetes", "Age", "Sex"}
        if not required_cols_age.issubset(df.columns):
            missing = required_cols_age.difference(df.columns)
            st.error(f"Thiếu các cột cần thiết cho biểu đồ: {missing}")
        else:
            pivot_df = agg_age_sex_diabetes(df)

            fig_line, ax_line = plt.subplots(figsize=(6, 3), dpi=150)
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

            ax_line.set_xlabel("Độ tuổi")
            ax_line.set_ylabel("Tỉ lệ mắc bệnh tiểu đường (%)")
            ax_line.set_title("Tỉ lệ mắc bệnh tiểu đường theo độ tuổi và giới tính")

            ax_line.yaxis.set_major_formatter(PercentFormatter(xmax=100))
            ax_line.grid(True, alpha=0.3)
            ax_line.legend(title="Giới tính", fontsize=8)

            plt.tight_layout()
            st.pyplot(fig_line, use_container_width=False)
            plt.close(fig_line)


    # 9. Biểu đồ mối quan hệ Diabetes vs feature + Sex (FRAGMENT – selectbox)
    show_feature_vs_sex_chart(df, numeric_cols)
