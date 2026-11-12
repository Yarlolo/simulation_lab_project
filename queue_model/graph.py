"""Graph representation and visualization of the bank service process."""
import networkx as nx
import matplotlib.pyplot as plt


def build_bank_graph(clerks=4):
    graph = nx.DiGraph()
    graph.add_node("arrival", label="Поступление\nклиентов", kind="source")
    graph.add_node("ticket", label="Регистрация", kind="process")
    graph.add_node("queue", label="Общая очередь", kind="queue")
    graph.add_node("exit", label="Выход", kind="sink")
    graph.add_edges_from([("arrival", "ticket"), ("ticket", "queue")])
    for i in range(clerks):
        key = f"clerk_{i+1}"
        graph.add_node(key, label=f"Окно {i+1}\nобслуживания", kind="server")
        graph.add_edge("queue", key)
        graph.add_edge(key, "exit")
    return graph


def draw_bank_graph(clerks=4, ax=None, queue_count=None, busy_count=None):
    graph = build_bank_graph(clerks)
    if ax is None:
        _, ax = plt.subplots(figsize=(12, 4.8))
    pos = {"arrival": (0, 0), "ticket": (2, 0), "queue": (4, 0), "exit": (9, 0)}
    ys = [1.65 - i * (3.3 / max(clerks-1, 1)) for i in range(clerks)]
    for i, y in enumerate(ys):
        pos[f"clerk_{i+1}"] = (6.5, y)
    colors = {"source": "#DCEAFE", "process": "#E8E5FF", "queue": "#FFF0CC",
              "server": "#DDF4E4", "sink": "#FCE2E2"}
    node_colors = []
    for n in graph.nodes:
        kind = graph.nodes[n]["kind"]
        color = colors[kind]
        if n == "queue" and queue_count is not None and queue_count > 0:
            color = "#F59E0B"
        if kind == "server" and busy_count is not None:
            server_no = int(n.split("_")[1])
            color = "#16A34A" if server_no <= busy_count else "#DDF4E4"
        node_colors.append(color)
    labels = nx.get_node_attributes(graph, "label")
    nx.draw_networkx(graph, pos, labels=labels, node_color=node_colors,
                     node_size=3000, edge_color="#64748B", arrows=True,
                     arrowsize=20, width=1.8, font_size=8.5,
                     connectionstyle="arc3,rad=0.03", ax=ax)
    ax.set_title("Маршрут клиента через систему банка", fontsize=13, pad=16, weight="bold")
    ax.text(4, -1.15, "Клиент ожидает, пока освободится любое окно", ha="center",
            fontsize=9, color="#475569")
    ax.set_xlim(-1, 10)
    ax.set_ylim(-1.55, 2.45)
    ax.axis("off")
    return ax
