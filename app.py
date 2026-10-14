import streamlit as st
import psycopg2
import pandas as pd
import datetime

# 1. Page Configuration (Sets the tab title and layout wide)
st.set_page_config(page_title="Climate Portal", page_icon="🌤️", layout="wide")

# Custom CSS to make the metrics and headers look modern
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border-left: 5px solid #F26B21;
        padding: 10px 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    return psycopg2.connect(
        dbname="Project", user="postgres", password="password", host="localhost", port="5432"
    )

try:
    conn = init_connection()
    cur = conn.cursor()

    # ================= SIDEBAR =================
    with st.sidebar:
        st.title("🌍 Climate Portal")
        st.markdown("### Navigation")
        
        # Fetch 6 Cities for the dropdown
        cur.execute("SELECT station_id, location FROM climate_sensors ORDER BY station_id;")
        stations = cur.fetchall()
        station_dict = {name: s_id for s_id, name in stations}

        selected_city = st.selectbox("📍 Select Station:", options=list(station_dict.keys()))
        current_station_id = station_dict[selected_city]
        
        st.divider()
        st.caption("DBMS Lab Project")

    # ================= MAIN PAGE HEADER =================
    st.title(f"🌤️ {selected_city} Weather Station")
    st.markdown("Monitor historical trends, calculate averages, and log new climate data.")
    
    # Fetch Past Data to use across the tabs
    df_past = pd.read_sql(
        "SELECT * FROM observation_log WHERE \"Station\" = %s ORDER BY \"Date\" DESC, \"Sr. No.\" DESC;", 
        conn, params=(selected_city,)
    )
    
    if not df_past.empty:
        # Create a visual Sr. No. starting from 1, but keep the real DB ID hidden for deleting
        df_past.rename(columns={"Sr. No.": "Record ID"}, inplace=True)
        df_past.insert(0, "Sr. No.", range(1, len(df_past) + 1))

    # ================= TABS NAVIGATION =================
    tab_dash, tab_add, tab_manage = st.tabs(["📊 Dashboard & Trends", "📝 Log New Data", "⚙️ Manage Records"])

    # --- TAB 1: DASHBOARD ---
    with tab_dash:
        # Dynamic Heatwave Alert Banner based on the latest reading
        if not df_past.empty:
            latest_temp = df_past.iloc[0]["Temperature (°C)"]
            if latest_temp > 40:
                st.error(f"🚨 **Heatwave Alert Level: High heatwave alert** (Latest reading: {latest_temp}°C)")
            elif 35 <= latest_temp <= 40:
                st.warning(f"⚠️ **Heatwave Alert Level: Moderate heatwave alert** (Latest reading: {latest_temp}°C)")
            else:
                st.success(f"✅ **Heatwave Alert Level: No heatwave alert** (Latest reading: {latest_temp}°C)")

        st.subheader("Station Averages")
        cur.execute("""
            SELECT AVG(temperature), AVG(rainfall), AVG(wind_speed), AVG(humidity)
            FROM sensor_observations WHERE station_id = %s
        """, (current_station_id,))
        avgs = cur.fetchone()
        
        if avgs[0] is not None:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🌡️ Avg Temp", f"{avgs[0]:.1f} °C")
            m2.metric("🌧️ Avg Rain", f"{avgs[1]:.1f} mm")
            m3.metric("🌬️ Avg Wind", f"{avgs[2]:.1f} km/h")
            m4.metric("💧 Avg Humidity", f"{avgs[3]:.1f} %")
            
            st.divider()
            
            # Create a simple trend chart if data exists
            if not df_past.empty:
                col_chart, col_table = st.columns([1, 1])
                
                with col_chart:
                    st.markdown("**Temperature & Humidity Trends**")
                    # Set date as index so Streamlit automatically graphs it over time
                    chart_data = df_past.set_index("Date")[["Temperature (°C)", "Humidity (%)"]]
                    st.line_chart(chart_data)
                
                with col_table:
                    st.markdown("**Recent Observations**")
                    st.dataframe(df_past, hide_index=True, use_container_width=True, height=350)
        else:
            st.info(f"Not enough data to calculate averages or draw charts for {selected_city}.")

    # --- TAB 2: LOG NEW DATA ---
    with tab_add:
        st.subheader("➕ Add New Observation")
        st.markdown(f"Enter the latest environmental readings for **{selected_city}**.")
        
        with st.form("data_form", clear_on_submit=True):
            obs_date = st.date_input("Date", datetime.date.today())
            
            c1, c2 = st.columns(2)
            temp = c1.number_input("Temperature (°C)", value=30.0, step=0.5)
            rain = c2.number_input("Rainfall (mm)", value=0.0, step=1.0)
            
            c3, c4 = st.columns(2)
            wind = c3.number_input("Wind Speed (km/h)", value=10.0, step=1.0)
            hum = c4.number_input("Humidity (%)", value=50.0, step=1.0)
            
            if st.form_submit_button("Submit Data", type="primary"):
                # Save Data to PostgreSQL
                cur.execute(
                    """INSERT INTO sensor_observations (station_id, obs_date, temperature, humidity, wind_speed, rainfall) 
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING obs_id""",
                    (current_station_id, obs_date, temp, hum, wind, rain)
                )
                new_obs_id = cur.fetchone()[0]
                
                # AI Logic 
                severity = "EXTREME" if temp >= 40 else "HIGH" if temp >= 37 else "MODERATE" if temp >= 35 else "LOW"
                msg = f"AI Alert: {severity} conditions detected."
                
                cur.execute("INSERT INTO trial_runs (model_id, obs_id, region_id, forecast_period) VALUES (1, %s, 1, '24h') RETURNING trial_id", (new_obs_id,))
                cur.execute("INSERT INTO heatwave_alerts (trial_id, severity, message) VALUES (%s, %s, %s)", (cur.fetchone()[0], severity, msg))
                conn.commit()
                
                st.success(f"Data securely saved for {selected_city}! AI Opinion generated.")
                st.rerun()

    # --- TAB 3: MANAGE RECORDS ---
    with tab_manage:
        st.subheader("🗑️ Delete a Record")
        if not df_past.empty:
            st.warning("Warning: Deleting a record will automatically cascade and delete its associated AI alerts from the database.")
            with st.form("delete_form"):
                col1, col2 = st.columns([3, 1])
                
                # Use the actual database Record ID for deleting, but show it nicely to the user
                db_ids = df_past["Record ID"].tolist()
                record_to_delete = col1.selectbox("Select Database Record ID to remove:", options=db_ids)
                
                if col2.form_submit_button("Delete Record"):
                    cur.execute("DELETE FROM sensor_observations WHERE obs_id = %s", (record_to_delete,))
                    conn.commit()
                    st.success(f"Record {record_to_delete} deleted successfully!")
                    st.rerun() 
        else:
            st.info(f"No records available to delete for {selected_city}.")

except Exception as e:
    st.error(f"Database error: {e}")
