import networkx as nx
from flask import Flask, jsonify, request
from flask_cors import CORS

from algorithms.graph import load_graph, get_shelter_nodes


# ============================================================
# Flask application
# ============================================================

app = Flask(__name__)

# Allow requests from React/Vite
CORS(app)


# ============================================================
# Load the verified graph once when the backend starts
# ============================================================

print("\nLoading evacuation network...")

G = load_graph()

print("Evacuation network loaded successfully.")


# ============================================================
# Home route
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Flood-Aware Evacuation Backend",
        "status": "running"
    })


# ============================================================
# Network information
# ============================================================

@app.route("/api/network", methods=["GET"])
def network():

    nodes = []

    for node_id, data in G.nodes(data=True):

        nodes.append({
            "id": int(node_id),
            "x": data["x"],
            "y": data["y"],
            "population": data["population"],
            "flood_risk": data["flood_risk"],
            "is_shelter": data["is_shelter"],
            "shelter_capacity": data["shelter_capacity"]
        })

    edges = []

    for source, destination, data in G.edges(data=True):

        edges.append({
            "source": int(source),
            "destination": int(destination),
            "distance": data["distance"],
            "road_capacity": data["road_capacity"],
            "flood_risk": data["flood_risk"]
        })

    return jsonify({
        "nodes": nodes,
        "edges": edges,
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges()
    })


# ============================================================
# Shelter information
# ============================================================

@app.route("/api/shelters", methods=["GET"])
def shelters():

    shelter_nodes = get_shelter_nodes(G)

    result = []

    for node in shelter_nodes:

        data = G.nodes[node]

        result.append({
            "id": int(node),
            "x": data["x"],
            "y": data["y"],
            "population": data["population"],
            "flood_risk": data["flood_risk"],
            "capacity": data["shelter_capacity"]
        })

    return jsonify({
        "count": len(result),
        "shelters": result
    })
# ============================================================
# Critical Junction Analysis
# ============================================================

@app.route("/api/critical-junctions", methods=["GET"])
def critical_junctions():

    # --------------------------------------------------------
    # Calculate betweenness centrality
    # --------------------------------------------------------

    betweenness = nx.betweenness_centrality(
        G,
        weight="distance",
        normalized=True
    )

    # --------------------------------------------------------
    # Top 5% centrality threshold
    # --------------------------------------------------------

    centrality_values = list(betweenness.values())

    centrality_threshold = sorted(
        centrality_values
    )[int(0.95 * len(centrality_values))]

    # --------------------------------------------------------
    # Flood-risk threshold
    # --------------------------------------------------------

    flood_threshold = 0.60

    # --------------------------------------------------------
    # Identify critical junctions
    # --------------------------------------------------------

    critical = []

    for node, centrality in betweenness.items():

        data = G.nodes[node]

        if (
            centrality >= centrality_threshold
            and
            data["flood_risk"] >= flood_threshold
        ):

            critical.append({
                "id": int(node),
                "x": data["x"],
                "y": data["y"],
                "population": data["population"],
                "flood_risk": data["flood_risk"],
                "betweenness": centrality
            })

    # --------------------------------------------------------
    # Sort by betweenness centrality
    # --------------------------------------------------------

    critical.sort(
        key=lambda x: x["betweenness"],
        reverse=True
    )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return jsonify({
        "count": len(critical),
        "centrality_threshold": centrality_threshold,
        "flood_threshold": flood_threshold,
        "critical_junctions": critical
    })
# ============================================================
# Route calculation
# ============================================================

@app.route("/api/route", methods=["POST"])
def calculate_route():

    data = request.get_json()

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if not data or "start_node" not in data:
        return jsonify({
            "error": "start_node is required"
        }), 400

    try:
        start_node = int(data["start_node"])
    except (ValueError, TypeError):

        return jsonify({
            "error": "start_node must be an integer"
        }), 400

    # --------------------------------------------------------
    # Check whether node exists
    # --------------------------------------------------------

    if start_node not in G:

        return jsonify({
            "error": f"Node {start_node} does not exist"
        }), 404

    # --------------------------------------------------------
    # Get shelters
    # --------------------------------------------------------

    shelter_nodes = get_shelter_nodes(G)

    if not shelter_nodes:

        return jsonify({
            "error": "No shelters available"
        }), 500

    # --------------------------------------------------------
    # Find best shelter using combined evacuation cost
    # --------------------------------------------------------

    best_shelter = None
    best_cost = float("inf")

    for shelter in shelter_nodes:

        try:

            cost = nx.shortest_path_length(
                G,
                source=start_node,
                target=shelter,
                weight="evacuation_cost"
            )

            if cost < best_cost:

                best_cost = cost
                best_shelter = shelter

        except nx.NetworkXNoPath:

            continue

    # --------------------------------------------------------
    # Check if a shelter is reachable
    # --------------------------------------------------------

    if best_shelter is None:

        return jsonify({
            "error": "No reachable shelter found"
        }), 404

    # --------------------------------------------------------
    # Calculate the three routes
    # --------------------------------------------------------

    normal_path = nx.shortest_path(
        G,
        source=start_node,
        target=best_shelter,
        weight="normal_cost"
    )

    flood_path = nx.shortest_path(
        G,
        source=start_node,
        target=best_shelter,
        weight="flood_cost"
    )

    evacuation_path = nx.shortest_path(
        G,
        source=start_node,
        target=best_shelter,
        weight="evacuation_cost"
    )

    # --------------------------------------------------------
    # Calculate route statistics
    # --------------------------------------------------------

    def route_statistics(path):

        total_distance = 0
        flood_risks = []
        congestion_ratios = []

        for i in range(len(path) - 1):

            u = path[i]
            v = path[i + 1]

            edge = G[u][v]

            total_distance += edge["distance"]

            flood_risks.append(
                edge["flood_risk"]
            )

            congestion_ratios.append(
                edge["congestion_ratio"]
            )

        return {
            "distance": total_distance,

            "average_flood_risk": (
                sum(flood_risks) / len(flood_risks)
                if flood_risks
                else 0
            ),

            "maximum_flood_risk": (
                max(flood_risks)
                if flood_risks
                else 0
            ),

            "average_congestion": (
                sum(congestion_ratios)
                / len(congestion_ratios)
                if congestion_ratios
                else 0
            ),

            "maximum_congestion": (
                max(congestion_ratios)
                if congestion_ratios
                else 0
            ),

            "segments": len(path) - 1
        }

    # --------------------------------------------------------
    # Get statistics
    # --------------------------------------------------------

    normal_stats = route_statistics(
        normal_path
    )

    flood_stats = route_statistics(
        flood_path
    )

    evacuation_stats = route_statistics(
        evacuation_path
    )

    # --------------------------------------------------------
    # Shelter information
    # --------------------------------------------------------

    shelter_data = G.nodes[best_shelter]

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return jsonify({

        "start_node": start_node,

        "recommended_shelter": {
            "id": int(best_shelter),
            "x": shelter_data["x"],
            "y": shelter_data["y"],
            "flood_risk": shelter_data["flood_risk"],
            "capacity": shelter_data["shelter_capacity"]
        },

        "normal_route": {
            "path": normal_path,
            **normal_stats
        },

        "flood_aware_route": {
            "path": flood_path,
            **flood_stats
        },

        "combined_route": {
            "path": evacuation_path,
            **evacuation_stats
        }

    })
# ============================================================
# Run Flask server
# ============================================================
# =========================================================
# EVACUATION CAPACITY ANALYSIS
# =========================================================

@app.route("/api/capacity", methods=["GET"])
def capacity_analysis():

    # Normal network maximum evacuation flow
    normal_capacity = 6840.00

    # Flood-adjusted network maximum evacuation flow
    flood_capacity = 1911.15

    # Capacity reduction caused by modeled flooding
    flood_reduction = (
        (normal_capacity - flood_capacity)
        / normal_capacity
        * 100
    )

    # Critical junction failure analysis
    failed_node = 1228

    failure_capacity = 1481.36

    additional_loss = (
        (flood_capacity - failure_capacity)
        / flood_capacity
        * 100
    )

    return jsonify({
        "normal_capacity": normal_capacity,
        "flood_adjusted_capacity": flood_capacity,
        "flood_reduction_percent": round(flood_reduction, 2),

        "failed_node": failed_node,
        "failure_capacity": failure_capacity,
        "additional_loss_percent": round(additional_loss, 2)
    })


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )