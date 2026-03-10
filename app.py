import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import time
import numpy as np
import plotly.graph_objects as go

# 1. Setup & Session State
st.set_page_config(layout="wide")
if 'idx' not in st.session_state: st.session_state.idx = 0
if 'run' not in st.session_state: st.session_state.run = False
if 'points' not in st.session_state: st.session_state.points = []

st.title("🏎️ Live Sync: Map & Telemetry")

# 2. Sidebar & Data
with st.sidebar:
    city = st.text_input("City", "Midtown, New York, USA")
    delay = st.slider("Update Speed", 0.1, 1.0, 0.3)
    if st.button("🚀 Start Simulation"): st.session_state.run = True
    if st.button("🔄 Reset"): 
        st.session_state.idx = 0
        st.session_state.run = False
        st.session_state.points = []
        st.rerun()

@st.cache_data
def get_data(loc, p1, p2):
    G = ox.graph_from_address(loc, dist=1200, network_type='drive')
    n1 = ox.distance.nearest_nodes(G, p1[1], p1[0])
    n2 = ox.distance.nearest_nodes(G, p2[1], p2[0])
    route = ox.shortest_path(G, n1, n2, weight='length')
    coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]
    speeds = np.random.normal(40, 5, len(coords)).tolist()
    return coords, speeds

# 3. The "Fragment" - This is the secret for No-Flicker Live Plotting
@st.fragment
def run_simulation(coords, speeds):
    col1, col2 = st.columns([2, 1])
    
    # Progress the index if running
    if st.session_state.run and st.session_state.idx < len(coords) - 1:
        st.session_state.idx += 1
        time.sleep(delay)
        st.rerun()

    curr_idx = st.session_state.idx
    
    with col1:
        m = folium.Map(location=coords[curr_idx], zoom_start=16, tiles="cartodbpositron")
        # Route trail
        folium.PolyLine(coords, color="blue", weight=2, opacity=0.3).add_to(m)
        # Moving Car
        folium.Marker(coords[curr_idx], icon=folium.Icon(color='red', icon='car', prefix='fa')).add_to(m)
        st_folium(m, height=500, width=800, key=f"map_{curr_idx}")

    with col2:
        st.metric("Current Speed", f"{speeds[curr_idx]:.1f} km/h")
        # Plotly graph updates as idx increases
        fig = go.Figure(go.Scatter(y=speeds[:curr_idx+1], mode='lines+markers', fill='tozeroy'))
        fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

# 4. Main UI Logic
m_init = folium.Map(location=[40.758, -73.985], zoom_start=15)
if len(st.session_state.points) < 2:
    out = st_folium(m_init, height=500, width=1200, key="init")
    if out['last_clicked']:
        st.session_state.points.append([out['last_clicked']['lat'], out['last_clicked']['lng']])
        st.rerun()
else:
    coords, speeds = get_data(city, st.session_state.points[0], st.session_state.points[1])
    run_simulation(coords, speeds)