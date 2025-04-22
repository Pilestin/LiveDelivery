import streamlit as st
import pandas as pd
import os
import subprocess
import time
from datetime import datetime, timedelta
import traci
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import folium
from streamlit_folium import st_folium

# Page configuration
st.set_page_config(
    page_title="SUMO Trafik Simülasyonu",
    page_icon="🚗",
    layout="wide"
)

# Create necessary directories
os.makedirs("configs", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# Function to check if SUMO is installed
def check_sumo_installation():
    sumo_home = os.environ.get("SUMO_HOME")
    if not sumo_home:
        return False, "SUMO_HOME environment variable is not set"
    
    try:
        # Try to run sumo --version to check if it's installed
        result = subprocess.run(["sumo", "--version"], 
                               capture_output=True, 
                               text=True)
        return True, result.stdout
    except FileNotFoundError:
        return False, "SUMO executable not found in PATH"

# Function to run SUMO simulation with TRACI
def run_simulation(progress_bar, status_text):
    results = []
    vehicle_paths = {}
    
    # Use the existing sumocfg file
    config_file = "configs/dennn.sumocfg"
    
    try:
        # Start TRACI with SUMO
        traci.start(["sumo", "-c", config_file])
        
        step = 0
        max_steps = 1000  # Set a reasonable limit
        begin_time = datetime.now()
        timestamp = begin_time
        # Main simulation loop
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            step += 1
            
            # Update progress bar every step
            progress = min(1.0, step / max_steps)
            progress_bar.progress(progress)
            
            vehicle_ids = traci.vehicle.getIDList()
            sim_time = traci.simulation.getTime()
            status_text.text(f"Simülasyon adımı: {step}, Zaman: {sim_time:.2f}, Araç sayısı: {len(vehicle_ids)}")
            
            # Collect data for each vehicle
            for veh_id in vehicle_ids:
                edge_id = traci.vehicle.getRoadID(veh_id)
                x, y, z = traci.vehicle.getPosition3D(veh_id) 
                lon, lat = traci.simulation.convertGeo(x, y)
                altitude = z
                slope = traci.vehicle.getSlope(veh_id)
                angle = traci.vehicle.getAngle(veh_id)
                speed = traci.vehicle.getSpeed(veh_id)
                energy_consumption = traci.vehicle.getElectricityConsumption(veh_id)

                # Store data
                data_point = {
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S.%f"),
                    "vehicle_id": veh_id,
                    "step": step,
                    "simulation_time": sim_time,
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": altitude,
                    "slope": slope,
                    "energy_consumption": energy_consumption,
                    "speed": speed,
                    "angle": angle,
                    "edge_id": edge_id
                }
                results.append(data_point)

                # Store path data for each vehicle
                if veh_id not in vehicle_paths:
                    vehicle_paths[veh_id] = []
                vehicle_paths[veh_id].append((lat, lon))
            
            timestamp += timedelta(seconds=1)
            
            
        # Close TRACI connection
        traci.close()
        
        # Create a DataFrame from results
        df = pd.DataFrame(results)
        
        return True, df, vehicle_paths
    
    except Exception as e:
        try:
            traci.close()
        except:
            pass
        return False, str(e), {}

# Function to save results to CSV
def save_to_csv(df, filename="trajectory_data.csv"):
    output_path = os.path.join("outputs", filename)
    df.to_csv(output_path, index=False)
    return output_path

st.title("🚗 SUMO Trafik Simülasyonu ve Rota Takibi")

# Check SUMO installation
sumo_installed, sumo_message = check_sumo_installation()
if not sumo_installed:
    st.error(f"⚠️ SUMO kurulumu bulunamadı: {sumo_message}")
    st.info("SUMO'yu kurmanız ve SUMO_HOME ortam değişkenini ayarlamanız gerekmektedir.")
    st.stop()
else:
    st.success(f"✅ SUMO kurulumu bulundu: {sumo_message.strip()}")

# Create tabs for different functionality
tab1, tab2, tab3 = st.tabs(["Simülasyon", "Sonuçlar", "Rota Görüntüleme"])

with tab1:
    st.header("Simülasyon Ayarları")
    
    # File upload section - only route file
    st.subheader("Route4Sim Dosyasını Yükleyin")
    route_file = st.file_uploader("SUMO rota dosyası (.xml, .rou.xml)", type=["xml", "rou.xml"])
    
    if route_file:
        # Save the uploaded file as Route4Sim.xml
        route_file_path = os.path.join("configs", "Route4Sim.xml")
        with open(route_file_path, "wb") as f:
            f.write(route_file.getvalue())
        st.success(f"✅ Rota dosyası başarıyla yüklendi ve {route_file_path} konumuna kaydedildi.")
        
        # Display file info
        file_size = os.path.getsize(route_file_path)
        st.info(f"Dosya boyutu: {file_size/1024:.2f} KB")
        
        # Try to parse the XML to show route information
        try:
            tree = ET.parse(route_file_path)
            root = tree.getroot()
            vehicle_count = len(root.findall(".//vehicle"))
            route_count = len(root.findall(".//route"))
            st.write(f"Tespit edilen araç sayısı: {vehicle_count}")
            st.write(f"Tespit edilen rota sayısı: {route_count}")
        except Exception as e:
            st.warning(f"XML dosyası ayrıştırılamadı: {str(e)}")
        
        # Run simulation button
        st.subheader("Simülasyonu Çalıştır")
        if st.button("▶️ Simülasyonu Başlat"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("Simülasyon başlatılıyor...")
            
            # Run the simulation
            success, result, vehicle_paths = run_simulation(progress_bar, status_text)
            
            if success:
                # Save results to session state
                st.session_state.simulation_results = result
                st.session_state.vehicle_paths = vehicle_paths
                
                # Save to CSV
                csv_path = save_to_csv(result)
                st.success(f"✅ Simülasyon tamamlandı! Sonuçlar {csv_path} dosyasına kaydedildi.")
                
                # Display summary
                st.subheader("Simülasyon Özeti")
                st.write(f"Toplanan veri noktası sayısı: {len(result)}")
                st.write(f"Simüle edilen araç sayısı: {result['vehicle_id'].nunique()}")
                st.write(f"Toplam simülasyon süresi: {result['simulation_time'].max():.2f} saniye")
                
                # Copy to Extended_Trajectory_Data.csv for the visualization app
                extended_path = "Extended_Trajectory_Data.csv"
                result[['timestamp', 'latitude', 'longitude']].to_csv(extended_path, index=False)
                st.info(f"Veriler, görselleştirme uygulaması için {extended_path} olarak da kaydedildi.")
            else:
                st.error(f"❌ Simülasyon sırasında hata oluştu: {result}")
    else:
        st.warning("Lütfen bir rota dosyası yükleyin.")

with tab2:
    st.header("Simülasyon Sonuçları")
    
    if 'simulation_results' in st.session_state:
        results = st.session_state.simulation_results
        
        # Show data preview
        st.subheader("Veri Önizleme")
        st.dataframe(results.head(10))
        
        # Download button
        csv = results.to_csv(index=False)
        st.download_button(
            label="CSV olarak İndir",
            data=csv,
            file_name="simulation_results.csv",
            mime="text/csv"
        )
        
        # Show some statistics
        st.subheader("İstatistikler")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Araç başına ortalama hız:")
            vehicle_speeds = results.groupby('vehicle_id')['speed'].mean()
            st.bar_chart(vehicle_speeds)
        
        with col2:
            st.write("Zamana göre araç sayısı:")
            vehicles_per_step = results.groupby('step')['vehicle_id'].nunique()
            st.line_chart(vehicles_per_step)
    else:
        st.info("Henüz bir simülasyon çalıştırılmadı. Lütfen önce 'Simülasyon' sekmesinde bir simülasyon çalıştırın.")

with tab3:
    # Same as before
    st.header("Rota Görüntüleme")
    
    if 'simulation_results' in st.session_state and 'vehicle_paths' in st.session_state:
        results = st.session_state.simulation_results
        vehicle_paths = st.session_state.vehicle_paths
        
        # Vehicle selection
        vehicle_list = sorted(list(vehicle_paths.keys()))
        selected_vehicle = st.selectbox("Gösterilecek aracı seçin:", vehicle_list)
        
        if selected_vehicle:
            # Get vehicle path
            path = vehicle_paths[selected_vehicle]
            
            # Create map
            center_lat = sum(p[0] for p in path) / len(path)
            center_lon = sum(p[1] for p in path) / len(path)
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
            
            # Add vehicle path as polyline
            folium.PolyLine(
                locations=path,
                weight=5,
                color="blue",
                opacity=0.7,
                tooltip=f"Vehicle {selected_vehicle} path"
            ).add_to(m)
            
            # Add markers for start and end points
            folium.Marker(
                location=path[0],
                icon=folium.Icon(icon="play", prefix="fa", color="green"),
                tooltip="Start point"
            ).add_to(m)
            
            folium.Marker(
                location=path[-1],
                icon=folium.Icon(icon="flag-checkered", prefix="fa", color="red"),
                tooltip="End point"
            ).add_to(m)
            
            # Display the map
            st_folium(m, width=800, height=500)
            
            # Show vehicle details
            vehicle_data = results[results['vehicle_id'] == selected_vehicle]
            
            st.subheader(f"Araç {selected_vehicle} Detayları")
            st.write(f"Yolculuk süresi: {vehicle_data['simulation_time'].max() - vehicle_data['simulation_time'].min():.2f} saniye")
            st.write(f"Ortalama hız: {vehicle_data['speed'].mean():.2f} m/s")
            st.write(f"Maksimum hız: {vehicle_data['speed'].max():.2f} m/s")
            
            # Plot speed over time
            st.subheader("Zamana göre hız")
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(vehicle_data['simulation_time'], vehicle_data['speed'])
            ax.set_xlabel('Simülasyon zamanı (s)')
            ax.set_ylabel('Hız (m/s)')
            ax.grid(True)
            st.pyplot(fig)
            
            # Export individual vehicle path
            if st.button(f"{selected_vehicle} aracının yolunu CSV olarak dışa aktar"):
                vehicle_csv = vehicle_data.to_csv(index=False)
                st.download_button(
                    label="İndir",
                    data=vehicle_csv,
                    file_name=f"vehicle_{selected_vehicle}_path.csv",
                    mime="text/csv"
                )
    else:
        st.info("Henüz bir simülasyon çalıştırılmadı. Lütfen önce 'Simülasyon' sekmesinde bir simülasyon çalıştırın.")
