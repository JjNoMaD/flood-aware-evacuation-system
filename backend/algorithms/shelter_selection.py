import networkx as nx
import numpy as np


# ============================================================
# FINAL SHELTER SELECTION PARAMETERS
# ============================================================

NUM_SHELTERS = 20

GRID_X = 5
GRID_Y = 4

MAX_SHELTER_FLOOD_RISK = 0.40

MIN_SHELTER_NETWORK_DISTANCE = 0.10

MIN_SHELTER_EUCLIDEAN_DISTANCE = 0.12


# ============================================================
# FINAL SHELTER SELECTION ALGORITHM
# ============================================================

def select_shelters(nodes_df, roads_df):

    # --------------------------------------------------------
    # 1. Build weighted road graph
    # --------------------------------------------------------

    G_shelter = nx.Graph()

    for _, row in nodes_df.iterrows():

        G_shelter.add_node(
            int(row["node_id"]),
            x=float(row["x"]),
            y=float(row["y"]),
            flood_risk=float(row["flood_risk"])
        )

    for _, row in roads_df.iterrows():

        G_shelter.add_edge(
            int(row["source"]),
            int(row["destination"]),
            distance=float(row["distance"])
        )

    # --------------------------------------------------------
    # 2. Low-risk candidate pool
    # --------------------------------------------------------

    shelter_candidates = nodes_df[
        nodes_df["flood_risk"] <= MAX_SHELTER_FLOOD_RISK
    ].copy()

    candidate_ids = (
        shelter_candidates["node_id"]
        .astype(int)
        .tolist()
    )

    print(
        f"Candidate shelter nodes: {len(candidate_ids)}"
    )

    # --------------------------------------------------------
    # 3. Create 20 spatial regions
    # --------------------------------------------------------

    regions = []

    for ix in range(GRID_X):

        for iy in range(GRID_Y):

            regions.append({
                "grid_x": ix,
                "grid_y": iy,
                "center_x": (ix + 0.5) / GRID_X,
                "center_y": (iy + 0.5) / GRID_Y
            })

    # --------------------------------------------------------
    # 4. Rank candidates for each region
    # --------------------------------------------------------

    region_candidates = {}

    for region_id, region in enumerate(regions):

        center_x = region["center_x"]
        center_y = region["center_y"]

        candidates = shelter_candidates.copy()

        # Distance from region center
        candidates["center_distance"] = np.sqrt(
            (candidates["x"] - center_x) ** 2
            +
            (candidates["y"] - center_y) ** 2
        )

        # Normalize center distance
        max_distance = candidates[
            "center_distance"
        ].max()

        if max_distance > 0:

            candidates["center_score"] = (
                candidates["center_distance"]
                / max_distance
            )

        else:

            candidates["center_score"] = 0

        # Normalize flood risk
        candidates["risk_score"] = (
            candidates["flood_risk"]
            / MAX_SHELTER_FLOOD_RISK
        )

        # Final score
        #
        # Lower score = better candidate
        candidates["base_score"] = (
            0.75 * candidates["center_score"]
            +
            0.25 * candidates["risk_score"]
        )

        candidates = candidates.sort_values(
            "base_score"
        )

        region_candidates[region_id] = (
            candidates["node_id"]
            .astype(int)
            .tolist()
        )

    # --------------------------------------------------------
    # 5. Select shelters with TWO separation rules
    # --------------------------------------------------------

    selected_shelters = []

    # Initially every candidate has infinite
    # minimum network distance.
    min_network_distance = {
        node: float("inf")
        for node in candidate_ids
    }

    # --------------------------------------------------------
    # Select one shelter for each of the 20 regions
    # --------------------------------------------------------

    for region_id in range(NUM_SHELTERS):

        candidates = region_candidates[region_id]

        valid_candidates = []

        for node in candidates:

            # Do not select the same node twice
            if node in selected_shelters:
                continue

            # ----------------------------------------------
            # Network separation
            # ----------------------------------------------

            network_ok = (
                min_network_distance[node]
                >= MIN_SHELTER_NETWORK_DISTANCE
            )

            # ----------------------------------------------
            # Geographical separation
            # ----------------------------------------------

            node_x = nodes_df.loc[
                nodes_df["node_id"] == node,
                "x"
            ].iloc[0]

            node_y = nodes_df.loc[
                nodes_df["node_id"] == node,
                "y"
            ].iloc[0]

            euclidean_ok = True

            for selected in selected_shelters:

                selected_x = nodes_df.loc[
                    nodes_df["node_id"] == selected,
                    "x"
                ].iloc[0]

                selected_y = nodes_df.loc[
                    nodes_df["node_id"] == selected,
                    "y"
                ].iloc[0]

                visual_distance = np.sqrt(
                    (node_x - selected_x) ** 2
                    +
                    (node_y - selected_y) ** 2
                )

                if (
                    visual_distance
                    < MIN_SHELTER_EUCLIDEAN_DISTANCE
                ):

                    euclidean_ok = False
                    break

            # Both constraints must be satisfied
            if network_ok and euclidean_ok:

                valid_candidates.append(node)

        # ----------------------------------------------------
        # Choose best valid candidate
        # ----------------------------------------------------

        if len(valid_candidates) > 0:

            selected_node = valid_candidates[0]

        else:

            # ------------------------------------------------
            # FALLBACK
            # ------------------------------------------------

            fallback_candidates = [
                node
                for node in candidates
                if node not in selected_shelters
            ]

            if len(fallback_candidates) == 0:

                raise RuntimeError(
                    "No unused shelter candidate available."
                )

            def fallback_score(node):

                if len(selected_shelters) == 0:
                    return float("inf")

                node_x = nodes_df.loc[
                    nodes_df["node_id"] == node,
                    "x"
                ].iloc[0]

                node_y = nodes_df.loc[
                    nodes_df["node_id"] == node,
                    "y"
                ].iloc[0]

                distances = []

                for selected in selected_shelters:

                    selected_x = nodes_df.loc[
                        nodes_df["node_id"] == selected,
                        "x"
                    ].iloc[0]

                    selected_y = nodes_df.loc[
                        nodes_df["node_id"] == selected,
                        "y"
                    ].iloc[0]

                    distances.append(
                        np.sqrt(
                            (node_x - selected_x) ** 2
                            +
                            (node_y - selected_y) ** 2
                        )
                    )

                return min(distances)

            selected_node = max(
                fallback_candidates,
                key=fallback_score
            )

        # Add selected shelter
        selected_shelters.append(
            int(selected_node)
        )

        # ----------------------------------------------------
        # Update network distances
        # ----------------------------------------------------

        new_network_distances = (
            nx.single_source_dijkstra_path_length(
                G_shelter,
                selected_node,
                weight="distance"
            )
        )

        for node in candidate_ids:

            if node in new_network_distances:

                min_network_distance[node] = min(
                    min_network_distance[node],
                    new_network_distances[node]
                )

    # --------------------------------------------------------
    # 6. Final check
    # --------------------------------------------------------

    if len(selected_shelters) != NUM_SHELTERS:

        raise RuntimeError(
            f"Expected {NUM_SHELTERS} shelters, "
            f"but selected {len(selected_shelters)}."
        )

    return selected_shelters