import streamlit as st
import osmnx as ox
import folium
from folium.plugins import TimestampedGeoJson, AntPath
from streamlit_folium import st_folium
from datetime import datetime, timedelta

st.set_page_config(page_title="Realistic Vehicle Tracker", layout="wide")

st.title("🚗 Pro Vehicle Route Simulator")
st.markdown("This version uses **Client-Side Rendering** for smooth, zero-flicker movement.")

# 1. Sidebar Configuration
with st.sidebar:
    st.header("Simulation Parameters")
    place = st.text_input("City/Location", "Midtown, New York, USA")
    dist = st.slider("Route Range (m)", 500, 2000, 1000)
    car_speed = st.slider("Simulated Speed (seconds per block)", 1, 10, 3)
    st.divider()
    ready = st.button("🚀 Deploy Vehicle")

# 2. Advanced Data Processing
@st.cache_data
def get_realistic_route(location, distance, step_duration):
    try:
        # Fetching network
        G = ox.graph_from_address(location, dist=distance, network_type='drive')
        nodes = list(G.nodes())
        # Pick two distant nodes
        route = ox.shortest_path(G, nodes[0], nodes[len(nodes)-1], weight='length')
        
        start_time = datetime(2026, 3, 10, 12, 0, 0) # Fixed starting point
        
        features = []
        full_path_coords = []

        for i, node in enumerate(route):
            point = G.nodes[node]
            lat, lon = point['y'], point['x']
            full_path_coords.append([lat, lon]) # For the static line
            
            # Create a point feature for the car at this specific second
            current_time = (start_time + timedelta(seconds=i * step_duration)).isoformat()
            
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat], # GeoJSON uses [Lon, Lat]
                },
                'properties': {
                    'time': current_time,
                    'icon': 'marker',
                    'icon_options': {
                        'iconShape': 'extra-marker',
                        'prefix': 'fa',
                        'icon': 'car',
                        'markerColor': 'red',
                        'iconColor': 'white'
                    }
                }
            })

        center = [G.nodes[route[0]]['y'], G.nodes[route[0]]['x']]
        return {'features': features, 'path': full_path_coords, 'center': center}
    except Exception as e:
        return str(e)

# 3. Execution Logic
if place:
    data = get_realistic_route(place, dist, car_speed)
    
    if isinstance(data, str):
        st.error(f"Network Error: {data}")
    else:
        # Create the Base Map
        m = folium.Map(location=data['center'], zoom_start=16, tiles="cartodbpositron")
        
        # Add a static "Planned Route" AntPath (Realistic blue flow)
        AntPath(
            locations=data['path'],
            dash_array=[1, 10],
            delay=1000,
            color='#0000FF',
            pulse_color='#FFFFFF',
            weight=4,
            opacity=0.6
        ).add_to(m)

        # Add the Time-Based Moving Car
        TimestampedGeoJson(
            {'type': 'FeatureCollection', 'features': data['features']},
            period='PT1S',
            add_last_point=True,
            auto_play=True,
            loop=True,
            max_speed=1,
            loop_button=True,
            time_slider_drag_update=True
        ).add_to(m)

        # Final Render
        st_folium(m, width=1300, height=700, key="realistic_sim")

st.caption("Controls are located at the bottom left of the map frame.")