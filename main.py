from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import networkx as nx
from typing import List, Dict, Any

app = FastAPI(title="Routing with Rules KB")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Modelos ----
class RouteRequest(BaseModel):
    origin: str
    destination: str
    preferences: Dict[str, Any] = {}

class RouteStep(BaseModel):
    node: str
    info: Dict[str, Any] = {}

class RouteResponse(BaseModel):
    path: List[str]
    weight: float
    steps: List[RouteStep]
    applied_rules: List[str]

#BASE DE CONOCIMIENTOS DEL SISTEMA INTELIGENTE
def build_sample_graph():
    G = nx.Graph()
    # nodos = estaciones
    stations = ["A", "B", "C", "D", "E", "F", "G"]
    for s in stations:
        G.add_node(s, wheelchair=True)
    # aristas con atributos: travel_time (min), line, is_transfer (si conecta distintas líneas), weight por defecto = travel_time
    edges = [
        # Línea 1 (Roja) - Este a Oeste
        ("A1", "A2", {"travel_time": 4, "line": "L1", "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),
        ("A2", "A3", {"travel_time": 5, "line": "L1", "wheelchair": True, "crowded": True,  "safety": "medium", "cost": 0}),
        ("A3", "A4", {"travel_time": 6, "line": "L1", "wheelchair": False,"crowded": False, "safety": "high", "cost": 0}),
        ("A4", "A5", {"travel_time": 7, "line": "L1", "wheelchair": True, "crowded": True,  "safety": "low", "cost": 0}),
        ("A5", "A6", {"travel_time": 5, "line": "L1", "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),

        # Línea 2 (Azul) - Norte a Sur
        ("B1", "B2", {"travel_time": 5, "line": "L2", "wheelchair": True, "crowded": True,  "safety": "medium", "cost": 0}),
        ("B2", "B3", {"travel_time": 8, "line": "L2", "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),
        ("B3", "B4", {"travel_time": 6, "line": "L2", "wheelchair": False,"crowded": True,  "safety": "low", "cost": 0}),
        ("B4", "B5", {"travel_time": 7, "line": "L2", "wheelchair": True, "crowded": False, "safety": "medium", "cost": 0}),
        ("B5", "B6", {"travel_time": 5, "line": "L2", "wheelchair": True, "crowded": True,  "safety": "high", "cost": 0}),

        # Línea 3 (Verde) - Diagonal
        ("C1", "C2", {"travel_time": 4, "line": "L3", "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),
        ("C2", "C3", {"travel_time": 7, "line": "L3", "wheelchair": True, "crowded": True,  "safety": "medium", "cost": 0}),
        ("C3", "C4", {"travel_time": 5, "line": "L3", "wheelchair": False,"crowded": False, "safety": "low", "cost": 0}),
        ("C4", "C5", {"travel_time": 8, "line": "L3", "wheelchair": True, "crowded": True,  "safety": "medium", "cost": 0}),
        ("C5", "C6", {"travel_time": 6, "line": "L3", "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),

        # Línea 4 (Amarilla) - Circular
        ("D1", "D2", {"travel_time": 5, "line": "L4", "wheelchair": True, "crowded": True,  "safety": "medium", "cost": 500}),
        ("D2", "D3", {"travel_time": 6, "line": "L4", "wheelchair": True, "crowded": False, "safety": "high", "cost": 500}),
        ("D3", "D4", {"travel_time": 5, "line": "L4", "wheelchair": True, "crowded": True,  "safety": "low", "cost": 500}),
        ("D4", "D1", {"travel_time": 7, "line": "L4", "wheelchair": True, "crowded": False, "safety": "high", "cost": 500}),

        # Conexiones entre líneas (transferencias)
        ("A3", "B2", {"travel_time": 3, "line": "X", "is_transfer": True, "wheelchair": True, "crowded": True, "safety": "medium", "cost": 0}),
        ("B4", "C3", {"travel_time": 4, "line": "X", "is_transfer": True, "wheelchair": False,"crowded": False, "safety": "low", "cost": 0}),
        ("C5", "D2", {"travel_time": 5, "line": "X", "is_transfer": True, "wheelchair": True, "crowded": True,  "safety": "medium", "cost": 0}),
        ("A6", "D4", {"travel_time": 6, "line": "X", "is_transfer": True, "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),

        # Línea 5 (Naranja) - corta
        ("E1", "E2", {"travel_time": 4, "line": "L5", "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),
        ("E2", "E3", {"travel_time": 6, "line": "L5", "wheelchair": True, "crowded": True, "safety": "medium", "cost": 0}),

        # Conexión entre líneas
        ("C6", "E1", {"travel_time": 5, "line": "X", "is_transfer": True, "wheelchair": True, "crowded": False, "safety": "high", "cost": 0}),
        ("D3", "E2", {"travel_time": 7, "line": "X", "is_transfer": True, "wheelchair": True, "crowded": True, "safety": "medium", "cost": 0}),

    ]

    for u,v,attrs in edges:
        attrs.setdefault("is_transfer", False)
        attrs.setdefault("weight", attrs["travel_time"])
        G.add_edge(u, v, **attrs)
    return G

GRAPH = build_sample_graph()

# ---- Motor de reglas simple ----
class RuleEngine:

    def __init__(self):
        self.rules = []
        self.applied = []

    def add_rule(self, name, func):
        self.rules.append((name, func))

    def run(self, graph: nx.Graph, context: dict):
        G = graph.copy()
        self.applied = []
        for name, rule in self.rules:
            changed = rule(G, context)
            if changed:
                self.applied.append(name)
        return G

# ---- Reglas de ejemplo ----
def rule_avoid_transfers(graph: nx.Graph, ctx: dict):
    if not ctx.get("avoid_transfers"): 
        return False
    # incrementar peso de aristas que son transferencias para desincentivar
    changed = False
    for u,v,data in graph.edges(data=True):
        if data.get("is_transfer"):
            data["weight"] = data.get("weight", data.get("travel_time",1)) + 30  # penaliza fuertemente
            changed = True
    return changed

def rule_wheelchair_only(graph: nx.Graph, ctx: dict):
    if not ctx.get("wheelchair"):
        return False
    # si hay nodos sin accesibilidad, removerlos (y aristas)
    removed = False
    for n,data in list(graph.nodes(data=True)):
        if not data.get("wheelchair", False):
            graph.remove_node(n)
            removed = True
    return removed

def rule_prefer_fastest(graph: nx.Graph, ctx: dict):
    if ctx.get("prefer_fastest") is False:
        for u,v,data in graph.edges(data=True):
            data["weight"] = data.get("weight", data.get("travel_time",1)) + (10 if data.get("is_transfer") else 0)
        return True
    return False

def rule_avoid_crowded(graph: nx.Graph, ctx: dict):
    """Penaliza tramos con mucha congestión."""
    if not ctx.get("avoid_crowded"):
        return False
    changed = False
    for u, v, data in graph.edges(data=True):
        if data.get("crowded"):
            data["weight"] = data.get("weight", data["travel_time"]) + 15
            changed = True
    return changed


def rule_prioritize_safety(graph: nx.Graph, ctx: dict):
    """Penaliza tramos con baja seguridad si el usuario lo pide."""
    if not ctx.get("safe_priority"):
        return False
    changed = False
    for u, v, data in graph.edges(data=True):
        if data.get("safety") == "low":
            data["weight"] = data.get("weight", data["travel_time"]) + 20
            changed = True
        elif data.get("safety") == "medium":
            data["weight"] = data.get("weight", data["travel_time"]) + 5
            changed = True
    return changed


def rule_budget_constraint(graph: nx.Graph, ctx: dict):
    """Evita rutas que sobrepasen un presupuesto (si se define)."""
    budget = ctx.get("budget")
    if budget is None:
        return False
    changed = False
    # Si una arista tiene costo mayor que el presupuesto permitido, la eliminamos
    for u, v, data in list(graph.edges(data=True)):
        if data.get("cost", 0) > budget:
            graph.remove_edge(u, v)
            changed = True
    return changed


# crear motor y registrar reglas
engine = RuleEngine()
engine.add_rule("avoid_transfers", rule_avoid_transfers)
engine.add_rule("wheelchair_only", rule_wheelchair_only)
engine.add_rule("prefer_fastest_toggle", rule_prefer_fastest)
engine.add_rule("avoid_crowded", rule_avoid_crowded)
engine.add_rule("prioritize_safety", rule_prioritize_safety)
engine.add_rule("budget_constraint", rule_budget_constraint)

# ---- Endpoint principal ----
@app.post("/route", response_model=RouteResponse)
def compute_route(req: RouteRequest):
    origin = req.origin
    dest = req.destination
    prefs = req.preferences or {}

    # aplicar reglas (motor de inferencia)
    modified_graph = engine.run(GRAPH, prefs)

    # validar nodos después de aplicar reglas
    if origin not in modified_graph.nodes:
        return {
            "path": [],
            "weight": 0,
            "steps": [],
            "applied_rules": engine.applied,
            "detail": f"Origin {origin} is not accessible under current rules"
        }
    if dest not in modified_graph.nodes:
        return {
            "path": [],
            "weight": 0,
            "steps": [],
            "applied_rules": engine.applied,
            "detail": f"Destination {dest} is not accessible under current rules"
        }

    # búsqueda: Dijkstra por peso
    try:
        path = nx.shortest_path(modified_graph, origin, dest, weight="weight")
        weight = nx.shortest_path_length(modified_graph, origin, dest, weight="weight")
    except nx.NetworkXNoPath:
        return {
            "path": [],
            "weight": 0,
            "steps": [],
            "applied_rules": engine.applied,
            "detail": f"No path between {origin} and {dest} under current rules"
        }

    steps = [{"node": n, "info": dict(modified_graph.nodes[n])} for n in path]

    return {
        "path": path,
        "weight": float(weight),
        "steps": steps,
        "applied_rules": engine.applied,
    }

@app.get("/graph")
def get_graph():
    nodes = {n: dict(GRAPH.nodes[n]) for n in GRAPH.nodes}
    edges = []
    for u,v,d in GRAPH.edges(data=True):
        edges.append({"u":u,"v":v,"d":d})
    return {"nodes": nodes, "edges": edges}
