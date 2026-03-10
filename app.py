import streamlit as st
import osmnx as ox
import folium
import plotly.graph_objects as go
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import numpy as np

st.set_page_config(page_title="Pro Logistics Sim", layout="wide")

# Inject FontAwesome for the Car Icon
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)

# 1. State Management
if 'points' not in st.session_state:
    st.session_state.points = []
if 'sim_ready' not in st.session_state:
    st.session_state.sim_ready = False

st.title("🚗 Pro Logistics & Telemetry Simulator")

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
    
    if len(st.session_state.points) == 2:
        if st.button("🚀 Deploy Vehicle"):
            st.session_state.sim_ready = True

# 3. Robust Data Logic
@st.cache_data
def get_city_graph(location):
    return ox.graph_from_address(location, dist=1500, network_type='drive')

@st.cache_data
def calculate_route_and_telemetry(_G, p1, p2, step_sec):
    try:
        orig_node = ox.distance.nearest_nodes(_G, X=p1[1], Y=p1[0])
        dest_node = ox.distance.nearest_nodes(_G, X=p2[1], Y=p2[0])
        route = ox.shortest_path(_G, orig_node, dest_node, weight='length')
        
        if not route:
            return "No route found between these points."

        path_coords = []
        for node_id in route:
            # ROBUST CHECK: Use .get() or access via graph nodes safely
            if node_id in _G.nodes:
                node_data = _G.nodes[node_id]
                path_coords.append([node_data['y'], node_data['x']])
            else:
                # Fallback: some nodes might be hidden in edges
                continue
        
        if not path_coords:
            return "Routing data error: No coordinates found."

        start_time = datetime(2026, 3, 10, 12, 0, 0)
        telemetry_values = np.random.normal(40, 5, len(path_coords)).tolist()
        times = [(start_time + timedelta(seconds=i * step_sec)).isoformat() for i in range(len(path_coords))]
        
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
        return {'path': path_coords, 'geojson': geojson, 'telemetry': telemetry_values, 'times': times}
    except Exception as e:
        return f"Routing Error: {str(e)}"

# 4. Map Logic
G = get_city_graph(city)
map_center = st.session_state.points[0] if st.session_state.points else [40.7580, -73.9855]
m = folium.Map(location=map_center, zoom_start=15, tiles="cartodbpositron")

# Draw selection markers
for i, pt in enumerate(st.session_state.points):
    color = 'green' if i == 0 else 'red'
    folium.Marker(pt, icon=folium.Icon(color=color, icon='info-sign')).add_to(m)

sim_data = None
if st.session_state.sim_ready and len(st.session_state.points) == 2:
    sim_result = calculate_route_and_telemetry(G, st.session_state.points[0], st.session_state.points[1], speed_mult)
    
    if isinstance(sim_result, str):
        st.error(sim_result)
        st.session_state.sim_ready = False
    else:
        sim_data = sim_result
        AntPath(locations=sim_data['path'], color='blue', weight=5, delay=4000).add_to(m)
        TimestampedGeoJson(
            {'type': 'FeatureCollection', 'features': [sim_data['geojson']]},
            period='PT1S', add_last_point=True, auto_play=True, loop=False, duration='PT0S'
        ).add_to(m)

output = st_folium(m, width=1300, height=550, key="unified_map_v3")

if output['last_clicked'] and not st.session_state.sim_ready:
    new_pt = [output['last_clicked']['lat'], output['last_clicked']['lng']]
    if len(st.session_state.points) < 2 and new_pt not in st.session_state.points:
        st.session_state.points.append(new_pt)
        st.rerun()

# 5. Dashboard Graph
if sim_data:
    st.subheader("📊 Vehicle Telemetry Dashboard")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sim_data['times'], y=sim_data['telemetry'], fill='tozeroy', line=dict(color='red')))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)