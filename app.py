import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import time
import numpy as np

st.set_page_config(page_title="Vehicle Tracker", layout="wide")

# 1. Session State Initialization
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'run_sim' not in st.session_state:
    st.session_state.run_sim = False

# 2. Sidebar Controls
with st.sidebar:
    st.title("🚗 Controller")
    place = st.text_input("Location", "Empire State Building, New York, USA")
    speed = st.slider("Step Delay", 0.1, 2.0, 0.5) # Increased min delay for cloud rendering
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Start"):
            st.session_state.run_sim = True
    with col2:
        if st.button("⏹ Stop"):
            st.session_state.run_sim = False
            
    if st.button("🔄 Reset"):
        st.session_state.current_step = 0
        st.session_state.run_sim = False
        st.rerun()

# 3. Data Loading
@st.cache_data
def get_route_data(location):
    try:
        G = ox.graph_from_address(location, dist=800, network_type='drive')
        nodes = list(G.nodes())
        route = ox.shortest_path(G, nodes[0], nodes[len(nodes)//2], weight='length')
        return [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]
    except:
        return None

coords = get_route_data(place)

if coords is None:
    st.error("Could not find address. Please check your spelling.")
    st.stop()

# 4. Telemetry Header
status_col1, status_col2, status_col3 = st.columns(3)
step = st.session_state.current_step
total = len(coords)

# Boundary check to prevent IndexError
if step >= total:
    step = total - 1
    st.session_state.run_sim = False

status_col1.metric("Progress", f"{step + 1} / {total}")
status_col2.metric("Speed", f"{np.random.uniform(20,50):.1f} km/h")
status_col3.metric("Battery", f"{max(0, 100 - (step * 100 // total))}%")

# 5. The Map (Optimized for Cloud)
def draw_map(current_step):
    current_loc = coords[current_step]
    m = folium.Map(location=current_loc, zoom_start=16, tiles="cartodbpositron")
    
    # Path trail (faded)
    folium.PolyLine(coords, color="blue", weight=2, opacity=0.2).add_to(m)
    
    # The Car
    folium.Marker(
        location=current_loc,
        icon=folium.Icon(color='red', icon='car', prefix='fa')
    ).add_to(m)
    
    st_folium(
        m, 
        key="vehicle_map",
        height=500, 
        width=1200, # Fill the screen
        returned_objects=[], # CRITICAL: stops the map from re-triggering logic
        use_container_width=True
    )

draw_map(step)

# 6. The Animation Trigger
if st.session_state.run_sim and st.session_state.current_step < total - 1:
    time.sleep(speed)
    st.session_state.current_step += 1
    st.rerun()
elif st.session_state.current_step >= total - 1:
    st.success("🏁 Destination Reached!")
    st.session_state.run_sim = False