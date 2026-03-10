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
    st.info("Click 2 points: START (Green) then END (Red).")
    
    if st.button("🔄 Clear & Reset"):
        st.session_state.points = []
        st.session_state.sim_ready = False
        st.rerun()
        
    st.header("2. Simulation")
    speed_mult = st.slider("Seconds per node", 1, 10, 3)
    
    deploy = False
    if len(st.session_state.points) == 2:
        deploy = st.button("🚀 Deploy Vehicle")
        if deploy:
            st.session_state.sim_ready = True

# 3. Data Logic
@st.cache_data
def get_city_graph(location):
    return ox.graph_from_address(location, dist=1500, network_type='drive')

@st.cache_data
def calculate_route_and_telemetry(_G, p1, p2, step_sec):
    # Find nearest nodes (p[1] is lon, p[0] is lat)
    orig_node = ox.distance.nearest_nodes(_G, p1[1], p1[0])
    dest_node = ox.distance.nearest_nodes(_G, p2[1], p2[0])
    
    route = ox.shortest_path(_G, orig_node, dest_node, weight='length')
    path_coords = [[_G.nodes[n]['y'], _G.nodes[n]['x']] for n in route]
    
    # Telemetry and Times
    start_time = datetime(2026, 3, 10, 12, 0, 0)
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
            'icon': 'marker',
            'icon_options': {
                'icon': 'car', 'prefix': 'fa', 'markerColor': 'red'
            }
        }
    }
    return {'path': path_coords, 'geojson': geojson, 'telemetry': telemetry_values, 'times': times}

# 4. Map Construction (Single Call Logic)
G = get_city_graph(city)
# Center on the first point if selected, else the city
map_center = st.session_state.points[0] if st.session_state.points else [40.7580, -73.9855]
m = folium.Map(location=map_center, zoom_start=15, tiles="cartodbpositron")

# Draw current selection
for i, pt in enumerate(st.session_state.points):
    color = 'green' if i == 0 else 'red'
    folium.Marker(pt, icon=folium.Icon(color=color, icon='info-sign')).add_to(m)

# Add Simulation Layers if ready
sim_data = None
if st.session_state.sim_ready and len(st.session_state.points) == 2:
    sim_data = calculate_route_and_telemetry(G, st.session_state.points[0], st.session_state.points[1], speed_mult)
    
    AntPath(locations=sim_data['path'], color='blue', weight=5, delay=4000).add_to(m)
    
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': [sim_data['geojson']]},
        period='PT1S', add_last_point=True, auto_play=True, loop=False, duration='PT0S'
    ).add_to(m)

# ONE and ONLY ONE Map call
output = st_folium(m, width=1300, height=550, key="unified_map")

# Handle Click logic
if output['last_clicked'] and len(st.session_state.points) < 2 and not st.session_state.sim_ready:
    clicked_pt = [output['last_clicked']['lat'], output['last_clicked']['lng']]
    if clicked_pt not in st.session_state.points:
        st.session_state.points.append(clicked_pt)
        st.rerun()

# 5. Graph Display
if sim_data:
    st.subheader("📊 Live Telemetry")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim_data['times'], y=sim_data['telemetry'], 
                             line=dict(color='firebrick', width=3)))
    fig.update_layout(xaxis_title="Time", yaxis_title="Speed (km/h)", 
                      height=300, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)