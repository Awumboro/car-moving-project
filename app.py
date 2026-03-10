import osmnx as ox
import time
import threading
import numpy as np
from ipyleaflet import Map, Marker, AntPath, WidgetControl, AwesomeIcon
from ipywidgets import HTML
from IPython.display import display

# 1. Configuration & Data Retrieval
PLACE_NAME = "Empire State Building, New York, USA"
DISTANCE = 800  # meters
TRAVEL_SPEED = 0.5 # seconds per node update

print("Fetching map data... please wait.")
G = ox.graph_from_address(PLACE_NAME, dist=DISTANCE, network_type='drive')
nodes = list(G.nodes())

# Find a route between two distant nodes in the graph
orig_node = nodes[0]
dest_node = nodes[len(nodes)//2] 
route = ox.shortest_path(G, orig_node, dest_node, weight='length')
route_coords = [[G.nodes[n]['y'], G.nodes[n]['x']] for n in route]

# 2. Initialize Map Components
# Create a car icon for the marker
car_icon = AwesomeIcon(name='car', marker_color='red', icon_color='white')

m = Map(center=route_coords[0], zoom=16)

# Create the dashboard UI
dashboard = HTML(
    value="<b>Initializing system...</b>",
    layout={'padding': '10px'}
)

# Create the vehicle marker
car_marker = Marker(location=route_coords[0], icon=car_icon, draggable=False)

# Add elements to map
m.add_layer(car_marker)
m.add_layer(AntPath(locations=route_coords, color='blue', pulse_color='white'))
m.add_control(WidgetControl(widget=dashboard, position='topright'))

# 3. The Simulation Logic
def run_vehicle_simulation():
    """Background task to move the car and update data."""
    time.sleep(2) # Wait for the map to render in the browser
    
    total_steps = len(route_coords)
    
    for i, coord in enumerate(route_coords):
        # Update the physical marker position
        car_marker.location = coord
        
        # Calculate simulated metrics
        current_speed = np.random.uniform(25, 55)
        battery_level = max(0, 100 - (i * (100/total_steps)))
        
        # Update the HTML Dashboard
        dashboard.value = f"""
        <div style="background-color: white; border: 2px solid #333; border-radius: 5px; padding: 10px; min-width: 150px;">
            <h4 style="margin: 0 0 10px 0; color: #d9534f;">Vehicle Telemetry</h4>
            <table style="width: 100%;">
                <tr><td><b>Progress:</b></td><td>{i+1}/{total_steps}</td></tr>
                <tr><td><b>Speed:</b></td><td>{current_speed:.1f} km/h</td></tr>
                <tr><td><b>Battery:</b></td><td>{battery_level:.1f}%</td></tr>
            </table>
        </div>
        """
        
        time.sleep(TRAVEL_SPEED)
    
    dashboard.value = "<div style='background: white; padding: 10px;'><b>Destination Reached.</b></div>"

# 4. Execution
display(m)

# Run the simulation in a background thread so the map remains interactive
simulation_thread = threading.Thread(target=run_vehicle_simulation)
simulation_thread.start()