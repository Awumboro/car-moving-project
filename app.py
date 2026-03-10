import streamlit as st
import osmnx as ox
import folium
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Vehicle Simulator", layout="wide")

st.title("🚀 Professional Vehicle Route Simulator")

# 1. Sidebar with "Action" button to prevent lag
with st.sidebar:
    st.header("Simulation Parameters")
    place_input = st.text_input("City/Location", "Midtown, New York, USA")
    dist_input = st.slider("Route Range (m)", 500, 2000, 1000)
    speed_input = st.slider("Seconds per node", 1, 10, 2)
    st.info("Adjust parameters and then click Deploy below.")
    deploy_btn = st.button("🚀 Deploy / Refresh Vehicle")

# 2. Logic to generate the timed route
@st.cache_data(show_spinner="Fetching map and calculating route...")
def get_clean_route(location, distance, step_duration):
    try:
        # Get graph and path
        G = ox.graph_from_address(location, dist=distance, network_type='drive')
        nodes = list(G.nodes())
        route = ox.shortest_path(G, nodes[0], nodes[-1], weight='length')
        
        start_time = datetime(2026, 3, 10, 12, 0, 0)
        
        coordinates = []
        times = []
        
        for i, node in enumerate(route):
            point = G.nodes[node]
            # GeoJSON uses [Lon, Lat]
            coordinates.append([point['x'], point['y']])
            current_time = (start_time + timedelta(seconds=i * step_duration)).isoformat()
            times.append(current_time)

        # ONE feature with MANY times = One car that moves (No trail)
        moving_car_feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString', # LineString + times = moving marker along line
                'coordinates': coordinates,
            },
            'properties': {
                'times': times,
                'style': {'color': 'blue', 'opacity': 0}, # Hide the line itself
                'icon': 'marker',
                'icon_options': {
                    'prefix': 'fa',
                    'icon': 'car',
                    'markerColor': 'red'
                }
            }
        }
        
        center = [G.nodes[route[0]]['y'], G.nodes[route[0]]['x']]
        path_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]
        
        return {'geojson': moving_car_feature, 'path': path_coords, 'center': center}
    except Exception as e:
        return str(e)

# 3. Render the Map
if deploy_btn:
    data = get_clean_route(place_input, dist_input, speed_input)
    
    if isinstance(data, str):
        st.error(f"Error: {data}")
    else:
        m = folium.Map(location=data['center'], zoom_start=16, tiles="cartodbpositron")
        
        # Static Flowing Path
        AntPath(
            locations=data['path'],
            color='blue',
            weight=5,
            opacity=0.5
        ).add_to(m)

        # Single Moving Marker
        TimestampedGeoJson(
            {'type': 'FeatureCollection', 'features': [data['geojson']]},
            period='PT1S',
            add_last_point=True,
            auto_play=True,
            loop=True,
            max_speed=1
        ).add_to(m)

        st_folium(m, width=1200, height=600, key="sim_map")
else:
    st.write("👈 Set your parameters and click **Deploy Vehicle** to start.")