import streamlit as st
import osmnx as ox
import folium
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Moving Car Project", layout="wide")

# Inject FontAwesome for the car icon
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)

if 'points' not in st.session_state: st.session_state.points = []
if 'sim_ready' not in st.session_state: st.session_state.sim_ready = False

st.title("Logistics & Telemetry Simulator")

# 1. Sidebar Setup
with st.sidebar:
    st.header("1. Setup")
    # city = st.text_input("City Name", "Midtown, New York, USA")
    city = st.text_input("City Name", "Accra, Ghana")
    st.info("Click 2 points: START (Green) then END (Red).")
    
    if st.button("🔄 Reset"):
        st.session_state.points = []
        st.session_state.sim_ready = False
        st.rerun()
        
    st.header("2. Simulation")
    step_sec = st.slider("Seconds per node", 1, 10, 2)
    
    if len(st.session_state.points) == 2:
        if st.button("Deploy Vehicle"):
            st.session_state.sim_ready = True

# # 2. Data Processing (One-time calculation)
# @st.cache_data
def get_map_graph(location):
    return ox.graph_from_address(location, dist=3500, network_type='drive')

@st.cache_data
def prepare_simulation_data(_G, p1, p2, speed):
    n1 = ox.distance.nearest_nodes(_G, X=p1[1], Y=p1[0])
    n2 = ox.distance.nearest_nodes(_G, X=p2[1], Y=p2[0])
    route = ox.shortest_path(_G, n1, n2, weight='length')
    
    path_coords = [[_G.nodes[n]['y'], _G.nodes[n]['x']] for n in route]
    start_time = datetime(2026, 3, 10, 12, 0, 0)
    times = [(start_time + timedelta(seconds=i * speed)).isoformat() for i in range(len(route))]
    
    speeds = np.random.normal(40, 5, len(route)).tolist()
    
    geojson = {
        'type': 'Feature',
        'geometry': {
            'type': 'LineString',
            'coordinates': [[c[1], c[0]] for c in path_coords],
        },
        'properties': {
            'times': times,
            'icon': 'marker',
            'tooltip': 'Vehicle 1',
            'icon_options': {
                'prefix': 'fa', 
                'icon': 'car', 
                'color': 'red',     # 'color' is more compatible with the plugin
                'iconColor': 'white'
            }
        }
    }
    return {'path': path_coords, 'geojson': geojson, 'speeds': speeds, 'times': times}

# # 3. Build the Map
# G = get_map_graph(city)
# center = st.session_state.points[0] if st.session_state.points else [40.7580, -73.9855]

# --- 1. Geocoding Logic (Add this new cached function) ---
@st.cache_data
def get_city_center(location):
    try:
        # Returns (lat, lon)
        return ox.geocode(location)
    except:
        # Fallback to a default if geocoding fails (e.g., Accra coordinates)
        return [5.6037, -0.1870]

# --- 2. Build the Map ---
G = get_map_graph(city)

# Auto-extract city center from the text input
city_lat_lon = get_city_center(city)

# Hierarchical centering logic
if st.session_state.points:
    # Center on the first clicked point (Start)
    center = st.session_state.points[0]
else:
    # Center on the city's geographical center
    center = city_lat_lon


m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron", control_scale=True, prefer_canvas=True, )

# Draw selection pins
for i, p in enumerate(st.session_state.points):
    folium.Marker(p, icon=folium.Icon(color='green' if i==0 else 'red')).add_to(m)



sim_data = None
if st.session_state.sim_ready and len(st.session_state.points) == 2:
    sim_data = prepare_simulation_data(G, st.session_state.points[0], st.session_state.points[1], step_sec)
    
    # The blue flow line
    AntPath(locations=sim_data['path'], color='blue', weight=5, delay=4000).add_to(m)
    
    # The car (animated in browser JS)
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': [sim_data['geojson']]},
        period='PT1S', add_last_point=True, auto_play=True, loop=False, 
    ).add_to(m)

# DISPLAY MAP ONCE
output = st_folium(m, width=1300, height=550, key="stable_map")

# Handle Clicks (only if not simulating)
if output['last_clicked'] and len(st.session_state.points) < 2 and not st.session_state.sim_ready:
    st.session_state.points.append([output['last_clicked']['lat'], output['last_clicked']['lng']])
    st.rerun()

# 4. Display the Graph (Stable)
if sim_data:
    st.subheader("📊 Full Trip Telemetry")
    fig = go.Figure(go.Scatter(x=sim_data['times'], y=sim_data['speeds'], fill='tozeroy', line=dict(color='red')))
    fig.update_layout(height=300, margin=dict(l=0,r=0,t=0,b=0), xaxis_title="Time", yaxis_title="Speed (km/h)")
    st.plotly_chart(fig, use_container_width=True)