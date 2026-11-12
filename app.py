import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx

from queue_model.simulation import QueueConfig, simulate_bank
from queue_model.graph import draw_bank_graph
from game_model.game import play_match, MOVES

st.set_page_config(page_title="Simulation Lab", page_icon="◫", layout="wide")
st.title("Simulation Lab")
st.caption("Две модели сложных систем: массовое обслуживание и противодействие стратегий")

page = st.sidebar.radio("Раздел", ["Обзор", "Модель банка", "Игровая модель"])

if page == "Обзор":
    st.subheader("О проекте")
    st.write("Приложение демонстрирует две независимые имитационные модели.")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 1. Банк и очереди")
        st.write("Поток клиентов, общая очередь и несколько окон обслуживания. Модель использует случайные интервалы поступления и обслуживания.")
    with c2:
        st.markdown("### 2. Игра стратегий")
        st.write("Повторяющаяся игра «Камень, ножницы, бумага» с фиксированными, циклическими, случайными и адаптивными агентами.")
    st.info("Выберите модель в меню слева, измените параметры и запустите эксперимент.")

elif page == "Модель банка":
    st.subheader("Графовая модель банка")
    st.write("Клиенты поступают в систему, проходят регистрацию, ожидают свободного специалиста и покидают банк после обслуживания.")
    with st.sidebar:
        st.markdown("### Параметры банка")
        clerks = st.slider("Количество окон", 1, 10, 4)
        arrival_rate = st.slider("Поступление клиентов, чел./мин", 0.05, 0.8, 0.32, 0.01)
        service_rate = st.slider("Скорость обслуживания, чел./мин на окно", 0.03, 0.4, 0.12, 0.01)
        patience = st.slider("Терпение клиента, мин", 5, 120, 45)
        horizon = st.slider("Продолжительность моделирования, мин", 60, 720, 480, 30)
        seed = st.number_input("Начальное значение генератора", 0, 100000, 42)
    fig, ax = plt.subplots(figsize=(11, 4))
    draw_bank_graph(clerks, ax)
    st.pyplot(fig, use_container_width=True)
    if st.button("Запустить моделирование", type="primary"):
        cfg = QueueConfig(horizon=horizon, arrival_rate=arrival_rate,
                          service_rate=service_rate, clerks=clerks,
                          patience=patience, seed=int(seed))
        result = simulate_bank(cfg)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Поступило клиентов", result["arrivals"])
        m2.metric("Обслужено", result["served"])
        m3.metric("Среднее ожидание", f'{result["mean_wait"]:.1f} мин')
        m4.metric("Максимальная очередь", result["max_queue"])
        m5,m6,m7 = st.columns(3)
        m5.metric("Не дождались", result["abandoned"])
        m6.metric("Время в системе", f'{result["mean_system"]:.1f} мин')
        m7.metric("Оценка загрузки окон", f'{100*result["utilization_estimate"]:.1f}%')
        qdf = pd.DataFrame(result["queue"], columns=["Время, мин", "Очередь"])
        st.markdown("#### Изменение длины очереди")
        st.line_chart(qdf.set_index("Время, мин"))
        rdf = pd.DataFrame(result["records"])
        if not rdf.empty:
            st.markdown("#### Первые записи о клиентах")
            st.dataframe(rdf.head(20), use_container_width=True)
        st.caption("Оценка загрузки рассчитана по доле фактически обслуженных клиентов относительно теоретической мощности; это приближённый показатель, а не точная занятость ресурсов.")

elif page == "Игровая модель":
    st.subheader("Модель противодействия стратегий")
    st.write("Два агента одновременно выбирают один из трёх ходов. Адаптивный агент оценивает последние действия соперника и выбирает ответный ход.")
    strategies = ["Случайная", "Постоянная", "Циклическая", "Адаптивная"]
    with st.sidebar:
        st.markdown("### Параметры игры")
        strategy_a = st.selectbox("Стратегия игрока A", strategies, index=3)
        strategy_b = st.selectbox("Стратегия игрока B", strategies, index=0)
        rounds = st.slider("Количество раундов", 50, 5000, 1000, 50)
        seed = st.number_input("Начальное значение генератора", 0, 100000, 42, key="game_seed")
    if st.button("Запустить игру", type="primary"):
        result = play_match(strategy_a, strategy_b, rounds, int(seed))
        a,b,c,d = st.columns(4)
        a.metric("Победы A", result["wins_a"])
        b.metric("Победы B", result["wins_b"])
        c.metric("Ничьи", result["draws"])
        d.metric("Итоговый счёт A", result["score_a"])
        df = pd.DataFrame(result["history"])
        st.markdown("#### Динамика счёта")
        st.line_chart(df.set_index("Раунд")[["Счёт A", "Счёт B"]])
        st.markdown("#### Частота исходов")
        outcomes = pd.DataFrame({"Исход": ["Победа A", "Победа B", "Ничья"],
                                 "Количество": [result["wins_a"], result["wins_b"], result["draws"]]})
        st.bar_chart(outcomes.set_index("Исход"))
        st.markdown("#### История первых 30 раундов")
        st.dataframe(df.head(30), use_container_width=True)
        st.caption("Адаптивная стратегия использует частоты ходов соперника за последние 20 раундов. Это простая эвристика, а не обучение с гарантированным выигрышем.")
