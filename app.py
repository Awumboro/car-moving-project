import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import time
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Pro Logistics Master", layout="wide")

# 1. Session State to handle the "Live" movement
if 'points' not in st.session_state: st.session_state.points = []
if 'sim_active' not in st.session_state: st.session_state.sim_active = False
if 'current_idx' not in st.session_state: st.session_state.current_idx = 0
if 'telemetry_history' not in st.session_state: st.session_state.telemetry_history = []

st.title("🚗 Pro Logistics: Live Telemetry & Routing")

# 2. Sidebar Controls
with st.sidebar:
    st.header("1. Mission Setup")
    city = st.text_input("City Name", "Midtown, New York, USA")
    st.info("Click 2 points on the map: START then END.")
    
    if st.button("🔄 Reset Map"):
        for key in ['points', 'sim_active', 'current_idx', 'telemetry_history']:
            st.session_state[key] = ([] if 'points' in key or 'history' in key else 0 if 'idx' in key else False)
        st.rerun()

    st.header("2. Drive Settings")
    drive_speed = st.slider("Drive Speed (Delay)", 0.01, 1.0, 0.2)
    
    if len(st.session_state.points) == 2 and not st.session_state.sim_active:
        if st.button("🚀 Start Engine"):
            st.session_state.sim_active = True
            st.rerun()

# 3. Data Processing
@st.cache_data
def get_map_graph(location):
    return ox.graph_from_address(location, dist=1500, network_type='drive')

@st.cache_data
def get_best_route(_G, p1, p2):
    try:
        n1 = ox.distance.nearest_nodes(_G, X=p1[1], Y=p1[0])
        n2 = ox.distance.nearest_nodes(_G, X=p2[1], Y=p2[0])
        route = ox.shortest_path(_G, n1, n2, weight='length')
        return [[_G.nodes[n]['y'], _G.nodes[n]['x']] for n in route]
    except:
        return None

G = get_map_graph(city)

# 4. Map & UI Layout
col_map, col_graph = st.columns([2, 1])

# Determine current car position
route_coords = None
if len(st.session_state.points) == 2:
    route_coords = get_best_route(G, st.session_state.points[0], st.session_state.points[1])

# Setup Base Map
center = st.session_state.points[0] if st.session_state.points else [40.7580, -73.9855]
m = folium.Map(location=center, zoom_start=15, tiles="cartodbpositron")

# Draw Markers
for i, p in enumerate(st.session_state.points):
    folium.Marker(p, icon=folium.Icon(color='green' if i==0 else 'red')).add_to(m)

if route_coords:
    # Draw the static path
    folium.PolyLine(route_coords, color="blue", weight=3, opacity=0.5).add_to(m)
    
    # Draw the LIVE CAR
    idx = st.session_state.current_idx
    car_pos = route_coords[idx]
    folium.Marker(car_pos, icon=folium.Icon(color='red', icon='car', prefix='fa')).add_to(m)

# Display Map
with col_map:
    output = st_folium(m, width=800, height=600, key="master_map")

# Handle Clicks
if output['last_clicked'] and len(st.session_state.points) < 2 and not st.session_state.sim_active:
    st.session_state.points.append([output['last_clicked']['lat'], output['last_clicked']['lng']])
    st.rerun()

# 5. Live Simulation Loop
if st.session_state.sim_active and route_coords:
    if st.session_state.current_idx < len(route_coords) - 1:
        # Simulate data
        new_val = np.random.uniform(30, 60)
        st.session_state.telemetry_history.append(new_val)
        
        # Advance the car
        st.session_state.current_idx += 1
        time.sleep(drive_speed)
        st.rerun()
    else:
        st.success("Destination Reached!")
        st.session_state.sim_active = False

# 6. The Graph (Updates Live)
with col_graph:
    st.subheader("📊 Live Telemetry")
    if st.session_state.telemetry_history:
        fig = go.Figure(go.Scatter(y=st.session_state.telemetry_history, mode='lines', fill='tozeroy', line=dict(color='red')))
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        st.metric("Current Speed", f"{st.session_state.telemetry_history[-1]:.1f} km/h")
        st.metric("Progress", f"{st.session_state.current_idx}/{len(route_coords)}")