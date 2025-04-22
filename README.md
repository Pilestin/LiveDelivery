# SUMO Traffic Simulation and Vehicle Tracker

This project provides tools for running SUMO traffic simulations and visualizing the movement of vehicles.

## Components

1. **Main Application** (`main.py`): A Streamlit application that lets you run SUMO simulations and analyze the results.
2. **Vehicle Tracker** (`vehicle_tracker.html`): A web-based tool for visualizing the movement of vehicles from the simulation.

## Requirements

- Python 3.6+
- SUMO (Simulation of Urban MObility)
- Streamlit
- Other Python dependencies listed in requirements.txt

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Make sure SUMO is installed and the SUMO_HOME environment variable is set.

## Usage

1. Run the main application:
   ```
   streamlit run main.py
   ```

2. Upload a SUMO route file and start the simulation.

3. After the simulation completes, you can use the "Vehicle Tracker" HTML file to visualize the movement of vehicles. Simply open the HTML file in your web browser.

## Multi-Vehicle Tracking

The vehicle tracker supports visualizing multiple vehicles simultaneously:

- Each vehicle is displayed with a unique color
- You can toggle individual vehicles on/off 
- Play/pause/reset controls are available for each vehicle
- Global controls affect all displayed vehicles
- Vehicle statistics show distance traveled and travel time

## Features

- **Route File Upload**: Upload SUMO route files directly
- **Simulation Control**: Start, monitor, and analyze SUMO simulations
- **Results Visualization**: View statistics about simulated routes
- **Dynamic Route Visualization**: Watch vehicles move along their routes
- **Export Data**: Export route data as CSV files for further analysis

## File Structure

- `main.py`: Main Streamlit application
- `vehicle_tracker.html`: Web-based vehicle visualization tool
- `configs/`: Directory for configuration files
- `outputs/`: Directory for simulation output files
