import streamlit as st
import osmnx as ox
import folium
from folium.plugins import TimestampedGeoJson
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="Smooth Vehicle Tracker", layout="wide")

st.title("🚗 Smooth Cloud-Optimized Vehicle Tracker")
st.markdown("This version uses browser-side animation to prevent flickering.")

# 1. Sidebar Configuration
with st.sidebar:
    place = st.text_input("Location", "Empire State Building, New York, USA")
    dist = st.slider("Route Distance", 500, 1500, 800)
    car_speed = st.slider("Simulated Car Speed (seconds per block)", 1, 10, 2)
    ready = st.button("Generate Animated Map")

# 2. Data Processing
@st.cache_data
def get_animated_route(location, distance, step_duration):
    try:
        G = ox.graph_from_address(location, dist=distance, network_type='drive')
        nodes = list(G.nodes())
        route = ox.shortest_path(G, nodes[0], nodes[len(nodes)//2], weight='length')
        
        features = []
        start_time = datetime.now()
        
        # Create the trajectory data
        coordinates = []
        times = []
        
        for i, node in enumerate(route):
            point = G.nodes[node]
            # Folium TimestampedGeoJson needs [Lon, Lat]
            coordinates.append([point['x'], point['y']])
            # Add timestamps for the browser to follow
            current_time = (start_time + timedelta(seconds=i * step_duration)).strftime('%Y-%m-%dT%H:%M:%S')
            times.append(current_time)

        # Build the GeoJSON Feature
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': coordinates,
            },
            'properties': {
                'times': times,
                'style': {'color': 'red', 'weight': 5},
                'icon': 'marker', # Tells the plugin to put a marker at the current time
                'icon_options': {'color': 'red'}
            }
        }
        
        center = [G.nodes[route[0]]['y'], G.nodes[route[0]]['x']]
        return {'feature': feature, 'center': center}
    except Exception as e:
        return str(e)

# 3. Execution
if ready or place:
    data = get_animated_route(place, dist, car_speed)
    
    if isinstance(data, str):
        st.error(f"Error: {data}")
    else:
        # Create Map
        m = folium.Map(location=data['center'], zoom_start=15)
        
        # Add the Animation Plugin
        # This handles the movement IN THE BROWSER without Python reruns
        TimestampedGeoJson(
            {'type': 'FeatureCollection', 'features': [data['feature']]},
            period='PT1S',
            duration='PT1S',
            add_last_point=True,
            auto_play=True,
            loop=True,
            max_speed=1,
            loop_button=True,
            date_options='HH:mm:ss',
            time_slider_drag_update=True
        ).add_to(m)

        # Render
        st_folium(m, width=1200, height=600, key="fixed_map")

st.info("The slider at the bottom left of the map controls the car's progress manually.")