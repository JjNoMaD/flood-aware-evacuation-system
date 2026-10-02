import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [network, setNetwork] = useState(null);
  const [shelters, setShelters] = useState(null);
  const [criticalJunctions, setCriticalJunctions] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);

  const [routeResult, setRouteResult] = useState(null);

  const [routeLoading, setRouteLoading] = useState(false);

  const [routeError, setRouteError] = useState("");

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState("");

  const [capacity, setCapacity] = useState(null);

  const [failureAnalysis, setFailureAnalysis] = useState(null);

  // Zoom and pan
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  useEffect(() => {
    async function loadData() {
      try {
        const [
    networkResponse,
    shelterResponse,
      capacityResponse
] = await Promise.all([
    axios.get("http://127.0.0.1:5000/api/network"),
    axios.get("http://127.0.0.1:5000/api/shelters"),
    axios.get("http://127.0.0.1:5000/api/capacity"),
]);
        setNetwork(networkResponse.data);
        setShelters(shelterResponse.data);
        setCapacity(capacityResponse.data);
        setFailureAnalysis(capacityResponse.data);
        setLoading(false);

        axios
          .get("http://127.0.0.1:5000/api/critical-junctions")
          .then((criticalResponse) => {
        console.log(
  "Critical Junctions:",
  criticalResponse.data
);

setCriticalJunctions(
  criticalResponse.data.critical_junctions || []
);
          })
          .catch((err) => {
            console.error("Could not load critical junctions.", err);
          });
      } catch (err) {
        console.error(err);
        setError("Could not connect to the Flask backend.");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // ---------------------------------------------------------
  // Loading
  // ---------------------------------------------------------

  if (loading) {
    return (
      <div className="loading-screen">
        <h1>Flood-Aware Evacuation System</h1>
        <p>Loading evacuation network...</p>
      </div>
    );
  }

  // ---------------------------------------------------------
  // Error
  // ---------------------------------------------------------

  if (error) {
    return (
      <div className="loading-screen">
        <h1>Flood-Aware Evacuation System</h1>
        <p>{error}</p>
      </div>
    );
  }

  // ---------------------------------------------------------
  // Node selection
  // ---------------------------------------------------------

  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };
  const findEvacuationRoute = async () => {

  if (!selectedNode) {
    setRouteError("Please select a starting node first.");
    return;
  }
  

  try {

    setRouteLoading(true);
    setRouteError("");
    setRouteResult(null);

    const response = await axios.post(
      "http://127.0.0.1:5000/api/route",
      {
        start_node: selectedNode.id
      }
    );

    setRouteResult(response.data);

  } catch (err) {

    console.error(err);

    setRouteError(
      err.response?.data?.error ||
      "Could not calculate evacuation route."
    );

  } finally {

    setRouteLoading(false);

  }
};
// =========================================================
// Route helper
// =========================================================

const isRouteEdge = (source, destination, path) => {

  if (!path || path.length < 2) {
    return false;
  }

  for (let i = 0; i < path.length - 1; i++) {

    const a = Number(path[i]);
    const b = Number(path[i + 1]);

    if (
      (a === source && b === destination) ||
      (a === destination && b === source)
    ) {
      return true;
    }
  }

  return false;
};
  // ---------------------------------------------------------
  // Zoom
  // ---------------------------------------------------------

  const handleWheel = (event) => {
    event.preventDefault();

    const zoomFactor = event.deltaY < 0 ? 1.15 : 0.87;

    setZoom((currentZoom) => {
      const newZoom = currentZoom * zoomFactor;

      return Math.min(
        Math.max(newZoom, 0.5),
        5
      );
    });
  };

  // ---------------------------------------------------------
  // Reset view
  // ---------------------------------------------------------

  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // ---------------------------------------------------------
  // Coordinate conversion
  // ---------------------------------------------------------

  const mapWidth = 900;
  const mapHeight = 650;

  const getX = (x) => {
    return x * mapWidth;
  };

  const getY = (y) => {
    return (1 - y) * mapHeight;
  };

  return (
    <div className="app">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <header className="top-header">

        <div>
          <h1>
            Flood-Aware Evacuation System
          </h1>

          <p>
            Graph-based evacuation route analysis
          </p>
        </div>

        <div className="header-status">
          <span></span>
          Network Online
        </div>

      </header>


      {/* =====================================================
          MAIN DASHBOARD
      ====================================================== */}

      <main>

        {/* Dashboard cards */}

        <div className="dashboard">

          <div className="stat-card">
            <div className="stat-value">
              {network.node_count}
            </div>

            <div className="stat-label">
              Road Nodes
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-value">
              {network.edge_count}
            </div>

            <div className="stat-label">
              Road Segments
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-value">
              {shelters.count}
            </div>

            <div className="stat-label">
              Evacuation Shelters
            </div>
          </div>

        {/* Capacity Analysis */}

        {capacity && (
          <>
            <div className="stat-card">
              <div className="stat-value">
                {capacity.normal_capacity.toFixed(2)}
              </div>

              <div className="stat-label">
                Normal Evacuation Capacity
              </div>
            </div>


            <div className="stat-card">
              <div className="stat-value">
                {capacity.flood_adjusted_capacity.toFixed(2)}
              </div>

              <div className="stat-label">
                Flood-Adjusted Capacity
              </div>
            </div>


            <div className="stat-card">
              <div className="stat-value">
                {capacity.flood_reduction_percent.toFixed(2)}%
              </div>

              <div className="stat-label">
                Capacity Reduction Due to Flood
              </div>
            </div>
            {failureAnalysis && (
  <div className="stat-card">
    <div className="stat-value">
      {failureAnalysis.failed_node}
    </div>

    <div className="stat-label">
      Failed Critical Junction
    </div>
  </div>
)}
{failureAnalysis && (
  <div className="stat-card">
    <div className="stat-value">
      {failureAnalysis.additional_loss_percent.toFixed(2)}%
    </div>

    <div className="stat-label">
      Additional Capacity Loss
    </div>
  </div>
)}
          </>
        )}

      
        </div>
        


        {/* ===================================================
            NETWORK MAP
        ==================================================== */}

        <div className="content-grid">

          <section className="map-panel">

            <div className="panel-header">

              <div>
                <h2>
                  Evacuation Network
                </h2>

                <p>
                  1,500 nodes · 3,654 road segments
                </p>
              </div>

              <button
                className="reset-button"
                onClick={resetView}
              >
                Reset View
              </button>

            </div>


            {/* Legend */}
<div className="legend">

  <div>
    <span className="legend-road"></span>
    Road
  </div>

  <div>
    <span className="legend-node"></span>
    Junction
  </div>

  <div>
    <span className="legend-shelter"></span>
    Shelter
  </div>

  <div>
    <span className="legend-normal"></span>
    Normal Route
  </div>

  <div>
    <span className="legend-flood"></span>
    Flood-Aware Route
  </div>

  <div>
    <span className="legend-combined"></span>
    Combined Route
  </div>

  <div>
    <span className="legend-start"></span>
    Start
  </div>

  <div>
    <span className="legend-recommended"></span>
    Recommended Shelter
  </div>

</div>


            {/* SVG network */}

            <div
              className="map-container"
              onWheel={handleWheel}
            >

              <svg
                viewBox={`0 0 ${mapWidth} ${mapHeight}`}
                className="network-svg"
              >

                <g
                  transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
                >

                  {/* -----------------------------------------
                      Roads
                  ------------------------------------------ */}

                  {network.edges.map((edge, index) => {

  const source = network.nodes.find(
    (node) => node.id === edge.source
  );

  const destination = network.nodes.find(
    (node) => node.id === edge.destination
  );

  if (!source || !destination) {
    return null;
  }

  const normal =
    routeResult?.normal_route?.path;

  const flood =
    routeResult?.flood_aware_route?.path;

  const combined =
    routeResult?.combined_route?.path;

  const isNormal = isRouteEdge(
    edge.source,
    edge.destination,
    normal
  );

  const isFlood = isRouteEdge(
    edge.source,
    edge.destination,
    flood
  );

  const isCombined = isRouteEdge(
    edge.source,
    edge.destination,
    combined
  );

  let lineClass = "road-line";

  if (isCombined) {
    lineClass = "route-combined";
  } else if (isFlood) {
    lineClass = "route-flood";
  } else if (isNormal) {
    lineClass = "route-normal";
  }

  return (
    <line
      key={index}
      x1={getX(source.x)}
      y1={getY(source.y)}
      x2={getX(destination.x)}
      y2={getY(destination.y)}
      className={lineClass}
    />
  );
})}

                  {/* -----------------------------------------
                      Nodes
                  ------------------------------------------ */}

                  {network.nodes.map((node) => {

                    const isShelter =
                      node.is_shelter;

                    const isSelected =
                      selectedNode &&
                      selectedNode.id === node.id;

                    const isRecommendedShelter =
    routeResult &&
    routeResult.recommended_shelter &&
    routeResult.recommended_shelter.id === node.id;

                    return (
  <g key={node.id}>

    {/* Node */}
    <circle
      cx={getX(node.x)}
      cy={getY(node.y)}
      r={
        isRecommendedShelter
          ? 8
          : isShelter
          ? 6
          : isSelected
          ? 5
          : 2
      }
      className={
        isRecommendedShelter
          ? "recommended-shelter-node"
          : isShelter
          ? "shelter-node"
          : isSelected
          ? "selected-node"
          : "normal-node"
      }
      onClick={() =>
        handleNodeClick(node)
      }
    />

    {/* Start label */}
    {isSelected && (
      <text
        x={getX(node.x)}
        y={getY(node.y) - 12}
        className="map-label start-label"
      >
        START
      </text>
    )}

    {/* Recommended shelter label */}
    {isRecommendedShelter && (
      <text
        x={getX(node.x)}
        y={getY(node.y) - 14}
        className="map-label shelter-label"
      >
        SHELTER {node.id}
      </text>
    )}

  </g>
);
                  })}

                </g>

              </svg>

            </div>

          </section>


          {/* =================================================
              NODE INFORMATION
          ================================================== */}

          <section className="info-panel">

            <h2>
              Node Information
            </h2>

            {!selectedNode ? (

              <div className="empty-state">

                <div className="empty-icon">
                  ●
                </div>

                <p>
                  Click a node on the network
                  to inspect it.
                </p>

              </div>

            ) : (

              <div className="node-details">

                <div className="node-title">
                  Node {selectedNode.id}
                </div>


                <div className="detail-row">
                  <span>Coordinates</span>
                  <strong>
                    {selectedNode.x.toFixed(3)},
                    {" "}
                    {selectedNode.y.toFixed(3)}
                  </strong>
                </div>


                <div className="detail-row">
                  <span>Population</span>
                  <strong>
                    {selectedNode.population.toLocaleString()}
                  </strong>
                </div>


                <div className="detail-row">
                  <span>Flood Risk</span>
                  <strong>
                    {selectedNode.flood_risk.toFixed(3)}
                  </strong>
                </div>


                <div className="detail-row">
                  <span>Node Type</span>
                  <strong>
                    {selectedNode.is_shelter
                      ? "Evacuation Shelter"
                      : "Road Junction"}
                  </strong>
                </div>


                {selectedNode.is_shelter && (

                  <div className="shelter-info">

                    <div>
                      Shelter Capacity
                    </div>

                    <strong>
                      {selectedNode.shelter_capacity.toLocaleString()}
                    </strong>

                  </div>

                )}
                <button
  className="route-button"
  onClick={findEvacuationRoute}
  disabled={routeLoading}
>
  {routeLoading
    ? "Calculating Route..."
    : "Find Evacuation Route"}
</button>
{routeError && (
  <div className="route-error">
    {routeError}
  </div>
)}

{routeResult && (
  <div className="route-result">

    <h3>Recommended Shelter</h3>

    <div className="recommended-shelter">

      <div className="shelter-number">
        Shelter {routeResult.recommended_shelter.id}
      </div>

      <p>
        Capacity:{" "}
        <strong>
          {routeResult.recommended_shelter.capacity.toLocaleString()}
        </strong>
      </p>

      <p>
        Flood Risk:{" "}
        <strong>
          {routeResult.recommended_shelter.flood_risk.toFixed(3)}
        </strong>
      </p>

    </div>


    <h3>Route Analysis</h3>


    <div className="route-card">

      <h4>Normal Route</h4>

      <p>
        Distance:{" "}
        {routeResult.normal_route.distance.toFixed(5)}
      </p>

      <p>
        Segments:{" "}
        {routeResult.normal_route.segments}
      </p>

      <p>
        Avg Flood Risk:{" "}
        {routeResult.normal_route.average_flood_risk.toFixed(3)}
      </p>

    </div>


    <div className="route-card">

      <h4>Flood-Aware Route</h4>

      <p>
        Distance:{" "}
        {routeResult.flood_aware_route.distance.toFixed(5)}
      </p>

      <p>
        Segments:{" "}
        {routeResult.flood_aware_route.segments}
      </p>

      <p>
        Avg Flood Risk:{" "}
        {routeResult.flood_aware_route.average_flood_risk.toFixed(3)}
      </p>

    </div>


    <div className="route-card combined">

      <h4>Combined Evacuation Route</h4>

      <p>
        Distance:{" "}
        {routeResult.combined_route.distance.toFixed(5)}
      </p>

      <p>
        Segments:{" "}
        {routeResult.combined_route.segments}
      </p>

      <p>
        Avg Flood Risk:{" "}
        {routeResult.combined_route.average_flood_risk.toFixed(3)}
      </p>

      <p>
        Avg Congestion:{" "}
        {routeResult.combined_route.average_congestion.toFixed(3)}
      </p>

    </div>

  </div>
)}
              </div>

            )}

          </section>

        </div>

      </main>
            {/* =====================================================
    CRITICAL JUNCTIONS
====================================================== */}

<section className="critical-panel">

  <div className="panel-header">
    <div>
      <h2>Critical Evacuation Junctions</h2>

      <p>
        High-betweenness junctions exposed to high flood risk
      </p>
    </div>

    <div className="critical-count">
      {criticalJunctions.length}
      <span> Critical Junctions</span>
    </div>
  </div>


  <div className="critical-info">

    <div>
      <span>Centrality Threshold</span>
      <strong>
        {criticalJunctions.length > 0
          ? "0.0624"
          : "—"}
      </strong>
    </div>

    <div>
      <span>Flood Risk Threshold</span>
      <strong>0.60</strong>
    </div>

  </div>


  <div className="critical-table">

    <div className="critical-row critical-header">

      <span>Node</span>

      <span>Betweenness</span>

      <span>Flood Risk</span>

      <span>Population</span>

    </div>


    {criticalJunctions
      .slice(0, 10)
      .map((junction) => (

        <div
          className="critical-row"
          key={junction.id}
        >

          <span>
            Node {junction.id}
          </span>

          <span>
            {junction.betweenness.toFixed(4)}
          </span>

          <span>
            {junction.flood_risk.toFixed(3)}
          </span>

          <span>
            {junction.population.toLocaleString()}
          </span>

        </div>

      ))}

  </div>

</section>
    </div>
  );
}

export default App;