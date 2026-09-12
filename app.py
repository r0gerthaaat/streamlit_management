import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Конфігурація сторінки
st.set_page_config(
    page_title="Toyota Supply Chain Risk Simulator | Quantitative School",
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
st.caption("Кількісна школа менеджменту • Оптимізація продуктового портфеля в умовах дефіциту ресурсів")

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
st.sidebar.subheader("Базова структура сегментів")

# Базові константи (млн авто, ціна $, змінні витрати $)
segments = {
    "Economy (Corolla, Yaris)": {"base_vol": 4.5, "price": 22_000, "vc": 18_000, "color": "#6c757d"},
    "Mid / SUV (RAV4, Camry)": {"base_vol": 4.0, "price": 36_000, "vc": 26_000, "color": "#1d3557"},
    "Premium (Lexus, LC)": {"base_vol": 1.5, "price": 65_000, "vc": 42_000, "color": "#d90429"}
}

fc_base = st.sidebar.number_input(
    "Постійні річні витрати (FC, $ млрд):",
    min_value=10.0,
    max_value=80.0,
    value=40.0,
    step=2.0
)

# ----------------- РОЗРАХУНКОВА ЧАСТИНА -----------------
total_base_vol = sum(s["base_vol"] for s in segments.values())  # 10 млн
available_parts_vol = total_base_vol * (1.0 - shortage_pct)      # ліміт виробництва
deficit_units = total_base_vol * shortage_pct                   # скільки не вистачає

# 1. Розрахунок маржі на одиницю (Unit Margin)
for k, v in segments.items():
    v["margin"] = v["price"] - v["vc"]

# 2. Сценарій А: Наївне (пропорційне) скорочення
naive_vols = {k: v["base_vol"] * (1.0 - shortage_pct) for k, v in segments.items()}

# 3. Сценарій Б: Кількісна оптимізація (Жадібний LP алгоритм за питомою маржею)
# Маржинальність: Premium ($23k) > Mid ($10k) > Economy ($4k)
opt_vols = {}
remaining_capacity = available_parts_vol

# Пріоритет: Преміум -> SUV -> Економ
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

base_vols = {k: v["base_vol"] for k, v in segments.items()}
res_base = compute_metrics(base_vols)
res_naive = compute_metrics(naive_vols)
res_opt = compute_metrics(opt_vols)

saved_ebit = res_opt["EBIT"] - res_naive["EBIT"]

# ----------------- ВІДОБРАЖЕННЯ KPI -----------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Випуск авто (Сценарії)", f"{res_naive['Volume']:.2f} млн", f"-{deficit_units:.2f} млн (-{shortage_pct*100:.0f}%)")
col2.metric("EBIT: Наївний підхід", f"${res_naive['EBIT']:.2f} млрд", f"{(res_naive['EBIT'] - res_base['EBIT']):.2f} млрд", delta_color="inverse")
col3.metric("EBIT: Оптимізація", f"${res_opt['EBIT']:.2f} млрд", f"{(res_opt['EBIT'] - res_base['EBIT']):.2f} млрд", delta_color="inverse")
col4.metric("🔥 Врятований прибуток", f"+${saved_ebit:.2f} млрд", "Ефект кількісної школи", delta_color="normal")

st.markdown("---")

# ----------------- ВІЗУАЛІЗАЦІЯ -----------------
col_chart1, col_chart2 = st.columns([1, 1])

with col_chart1:
    st.subheader("📊 Структура випуску за сегментами (млн авто)")
    fig_bar = go.Figure()

    scenarios = ["Базовий стан", "Наївне скорочення", "Кількісна оптимізація"]
    for k, v in segments.items():
        vals = [base_vols[k], naive_vols[k], opt_vols[k]]
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
    st.subheader("📉 Порівняння Операційного Прибутку (EBIT)")
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
        yaxis_title="EBIT ($ млрд)",
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_ebit, use_container_width=True)

# ----------------- ТАБЛИЦЯ ДЛЯ ПРЕЗЕНТАЦІЇ -----------------
st.subheader("📋 Зведена аналітична таблиця (Дані для виступу)")

summary_df = pd.DataFrame({
    "Метрика": [
        "Обсяг випуску (млн од.)",
        "Виручка ($ млрд)",
        "Змінні витрати ($ млрд)",
        "Постійні витрати ($ млрд)",
        "Операційний прибуток EBIT ($ млрд)",
        "Рентабельність (EBIT Margin, %)"
    ],
    "Базовий стан": [
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

# ----------------- ВИСНОВКИ ДЛЯ 5-Ї ЛЮДИНИ -----------------
with st.expander("💡 Системні висновки для переходу до Пункту 5 (Рішення)"):
    st.markdown(f"""
    1. **Жорсткість постійних витрат:** При падінні виробництва на **{shortage_pct*100:.0f}%** наївна стратегія призводить до обвалу операційного прибутку на **{abs((res_naive['EBIT'] - res_base['EBIT']) / res_base['EBIT'] * 100):.1f}%** через високий операційний леверидж (постійні витрати $40 млрд залишаються незмінними).
    2. **Перевага кількісного методу:** Перерозподіл лімітованих ресурсів у преміальні моделі (Lexus / SUV) зберігає **${saved_ebit:.2f} млрд** прибутку при абсолютно однаковій кількості випущених авто ({res_opt['Volume']:.1f} млн).
    3. **Зв'язок систем:** Збій на *Вході* (постачання) не обов'язково лінійно транслюється на *Вихід* (прибуток), якщо підсистема *Управління виробництвом* адаптує внутрішній пріоритет розподілу.
    """)