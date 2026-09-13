import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Конфігурація сторінки
st.set_page_config(
    page_title="Toyota 2024 Supply Chain Risk Simulator | Quantitative School",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Стилізація
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #d90429;
    }
</style>
""", unsafe_allow_html=True)

# Заголовок
st.title("🚗 Toyota Motor Corp: Моделювання системного ризику постачання")
st.caption("Кількісна школа менеджменту • Оптимізація продуктового портфеля на базі звітності 2024 року")

# ----------------- SIDEBAR: ПАРАМЕТРИ -----------------
st.sidebar.header("⚙️ Вхідні параметри шоку")

shortage_pct = st.sidebar.slider(
    "Дефіцит критичних компонентів (%):",
    min_value=0,
    max_value=50,
    value=20,
    step=5,
    help="Відсоток скорочення постачання (наприклад, мікрочипів, батарей або кабельних джгутів)."
) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("Базова структура сегментів (2024)")

# Калібрування під 10.82 млн авто та $410.9 млрд виторгу:
# 1) Економ: 4.82 млн * $25,000 = $120.5 млрд
# 2) Mid/SUV: 4.30 млн * $43,000 = $184.9 млрд
# 3) Преміум: 1.70 млн * $62,059 = $105.5 млрд
# Сукупна виручка = $410.9 млрд | Питома маржа: Premium > Mid > Economy
segments = {
    "Economy (Corolla, Yaris)": {"base_vol": 4.82, "price": 25_000, "vc": 20_000, "color": "#6c757d"},
    "Mid / SUV (RAV4, Camry)": {"base_vol": 4.30, "price": 43_000, "vc": 31_000, "color": "#1d3557"},
    "Premium (Lexus, LC)": {"base_vol": 1.70, "price": 62_059, "vc": 39_059, "color": "#d90429"}
}

# Фіксовані витрати FC виведені з формули: TR ($410.9B) - VC ($315.8B) - Прибуток ($45.1B) = $50.0 млрд
fc_base = st.sidebar.number_input(
    "Постійні річні витрати (FC, $ млрд):",
    min_value=10.0,
    max_value=90.0,
    value=50.0,
    step=2.0,
    help="Амортизація заводів, науково-дослідні розробки (R&D), утримання штаб-квартири та постійний персонал."
)

# ----------------- РОЗРАХУНКОВА ЧАСТИНА -----------------
total_base_vol = sum(s["base_vol"] for s in segments.values())  # 10.82 млн
available_parts_vol = total_base_vol * (1.0 - shortage_pct)
deficit_units = total_base_vol * shortage_pct

for k, v in segments.items():
    v["margin"] = v["price"] - v["vc"]

# Сценарій 1: Наївне пропорційне скорочення
naive_vols = {k: v["base_vol"] * (1.0 - shortage_pct) for k, v in segments.items()}

# Сценарій 2: Жадібна кількісна оптимізація (пріоритет за питомою маржею)
opt_vols = {}
remaining_capacity = available_parts_vol

for k in ["Premium (Lexus, LC)", "Mid / SUV (RAV4, Camry)", "Economy (Corolla, Yaris)"]:
    allocated = min(segments[k]["base_vol"], remaining_capacity)
    opt_vols[k] = allocated
    remaining_capacity -= allocated

def compute_metrics(vols_dict):
    total_rev = sum(vols_dict[k] * segments[k]["price"] for k in vols_dict) / 1_000.0  # $ млрд
    total_vc = sum(vols_dict[k] * segments[k]["vc"] for k in vols_dict) / 1_000.0     # $ млрд
    total_vol = sum(vols_dict.values())
    ebit = total_rev - total_vc - fc_base
    return {
        "Volume": total_vol,
        "Revenue": total_rev,
        "VC": total_vc,
        "FC": fc_base,
        "EBIT": ebit,
        "Margin_pct": (ebit / total_rev * 100) if total_rev > 0 else 0
    }

res_base = compute_metrics({k: v["base_vol"] for k, v in segments.items()})
res_naive = compute_metrics(naive_vols)
res_opt = compute_metrics(opt_vols)

saved_ebit = res_opt["EBIT"] - res_naive["EBIT"]

# ----------------- ВІДОБРАЖЕННЯ KPI -----------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Випуск авто (Сценарії)", f"{res_naive['Volume']:.2f} млн", f"-{deficit_units:.2f} млн (-{shortage_pct*100:.0f}%)")
col2.metric("Прибуток: Наївний підхід", f"${res_naive['EBIT']:.2f} млрд", f"{(res_naive['EBIT'] - res_base['EBIT']):.2f} млрд", delta_color="inverse")
col3.metric("Прибуток: Оптимізація", f"${res_opt['EBIT']:.2f} млрд", f"{(res_opt['EBIT'] - res_base['EBIT']):.2f} млрд", delta_color="inverse")
col4.metric("🔥 Врятований прибуток", f"+${saved_ebit:.2f} млрд", "Ефект кількісної школи", delta_color="normal")

st.markdown("---")

# ----------------- ВІЗУАЛІЗАЦІЯ -----------------
col_chart1, col_chart2 = st.columns([1, 1])

with col_chart1:
    st.subheader("📊 Структура випуску за сегментами (млн авто)")
    fig_bar = go.Figure()

    scenarios = ["Базовий стан (2024)", "Наївне скорочення", "Кількісна оптимізація"]
    for k, v in segments.items():
        vals = [segments[k]["base_vol"], naive_vols[k], opt_vols[k]]
        fig_bar.add_trace(go.Bar(
            name=k,
            x=scenarios,
            y=vals,
            marker_color=v["color"],
            text=[f"{val:.2f}M" for val in vals],
            textposition="inside"
        ))

    fig_bar.update_layout(
        barmode="stack",
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_chart2:
    st.subheader("📉 Порівняння Прибутку (EBIT / Чистий ефект)")
    ebit_vals = [res_base["EBIT"], res_naive["EBIT"], res_opt["EBIT"]]
    colors = ["#2b2d42", "#d90429", "#2a9d8f"]

    fig_ebit = go.Figure(go.Bar(
        x=scenarios,
        y=ebit_vals,
        marker_color=colors,
        text=[f"${val:.2f}B" for val in ebit_vals],
        textposition="outside"
    ))

    fig_ebit.update_layout(
        height=420,
        yaxis_title="Прибуток ($ млрд)",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_ebit, use_container_width=True)

# ----------------- ЗВЕДЕНА ТАБЛИЦЯ -----------------
st.subheader("📋 Зведена аналітична таблиця (Toyota 2024 Baseline)")

summary_df = pd.DataFrame({
    "Метрика": [
        "Обсяг випуску (млн од.)",
        "Виручка / Виторг ($ млрд)",
        "Змінні витрати ($ млрд)",
        "Постійні витрати ($ млрд)",
        "Прибуток ($ млрд)",
        "Маржинальність (%)"
    ],
    "Базовий стан (2024)": [
        f"{res_base['Volume']:.2f}",
        f"${res_base['Revenue']:.2f}",
        f"${res_base['VC']:.2f}",
        f"${res_base['FC']:.2f}",
        f"${res_base['EBIT']:.2f}",
        f"{res_base['Margin_pct']:.1f}%"
    ],
    f"Наївний (-{shortage_pct*100:.0f}%)": [
        f"{res_naive['Volume']:.2f}",
        f"${res_naive['Revenue']:.2f}",
        f"${res_naive['VC']:.2f}",
        f"${res_naive['FC']:.2f}",
        f"${res_naive['EBIT']:.2f}",
        f"{res_naive['Margin_pct']:.1f}%"
    ],
    "Оптимізація міксу": [
        f"{res_opt['Volume']:.2f}",
        f"${res_opt['Revenue']:.2f}",
        f"${res_opt['VC']:.2f}",
        f"${res_opt['FC']:.2f}",
        f"${res_opt['EBIT']:.2f}",
        f"{res_opt['Margin_pct']:.1f}%"
    ],
    "Ефект оптимізації (Δ)": [
        "0.00",
        f"+${(res_opt['Revenue'] - res_naive['Revenue']):.2f}",
        f"+${(res_opt['VC'] - res_naive['VC']):.2f}",
        "$0.00",
        f"+${saved_ebit:.2f}",
        f"+{(res_opt['Margin_pct'] - res_naive['Margin_pct']):.1f} в.п."
    ]
})

st.dataframe(summary_df, use_container_width=True, hide_index=True)

# ----------------- ВИСНОВКИ ДЛЯ ЗАХИСТУ -----------------
with st.expander("💡 Методологічні пояснення до моделі 2024 року"):
    st.markdown(f"""
    * **Вихідні дані 2024:** Обсяг випуску 10.82 млн од., виручка $410.9 млрд і прибуток $45.1 млрд взяті з річної звітності.
    * **Принцип оптимізації:** Lexus приносить **$23 000** маржі з однієї машини, RAV4/Camry — **$12 000**, а Corolla/Yaris — лише **$5 000**.
    * **Результат:** При дефіциті у 20% лінійний розподіл наявних деталей рятує **${saved_ebit:.2f} млрд** прибутку без залучення зовнішнього фінансування.
    """)
