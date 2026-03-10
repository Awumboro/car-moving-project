import streamlit as st
import osmnx as ox
import folium
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="Pro Vehicle Simulator", layout="wide")

# 1. Sidebar - Setup the Inputs
with st.sidebar:
    st.header("🛰️ Mission Control")
    place_name = st.text_input("Location", "Midtown, New York, USA")
    route_dist = st.slider("Route Distance (m)", 500, 2500, 1000)
    travel_speed = st.slider("Seconds per node", 1, 10, 2)
    st.write("---")
    # Using a button prevents the "slider lag" 
    # because the heavy code only runs when clicked.
    generate = st.button("🚀 Update & Deploy Vehicle")

# 2. Optimized Data Processing
@st.cache_data(show_spinner="Downloading Map & Routing...")
def get_cached_simulation(location, distance, step_sec):
    try:
        # Load the graph
        G = ox.graph_from_address(location, dist=distance, network_type='drive')
        nodes = list(G.nodes())
        # Calculate shortest path
        route = ox.shortest_path(G, nodes[0], nodes[-1], weight='length')
        
        path_coords = []
        times = []
        start_time = datetime(2026, 3, 10, 12, 0, 0)

        for i, node in enumerate(route):
            p = G.nodes[node]
            # Folium/Leaflet uses [Lat, Lon] for lines
            path_coords.append([p['y'], p['x']])
            # GeoJSON uses [Lon, Lat] for movement
            current_time = (start_time + timedelta(seconds=i * step_sec)).isoformat()
            times.append(current_time)

        # Structure for a SINGLE MOVING CAR (LineString + times)
        moving_car_geojson = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': [[c[1], c[0]] for c in path_coords], # Lon, Lat
            },
            'properties': {
                'times': times,
                'style': {'color': 'red', 'opacity': 0}, # Hide the path line, show only marker
                'icon': 'marker',
                'icon_options': {
                    'prefix': 'fa', 'icon': 'car', 'markerColor': 'red'
                }
            }
        }
        
        return {
            'center': path_coords[0],
            'path': path_coords,
            'geojson': moving_car_geojson
        }
    except Exception as e:
        return str(e)

# 3. Execution Logic
# We run it if the button is pressed OR if we already have it in the session
if "map_data" not in st.session_state:
    st.session_state.map_data = get_cached_simulation(place_name, route_dist, travel_speed)

if generate:
    st.session_state.map_data = get_cached_simulation(place_name, route_dist, travel_speed)

data = st.session_state.map_data

if isinstance(data, str):
    st.error(f"Error: {data}")
else:
    # 4. Building the Map
    m = folium.Map(location=data['center'], zoom_start=16, tiles="cartodbpositron")

    # Add the flowing "Planned Route"
    AntPath(locations=data['path'], color='blue', weight=5, opacity=0.5).add_to(m)

    # Add the Moving Vehicle
    TimestampedGeoJson(
        {'type': 'FeatureCollection', 'features': [data['geojson']]},
        period='PT1S',
        add_last_point=True,
        auto_play=True,
        loop=True,
        max_speed=1
    ).add_to(m)

    st_folium(m, width=1200, height=650, key="sim_map")