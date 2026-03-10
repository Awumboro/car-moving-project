import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import time
import numpy as np

st.set_page_config(page_title="Vehicle Tracker", layout="wide")

# 1. Persistent State - This keeps the car's position saved
if 'current_step' not in st.session_state:
    st.session_state.current_step = 0
if 'run_sim' not in st.session_state:
    st.session_state.run_sim = False

# 2. Sidebar Settings
with st.sidebar:
    st.title("🚗 Controller")
    place = st.text_input("Location", "Empire State Building, New York, USA")
    speed = st.slider("Step Delay", 0.01, 1.0, 0.2)
    if st.button("🚀 Start / Resume"):
        st.session_state.run_sim = True
    if st.button("⏹ Stop"):
        st.session_state.run_sim = False
    if st.button("🔄 Reset"):
        st.session_state.current_step = 0
        st.session_state.run_sim = False

# 3. Data Loading (Cached)
@st.cache_data
def get_route_data(location):
    G = ox.graph_from_address(location, dist=800, network_type='drive')
    nodes = list(G.nodes())
    route = ox.shortest_path(G, nodes[0], nodes[len(nodes)//2], weight='length')
    return [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]

coords = get_route_data(place)

# 4. The Map Display Logic
def draw_map(step):
    current_loc = coords[step]
    
    # We fix the center and zoom so it doesn't "jump"
    m = folium.Map(location=current_loc, zoom_start=16)
    
    # Path trail
    folium.PolyLine(coords, color="blue", weight=2, opacity=0.3).add_to(m)
    
    # The Vehicle
    folium.Marker(
        location=current_loc,
        icon=folium.Icon(color='red', icon='car', prefix='fa')
    ).add_to(m)
    
    # RETURN_ON_HOVER=False and use_container_width=True help performance
    return st_folium(
        m, 
        key="vehicle_map",
        height=500, 
        width=1000,
        returned_objects=[] # This prevents the app from re-running when you click the map
    )

# 5. The Animation Loop
status = st.empty()

if st.session_state.run_sim:
    while st.session_state.current_step < len(coords) and st.session_state.run_sim:
        step = st.session_state.current_step
        
        status.metric("Speed", f"{np.random.uniform(20,50):.1f} km/h", f"Step {step}")
        
        draw_map(step)
        
        st.session_state.current_step += 1
        time.sleep(speed)
        st.rerun() # This is the "correct" way to animate in modern Streamlit
else:
    draw_map(st.session_state.current_step)
    status.write("Simulation Paused. Press Start to begin.")