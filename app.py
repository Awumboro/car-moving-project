import streamlit as st
import osmnx as ox
import folium
import plotly.graph_objects as go
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Interactive Logistics Sim", layout="wide")

# 1. State Management for O-D Selection
if 'points' not in st.session_state:
    st.session_state.points = []  # To store [[lat, lon], [lat, lon]]
if 'sim_ready' not in st.session_state:
    st.session_state.sim_ready = False

st.title("🚚 Interactive Logistics & Telemetry Simulator")

# 2. Sidebar Controls
with st.sidebar:
    st.header("1. Setup")
    city = st.text_input("City Name", "Midtown, New York, USA")
    st.info("Click two points on the map: First is START, Second is END.")
    
    if st.button("🔄 Clear Points"):
        st.session_state.points = []
        st.session_state.sim_ready = False
        st.rerun()
        
    st.header("2. Simulation")
    speed_mult = st.slider("Seconds per node", 1, 10, 3)
    
    if len(st.session_state.points) == 2:
        if st.button("🚀 Deploy Vehicle"):
            st.session_state.sim_ready = True

# 3. Data Processing Logic
@st.cache_data
def get_city_graph(location):
    # Just get the graph once and cache it
    return ox.graph_from_address(location, dist=1500, network_type='drive')

@st.cache_data
def calculate_route_and_telemetry(_G, p1, p2, step_sec):
    # Find nearest nodes to the click coordinates
    orig_node = ox.distance.nearest_nodes(_G, p1[1], p1[0])
    dest_node = ox.distance.nearest_nodes(_G, p2[1], p2[0])
    
    route = ox.shortest_path(_G, orig_node, dest_node, weight='length')
    
    path_coords = [[_G.nodes[n]['y'], _G.nodes[n]['x']] for n in route]
    start_time = datetime(2026, 3, 10, 12, 0, 0)
    
    # Generate fake sensor data (e.g. Speed/Vibration)
    telemetry_values = np.random.normal(40, 5, len(route)).tolist()
    
    times = [(start_time + timedelta(seconds=i * step_sec)).isoformat() for i in range(len(route))]
    
    geojson = {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [[c[1], c[0]] for c in path_coords],
        },
        'properties': {
            'times': times,
            'style': {'color': 'red', 'opacity': 0},
            'icon': 'marker',
            'icon_options': {
                'prefix': 'fa', 'icon': 'car', 'markerColor': 'red'
            }
        }
    }
    return {'path': path_coords, 'geojson': geojson, 'telemetry': telemetry_values, 'times': times}

# 4. Rendering
G = get_city_graph(city)
center = [st.session_state.points[0][0], st.session_state.points[0][1]] if st.session_state.points else [40.7580, -73.9855]

m = folium.Map(location=center, zoom_start=15, tiles="cartodbpositron")

# Handle User Clicks
output = st_folium(m, width=1300, height=500, key="selector_map")

if output['last_clicked'] and not st.session_state.sim_ready:
    new_point = [output['last_clicked']['lat'], output['last_clicked']['lng']]
    if new_point not in st.session_state.points:
        if len(st.session_state.points) < 2:
            st.session_state.points.append(new_point)
            st.rerun()

# Draw selected points
for i, pt in enumerate(st.session_state.points):
    color = 'green' if i == 0 else 'red'
    label = 'START' if i == 0 else 'END'
    folium.Marker(pt, popup=label, icon=folium.Icon(color=color)).add_to(m)

# 5. Simulation Overlay
if st.session_state.sim_ready and len(st.session_state.points) == 2:
    sim_data = calculate_route_and_telemetry(G, st.session_state.points[0], st.session_state.points[1], speed_mult)
    
    # Slower AntPath
    AntPath(locations=sim_data['path'], color='blue', weight=5, delay=3000).add_to(m) # delay 3000 = slower
    
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': [sim_data['geojson']]},
        period='PT1S', add_last_point=True, auto_play=True, loop=False
    ).add_to(m)

    # 6. Telemetry Graph
    st.subheader("📊 Live Telemetry (Vehicle Speed over Journey)")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim_data['times'], y=sim_data['telemetry'], mode='lines+markers', name="Speed (km/h)"))
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=300, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

# Re-render map with markers/simulation
st_folium(m, width=1300, height=500, key="sim_map_final")