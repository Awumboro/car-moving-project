import streamlit as st
import osmnx as ox
import folium
import plotly.graph_objects as go
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Interactive Logistics Sim", layout="wide")

# 1. State Management
if 'points' not in st.session_state:
    st.session_state.points = []
if 'sim_ready' not in st.session_state:
    st.session_state.sim_ready = False

st.title("🚚 Interactive Logistics & Telemetry Simulator")

# 2. Sidebar
with st.sidebar:
    st.header("1. Setup")
    city = st.text_input("City Name", "Midtown, New York, USA")
    st.info("Click 2 points on the map: START (Green) then END (Red).")
    
    if st.button("🔄 Clear & Reset"):
        st.session_state.points = []
        st.session_state.sim_ready = False
        st.rerun()
        
    st.header("2. Simulation")
    speed_mult = st.slider("Seconds per node", 1, 10, 3)
    
    if len(st.session_state.points) == 2:
        if st.button("🚀 Deploy Vehicle"):
            st.session_state.sim_ready = True

# 3. Data Logic
@st.cache_data
def get_city_graph(location):
    # dist=1500 is a good balance for Manhattan
    return ox.graph_from_address(location, dist=1500, network_type='drive')

@st.cache_data
def calculate_route_and_telemetry(_G, p1, p2, step_sec):
    # p1 and p2 are [lat, lon]
    # Find nearest nodes using X, Y (Lon, Lat)
    orig_node = ox.distance.nearest_nodes(_G, X=p1[1], Y=p1[0])
    dest_node = ox.distance.nearest_nodes(_G, X=p2[1], Y=p2[0])
    
    # Calculate shortest path
    route = ox.shortest_path(_G, orig_node, dest_node, weight='length')
    
    # Extract coordinates correctly
    path_coords = []
    for node_id in route:
        node_data = _G.nodes[node_id]
        path_coords.append([node_data['y'], node_data['x']])
    
    # Telemetry and Times
    start_time = datetime(2026, 3, 10, 12, 0, 0)
    # Use the length of path_coords to ensure matching array sizes
    telemetry_values = np.random.normal(40, 5, len(path_coords)).tolist()
    times = [(start_time + timedelta(seconds=i * step_sec)).isoformat() for i in range(len(path_coords))]
    
    geojson = {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [[c[1], c[0]] for c in path_coords], # GeoJSON uses [Lon, Lat]
        },
        'properties': {
            'times': times,
            'icon': 'marker',
            'icon_options': {
                'icon': 'car', 
                'prefix': 'fa', 
                'markerColor': 'red'
            }
        }
    }
    return {'path': path_coords, 'geojson': geojson, 'telemetry': telemetry_values, 'times': times}

# 4. Map Logic
G = get_city_graph(city)
map_center = st.session_state.points[0] if st.session_state.points else [40.7580, -73.9855]
m = folium.Map(location=map_center, zoom_start=15, tiles="cartodbpositron")

# Draw selection markers
for i, pt in enumerate(st.session_state.points):
    color = 'green' if i == 0 else 'red'
    folium.Marker(pt, icon=folium.Icon(color=color, icon='info-sign')).add_to(m)

# If simulation is active, add layers
sim_data = None
if st.session_state.sim_ready and len(st.session_state.points) == 2:
    sim_data = calculate_route_and_telemetry(G, st.session_state.points[0], st.session_state.points[1], speed_mult)
    
    # The blue route line
    AntPath(locations=sim_data['path'], color='blue', weight=5, delay=4000).add_to(m)
    
    # The moving car
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': [sim_data['geojson']]},
        period='PT1S', 
        add_last_point=True, 
        auto_play=True, 
        loop=False
    ).add_to(m)

# Unified Map Display
output = st_folium(m, width=1300, height=550, key="unified_sim_map")

# Interaction logic
if output['last_clicked'] and not st.session_state.sim_ready:
    new_pt = [output['last_clicked']['lat'], output['last_clicked']['lng']]
    if len(st.session_state.points) < 2 and new_pt not in st.session_state.points:
        st.session_state.points.append(new_pt)
        st.rerun()

# 5. Dashboard Graph
if sim_data:
    st.subheader("📊 Vehicle Telemetry Dashboard")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sim_data['times'], 
        y=sim_data['telemetry'], 
        mode='lines',
        line=dict(color='firebrick', width=3),
        fill='tozeroy'
    ))
    fig.update_layout(
        xaxis_title="Simulation Time",
        yaxis_title="Speed (km/h)",
        height=300,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)