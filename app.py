import streamlit as st
import osmnx as ox
import folium
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go

# Set page to wide mode for better visualization
st.set_page_config(page_title="Stable Pro Logistics", layout="wide")

# Inject FontAwesome so the 'car' icon actually renders
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)

# Initialize Session State
if 'points' not in st.session_state: st.session_state.points = []
if 'sim_ready' not in st.session_state: st.session_state.sim_ready = False

st.title("🚚 Stable Logistics & Telemetry Simulator")

# --- 1. SIDEBAR SETUP ---
with st.sidebar:
    st.header("1. Setup")
    city = st.text_input("City Name", "Midtown, New York, USA")
    st.info("Click 2 points on the map: START (Green) then END (Red).")
    
    if st.button("🔄 Clear & Reset"):
        st.session_state.points = []
        st.session_state.sim_ready = False
        st.rerun()
        
    st.header("2. Simulation")
    step_sec = st.slider("Seconds per node", 1, 10, 3)
    
    if len(st.session_state.points) == 2:
        if st.button("🚀 Deploy Vehicle"):
            st.session_state.sim_ready = True

# --- 2. DATA PROCESSING ---
@st.cache_data
def get_map_graph(location):
    # Fetch driving network
    return ox.graph_from_address(location, dist=1500, network_type='drive')

@st.cache_data
def prepare_simulation_data(_G, p1, p2, speed):
    try:
        # Find nearest nodes to clicked points
        n1 = ox.distance.nearest_nodes(_G, X=p1[1], Y=p1[0])
        n2 = ox.distance.nearest_nodes(_G, X=p2[1], Y=p2[0])
        
        # Calculate shortest path
        route = ox.shortest_path(_G, n1, n2, weight='length')
        
        path_coords = []
        for n in route:
            node_data = _G.nodes[n]
            path_coords.append([node_data['y'], node_data['x']])
            
        start_time = datetime(2026, 3, 10, 12, 0, 0)
        times = [(start_time + timedelta(seconds=i * speed)).isoformat() for i in range(len(route))]
        
        # Simulated Telemetry (Speed)
        speeds = np.random.normal(40, 5, len(route)).tolist()
        
        # GEOJSON for the moving marker
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
                    'prefix': 'fa', 
                    'icon': 'car', 
                    'markerColor': 'red', 
                    'iconColor': 'white'
                }
            }
        }
        return {'path': path_coords, 'geojson': geojson, 'speeds': speeds, 'times': times}
    except Exception as e:
        return f"Routing Error: {str(e)}"

# --- 3. MAP CONSTRUCTION ---
G = get_map_graph(city)
# Determine map center: either the first clicked point or a default
center = st.session_state.points[0] if st.session_state.points else [40.7580, -73.9855]
m = folium.Map(location=center, zoom_start=15, tiles="cartodbpositron")

# Draw selection markers (Green for Start, Red for End)
for i, p in enumerate(st.session_state.points):
    color = 'green' if i == 0 else 'red'
    folium.Marker(p, icon=folium.Icon(color=color, icon='info-sign')).add_to(m)

sim_data = None
if st.session_state.sim_ready and len(st.session_state.points) == 2:
    result = prepare_simulation_data(G, st.session_state.points[0], st.session_state.points[1], step_sec)
    
    if isinstance(result, str):
        st.error(result)
        st.session_state.sim_ready = False
    else:
        sim_data = result
        # The blue flowing route line
        AntPath(locations=sim_data['path'], color='blue', weight=5, delay=4000).add_to(m)
        
        # The moving car (JavaScript-based animation)
        TimestampedGeoJson(
            {'type': 'FeatureCollection', 'features': [sim_data['geojson']]},
            period='PT1S', 
            add_last_point=True, 
            auto_play=True, 
            loop=False,
            duration='PT0S' # Keeps only current marker visible
        ).add_to(m)

# DISPLAY MAP
output = st_folium(m, width=1300, height=550, key="master_logistics_map")

# Handle Click logic (Disabled if simulation is running)
if output['last_clicked'] and len(st.session_state.points) < 2 and not st.session_state.sim_ready:
    clicked_pt = [output['last_clicked']['lat'], output['last_clicked']['lng']]
    if clicked_pt not in st.session_state.points:
        st.session_state.points.append(clicked_pt)
        st.rerun()

# --- 4. TELEMETRY GRAPH ---
if sim_data:
    st.subheader("📊 Trip Telemetry Dashboard")
    
    # Calculate some summary stats for the user
    total_nodes = len(sim_data['path'])
    avg_speed = np.mean(sim_data['speeds'])
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        fig = go.Figure(go.Scatter(
            x=sim_data['times'], 
            y=sim_data['speeds'], 
            fill='tozeroy', 
            line=dict(color='firebrick', width=3),
            name="Vehicle Speed"
        ))
        fig.update_layout(
            height=300, 
            margin=dict(l=0, r=0, t=20, b=0), 
            xaxis_title="Simulation Time", 
            yaxis_title="Speed (km/h)"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("Total Nodes", total_nodes)
        st.metric("Avg Speed", f"{avg_speed:.1f} km/h")
        st.success("Simulation Active")

st.caption("Instructions: 1. Click two points on the map. 2. Hit 'Deploy Vehicle' in the sidebar.")