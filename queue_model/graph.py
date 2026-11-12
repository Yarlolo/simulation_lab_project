"""Graph representation of the bank service process."""
import networkx as nx
import matplotlib.pyplot as plt

def build_bank_graph(clerks=4):
    G = nx.DiGraph()
    nodes = [
        ("arrival", "Приход клиентов"),
        ("ticket", "Регистрация"),
        ("queue", "Общая очередь"),
    ]
    for node, label in nodes:
        G.add_node(node, label=label)
    G.add_node("exit", label="Выход")
    G.add_edge("arrival", "ticket")
    G.add_edge("ticket", "queue")
    for i in range(clerks):
        key = f"clerk_{i+1}"
        G.add_node(key, label=f"Окно {i+1}")
        G.add_edge("queue", key)
        G.add_edge(key, "exit")
    return G

def draw_bank_graph(clerks=4, ax=None):
    G = build_bank_graph(clerks)
    pos = {"arrival": (0, 1), "ticket": (1.5, 1), "queue": (3, 1), "exit": (7, 1)}
    for i in range(clerks):
        pos[f"clerk_{i+1}"] = (4.7, 1.7 - i * (1.4 / max(clerks-1, 1)))
    labels = nx.get_node_attributes(G, "label")
    if ax is None:
        _, ax = plt.subplots(figsize=(10, 4))
    nx.draw_networkx(G, pos, labels=labels, node_size=2300, node_color="#e8eef7",
                     edge_color="#607d9b", arrows=True, arrowsize=18,
                     font_size=8, ax=ax)
    ax.set_axis_off()
    return ax
