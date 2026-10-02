from algorithms.graph import load_graph
from algorithms.shelter_selection import select_shelters


# Load the exact graph
G = load_graph()

# Run shelter selection
shelters = select_shelters(G)

print("\n========================================")
print("GENERATED SHELTERS")
print("========================================")

print(sorted(shelters))

print("\nNumber of shelters:", len(shelters))

print("\nShelter details:")

for node in sorted(shelters):

    data = G.nodes[node]

    print(
        f"Node {node}: "
        f"flood_risk={data['flood_risk']:.3f}, "
        f"x={data['x']:.3f}, "
        f"y={data['y']:.3f}"
    )