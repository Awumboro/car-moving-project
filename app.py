import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import time
import numpy as np

# Page setup
st.set_page_config(page_title="Vehicle Tracker", layout="wide")
st.title("🚗 Interactive Vehicle Route Simulator")

# 1. Sidebar Inputs
with st.sidebar:
    st.header("Settings")
    place = st.text_input("Location", "Empire State Building, New York, USA")
    speed = st.slider("Simulation Speed (sec/step)", 0.1, 1.0, 0.3)
    run_btn = st.button("🚀 Launch Simulation")

# 2. Map & Route Logic (Cached for speed)
@st.cache_data
def get_route(location):
    G = ox.graph_from_address(location, dist=800, network_type='drive')
    nodes = list(G.nodes())
    route = ox.shortest_path(G, nodes[0], nodes[len(nodes)//2], weight='length')
    return [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]

try:
    route_coords = get_route(place)
except Exception as e:
    st.error(f"Could not find location: {e}")
    st.stop()

# 3. UI Placeholders
# We use placeholders so we can update the map in the same spot
status_box = st.empty()
map_placeholder = st.empty()

# 4. Simulation Execution
if run_btn:
    for i, coord in enumerate(route_coords):
        # Update Dashboard
        current_speed = np.random.uniform(30, 60)
        battery = max(0, 100 - i)
        
        status_box.markdown(f"""
        ### Telemetry
        **Progress:** {i+1}/{len(route_coords)} | **Speed:** {current_speed:.1f} km/h | **Battery:** {battery}%
        """)

        # Re-render the map at the new position
        m = folium.Map(location=coord, zoom_start=16)
        
        # Draw the full planned path
        folium.PolyLine(route_coords, color="blue", weight=2, opacity=0.5).add_to(m)
        
        # Draw the car
        folium.Marker(
            location=coord, 
            icon=folium.Icon(color='red', icon='car', prefix='fa')
        ).add_to(m)
        
        with map_placeholder:
            st_folium(m, height=500, width=1200, key=f"map_{i}")
        
        time.sleep(speed)
    st.success("Target Reached!")
else:
    # Show initial static map
    m = folium.Map(location=route_coords[0], zoom_start=16)
    folium.PolyLine(route_coords, color="blue", weight=2).add_to(m)
    with map_placeholder:
        st_folium(m, height=500, width=1200)