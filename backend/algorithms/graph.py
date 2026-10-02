import networkx as nx
import pandas as pd

from algorithms.shelter_selection import select_shelters


# ============================================================
# Configuration
# ============================================================

FLOOD_LAMBDA = 2.0
CONGESTION_LAMBDA = 1.0


# ============================================================
# Exact shelter capacities from the final Colab analysis
# ============================================================

SHELTER_CAPACITIES = {
    3: 19675,
    142: 10309,
    267: 26005,
    347: 28262,
    466: 18507,
    511: 14820,
    545: 19759,
    563: 24179,
    580: 24278,
    590: 20196,
    615: 24817,
    632: 24228,
    720: 16412,
    785: 10015,
    929: 26989,
    1026: 23871,
    1046: 13952,
    1116: 25664,
    1304: 19692,
    1405: 29433
}


# ============================================================
# Load graph
# ============================================================

def load_graph():

    # --------------------------------------------------------
    # Load CSV files
    # --------------------------------------------------------

    nodes = pd.read_csv("data/nodes.csv")
    roads = pd.read_csv("data/roads.csv")

    # --------------------------------------------------------
    # Select shelters using the FINAL Colab algorithm
    # --------------------------------------------------------

    selected_shelters = select_shelters(
        nodes,
        roads
    )

    print("\nSelected shelters:")
    print(sorted(selected_shelters))

    # --------------------------------------------------------
    # Verify selected shelters against expected shelters
    # --------------------------------------------------------

    expected_shelters = set(SHELTER_CAPACITIES.keys())
    actual_shelters = set(selected_shelters)

    if actual_shelters != expected_shelters:

        raise RuntimeError(
            "Shelter selection does not match the "
            "final Colab shelter configuration."
        )

    # --------------------------------------------------------
    # Create graph
    # --------------------------------------------------------

    G = nx.Graph()

    # --------------------------------------------------------
    # Add nodes
    # --------------------------------------------------------

    for _, row in nodes.iterrows():

        node_id = int(row["node_id"])

        # Shelter status comes from the final
        # shelter-selection algorithm
        is_shelter = node_id in selected_shelters

        # Assign the exact capacities used in Colab
        if is_shelter:
            shelter_capacity = SHELTER_CAPACITIES[node_id]
        else:
            shelter_capacity = 0

        G.add_node(
            node_id,

            x=float(row["x"]),

            y=float(row["y"]),

            population=int(
                row["population"]
            ),

            flood_risk=float(
                row["flood_risk"]
            ),

            is_shelter=is_shelter,

            shelter_capacity=shelter_capacity
        )

    # --------------------------------------------------------
    # Add roads
    # --------------------------------------------------------

    for _, row in roads.iterrows():

        source = int(
            row["source"]
        )

        destination = int(
            row["destination"]
        )

        distance = float(
            row["distance"]
        )

        road_capacity = float(
            row["road_capacity"]
        )

        flood_risk = float(
            row["flood_risk"]
        )

        # ----------------------------------------------------
        # Local population
        # ----------------------------------------------------

        local_population = (
            G.nodes[source]["population"]
            +
            G.nodes[destination]["population"]
        ) / 2

        # ----------------------------------------------------
        # Congestion
        # ----------------------------------------------------

        congestion_ratio = (
            local_population
            / road_capacity
        )

        congestion_factor = (
            1
            +
            CONGESTION_LAMBDA
            * congestion_ratio
        )

        # ----------------------------------------------------
        # Normal cost
        # ----------------------------------------------------

        normal_cost = distance

        # ----------------------------------------------------
        # Flood-aware cost
        # ----------------------------------------------------

        flood_cost = (
            distance
            *
            (
                1
                +
                FLOOD_LAMBDA
                * flood_risk
            )
        )

        # ----------------------------------------------------
        # Combined evacuation cost
        # ----------------------------------------------------

        evacuation_cost = (
            flood_cost
            *
            congestion_factor
        )

        G.add_edge(
            source,
            destination,

            distance=distance,

            road_capacity=road_capacity,

            flood_risk=flood_risk,

            local_population=local_population,

            congestion_ratio=congestion_ratio,

            congestion_factor=congestion_factor,

            normal_cost=normal_cost,

            flood_cost=flood_cost,

            evacuation_cost=evacuation_cost
        )

    return G


# ============================================================
# Get shelters
# ============================================================

def get_shelter_nodes(G):

    return [
        node
        for node, data in G.nodes(
            data=True
        )
        if data["is_shelter"]
    ]


# ============================================================
# Test graph
# ============================================================

if __name__ == "__main__":

    G = load_graph()

    shelters = get_shelter_nodes(G)

    print("\n========================================")
    print("GRAPH LOADED")
    print("========================================")

    print(
        "Nodes:",
        G.number_of_nodes()
    )

    print(
        "Roads:",
        G.number_of_edges()
    )

    print(
        "Shelters:",
        len(shelters)
    )

    print("\nShelter nodes:")

    print(
        sorted(shelters)
    )

    print("\nShelter capacities:")

    for shelter in sorted(shelters):

        print(
            f"Node {shelter}: "
            f"{G.nodes[shelter]['shelter_capacity']}"
        )

    print("\nNode 612:")

    print(
        G.nodes[612]
    )

    print("\nNode 1228:")

    print(
        G.nodes[1228]
    )