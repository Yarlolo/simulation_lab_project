import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from queue_model.simulation import QueueConfig, simulate_bank
from queue_model.graph import draw_bank_graph
from game_model.game import play_match, run_tournament, MOVES

st.set_page_config(page_title="Simulation Lab", page_icon="◫", layout="wide")

# Minimal visual system
st.markdown("""
<style>
.block-container {padding-top: 1.8rem; padding-bottom: 3rem; max-width: 1400px;}
[data-testid="stMetric"] {background: #f7f9fc; border: 1px solid #e7ebf2; padding: 14px 16px; border-radius: 12px;}
section[data-testid="stSidebar"] {border-right: 1px solid #e8ebf0;}
.small-muted {color:#64748b; font-size:0.9rem;}
</style>
""", unsafe_allow_html=True)

st.title("Simulation Lab")
st.caption("Интерактивное исследование систем массового обслуживания и стратегического противодействия")
page = st.sidebar.radio("Раздел проекта", ["Обзор", "Модель банка", "Игровая модель"], index=0)

if page == "Обзор":
    st.subheader("Две модели — два типа сложных систем")
    st.write("Проект показывает, как с помощью имитационного моделирования исследовать процессы с очередями и поведение конкурирующих стратегий.")
    left, right = st.columns(2)
    with left:
        st.markdown("### 01 · Банк и очередь")
        st.write("Поток клиентов, общая очередь, несколько окон, ограниченное терпение и измерение качества обслуживания.")
        st.markdown("**Что исследуем:** ожидание, загрузку окон, пропускную способность и потери клиентов.")
    with right:
        st.markdown("### 02 · Игровая модель")
        st.write("Повторяющаяся игра «Камень, ножницы, бумага» с шестью типами поведения агентов и круговым турниром.")
        st.markdown("**Что исследуем:** устойчивость стратегий, адаптацию и результаты попарных столкновений.")
    st.divider()
    st.markdown("#### Как работать с приложением")
    st.markdown("1. Выберите модель в боковом меню.\n2. Измените параметры эксперимента.\n3. Запустите моделирование.\n4. Изучите графики, метрики и сравнение сценариев.")
    st.info("Результаты зависят от параметров и случайного seed. Для корректного сравнения сценариев используйте одинаковое начальное значение генератора.")

elif page == "Модель банка":
    st.subheader("Модель банка: графовая система массового обслуживания")
    st.write("Клиенты поступают с пуассоновским потоком, ожидают свободное окно и обслуживаются за случайное время. Если ожидание превышает терпение клиента, он покидает систему.")
    with st.sidebar:
        st.markdown("### Параметры эксперимента")
        clerks = st.slider("Количество окон", 1, 10, 4)
        arrival_rate = st.slider("Интенсивность поступления (клиентов/мин)", 0.05, 0.8, 0.32, 0.01)
        service_rate = st.slider("Интенсивность обслуживания на окно (клиентов/мин)", 0.03, 0.4, 0.12, 0.01)
        patience = st.slider("Терпение клиента (мин)", 5, 120, 45)
        horizon = st.slider("Время поступления клиентов (мин)", 60, 720, 480, 30)
        seed = st.number_input("Seed", 0, 100000, 42, key="bank_seed")
        run_bank = st.button("Запустить моделирование", type="primary", use_container_width=True)

    if run_bank:
        cfg = QueueConfig(horizon=horizon, arrival_rate=arrival_rate,
                          service_rate=service_rate, clerks=clerks,
                          patience=patience, seed=int(seed))
        with st.spinner("Моделируем поток клиентов..."):
            st.session_state["bank_result"] = simulate_bank(cfg)

    result = st.session_state.get("bank_result")
    st.markdown("#### 1. Структура системы")
    graph_fig, graph_ax = plt.subplots(figsize=(12, 4.8))
    draw_bank_graph(clerks, graph_ax)
    graph_fig.tight_layout()
    st.pyplot(graph_fig, use_container_width=True)
    plt.close(graph_fig)
    st.caption("Рёбра показывают возможные переходы клиента. Из общей очереди клиент направляется к любому освободившемуся окну.")

    if result:
        st.markdown("#### 2. Основные показатели")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Поступило", result["arrivals"])
        c2.metric("Обслужено", result["served"])
        c3.metric("Покинули очередь", result["abandoned"])
        c4.metric("Доля обслуженных", f'{100*result["served"]/max(result["arrivals"],1):.1f}%')
        c5,c6,c7,c8 = st.columns(4)
        c5.metric("Среднее ожидание", f'{result["mean_wait"]:.1f} мин')
        c6.metric("Медиана ожидания", f'{result["median_wait"]:.1f} мин')
        c7.metric("90-й перцентиль", f'{result["p90_wait"]:.1f} мин')
        c8.metric("Средняя загрузка окон", f'{100*result["utilization_estimate"]:.1f}%')

        timeline = pd.DataFrame(result["timeline"])
        st.markdown("#### 3. Динамика работы банка")
        tab1, tab2 = st.tabs(["Очередь и окна", "Прохождение клиентов"])
        with tab1:
            st.line_chart(timeline.set_index("Время")[["Очередь", "Занято окон"]], height=300)
            st.caption("Число ожидающих и занятых окон фиксируется с заданным временным шагом.")
        with tab2:
            if len(timeline) > 1:
                idx = st.slider("Момент моделирования (номер замера)", 0, len(timeline)-1, min(30, len(timeline)-1), key="bank_snapshot")
                snap = timeline.iloc[idx]
                st.write(f"Время: **{snap['Время']:.0f} мин** · В очереди: **{int(snap['Очередь'])}** · Занято окон: **{int(snap['Занято окон'])} из {clerks}**")
                st.progress(min(1.0, float(snap["Занято окон"])/clerks), text="Доля занятых окон в выбранный момент")
                live_fig, live_ax = plt.subplots(figsize=(12, 4.5))
                draw_bank_graph(clerks, live_ax, int(snap["Очередь"]), int(snap["Занято окон"]))
                live_fig.tight_layout()
                st.pyplot(live_fig, use_container_width=True)
                plt.close(live_fig)
                st.caption("На схеме зелёным отмечены занятые окна, жёлтым — очередь, в которой есть клиенты.")

        st.markdown("#### 4. Время ожидания клиентов")
        served_df = pd.DataFrame([r for r in result["records"] if r["served"]])
        if not served_df.empty:
            hist_fig, hist_ax = plt.subplots(figsize=(10, 3.2))
            hist_ax.hist(served_df["wait"], bins=25, edgecolor="white")
            hist_ax.set_xlabel("Ожидание, мин")
            hist_ax.set_ylabel("Количество клиентов")
            hist_ax.set_title("Распределение времени ожидания")
            hist_ax.grid(axis="y", alpha=.2)
            st.pyplot(hist_fig, use_container_width=True)
            plt.close(hist_fig)
        util_df = pd.DataFrame({"Окно": [f"Окно {k}" for k in result["clerk_utilization"]],
                                "Загрузка, %": [100*v for v in result["clerk_utilization"].values()]})
        st.markdown("#### 5. Загрузка каждого окна")
        st.bar_chart(util_df.set_index("Окно"), y="Загрузка, %")
        st.markdown("#### 6. Журнал клиентов")
        st.dataframe(pd.DataFrame(result["records"]).head(100), use_container_width=True, hide_index=True)
        st.download_button("Скачать журнал клиентов CSV", pd.DataFrame(result["records"]).to_csv(index=False).encode("utf-8-sig"), "bank_customers.csv", "text/csv")

        st.markdown("#### 7. Сравнение числа окон")
        if st.button("Сравнить конфигурации: 2–5 окон"):
            comparisons = []
            for n in range(2, 6):
                rr = simulate_bank(QueueConfig(horizon=horizon, arrival_rate=arrival_rate,
                    service_rate=service_rate, clerks=n, patience=patience, seed=int(seed)))
                comparisons.append({"Окон": n, "Обслужено": rr["served"], "Потеряно": rr["abandoned"],
                    "Среднее ожидание, мин": rr["mean_wait"], "Загрузка, %": 100*rr["utilization_estimate"]})
            st.session_state["bank_comparison"] = pd.DataFrame(comparisons)
        if "bank_comparison" in st.session_state:
            st.dataframe(st.session_state["bank_comparison"].round(2), use_container_width=True, hide_index=True)
            st.line_chart(st.session_state["bank_comparison"].set_index("Окон")[["Среднее ожидание, мин", "Потеряно"]])
    else:
        st.info("Настройте параметры слева и нажмите «Запустить моделирование», чтобы увидеть результаты.")

elif page == "Игровая модель":
    st.subheader("Игровая модель: противостояние стратегий")
    st.write("Агенты одновременно выбирают ход. Победитель получает +1, проигравший −1, ничья даёт 0. Адаптивные агенты используют историю ходов соперника.")
    strategies = ["Случайная", "Постоянная", "Циклическая", "Частотная", "Марковская", "Смешанная"]
    with st.sidebar:
        st.markdown("### Параметры игры")
        strategy_a = st.selectbox("Стратегия игрока A", strategies, index=3)
        strategy_b = st.selectbox("Стратегия игрока B", strategies, index=0)
        rounds = st.slider("Количество раундов", 100, 5000, 1000, 100)
        window = st.slider("Размер окна памяти", 5, 100, 30, 5)
        alpha = st.slider("Сглаживание вероятностей", 0.1, 5.0, 1.0, 0.1)
        seed = st.number_input("Seed", 0, 100000, 42, key="game_seed")
        run_game = st.button("Запустить матч", type="primary", use_container_width=True)
        run_tour = st.button("Провести турнир стратегий", use_container_width=True)

    if run_game:
        st.session_state["game_result"] = play_match(strategy_a, strategy_b, rounds,
            int(seed), alpha, window)
    if run_tour:
        with st.spinner("Проводим круговой турнир..."):
            st.session_state["tournament"] = run_tournament(strategies, rounds,
                int(seed), alpha, window)

    result = st.session_state.get("game_result")
    if result:
        st.markdown("#### 1. Результат матча")
        a,b,c,d = st.columns(4)
        a.metric("Победы A", result["wins_a"])
        b.metric("Победы B", result["wins_b"])
        c.metric("Ничьи", result["draws"])
        d.metric("Итоговый счёт A", result["score_a"], delta=result["score_a"]-result["score_b"])
        df = pd.DataFrame(result["history"])
        st.markdown("#### 2. Динамика счёта")
        st.line_chart(df.set_index("Раунд")[["Счёт A", "Счёт B"]], height=300)
        st.markdown("#### 3. Распределение ходов")
        dist = pd.concat([df["Ход A"].value_counts(normalize=True).rename("Игрок A"),
                          df["Ход B"].value_counts(normalize=True).rename("Игрок B")], axis=1).fillna(0)*100
        st.bar_chart(dist)
        st.markdown("#### 4. Последние раунды")
        st.dataframe(df.tail(30), use_container_width=True, hide_index=True)
        st.download_button("Скачать историю матча CSV", df.to_csv(index=False).encode("utf-8-sig"), "game_history.csv", "text/csv")

    tournament = st.session_state.get("tournament")
    if tournament:
        scores, details, ranking = tournament
        st.divider()
        st.markdown("#### Турнир: каждая стратегия против каждой")
        st.write("В каждой ячейке — средний баланс очков первой стратегии за раунд. Положительное значение означает преимущество строки над столбцом.")
        st.dataframe(scores.round(3), use_container_width=True)
        st.markdown("#### Рейтинг стратегий")
        st.bar_chart(ranking.set_index("Стратегия"))
        st.dataframe(ranking.round(3), use_container_width=True, hide_index=True)
        st.markdown("#### Подробности матчей")
        st.dataframe(details.round(2), use_container_width=True, hide_index=True)
    if not result and not tournament:
        st.info("Выберите две стратегии и запустите матч либо проведите полный турнир.")
    st.caption("Частотная стратегия отвечает на наиболее частый ход соперника. Марковская оценивает вероятности переходов между последовательными ходами. Смешанная использует вероятностную модель с равномерной примесью, поэтому её поведение менее детерминировано.")
