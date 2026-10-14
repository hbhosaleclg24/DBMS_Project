-- Drop old tables to start fresh without errors
DROP TABLE IF EXISTS user_feedback CASCADE;
DROP TABLE IF EXISTS heatwave_alerts CASCADE;
DROP TABLE IF EXISTS trial_runs CASCADE;
DROP TABLE IF EXISTS ai_models CASCADE;
DROP TABLE IF EXISTS sensor_observations CASCADE;
DROP TABLE IF EXISTS geospatial_regions CASCADE;
DROP TABLE IF EXISTS climate_sensors CASCADE;
DROP VIEW IF EXISTS observation_log CASCADE;

-- 1. CLIMATE SENSORS TABLE (Now with the 6 specific cities)
CREATE TABLE climate_sensors (
    station_id SERIAL PRIMARY KEY,
    location VARCHAR(100) NOT NULL,
    elevation DECIMAL(6, 2), 
    status VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 2. GEOSPATIAL REGIONS TABLE (Kept for your ER diagram)
CREATE TABLE geospatial_regions (
    region_id SERIAL PRIMARY KEY,
    boundary_region VARCHAR(100) NOT NULL,
    major_cities TEXT,
    vulnerability_index DECIMAL(3, 2)
);

-- 3. SENSOR OBSERVATIONS TABLE (Updated to include manual DATE)
CREATE TABLE sensor_observations (
    obs_id SERIAL PRIMARY KEY,
    station_id INT REFERENCES climate_sensors(station_id) ON DELETE CASCADE,
    obs_date DATE NOT NULL, -- Lets the user input the exact date
    temperature DECIMAL(4, 1) NOT NULL,
    humidity DECIMAL(5, 2),
    wind_speed DECIMAL(5, 2),
    rainfall DECIMAL(5, 2)
);

-- 4. AI MODELS TABLE
CREATE TABLE ai_models (
    model_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    version VARCHAR(20) NOT NULL,
    accuracy DECIMAL(5, 2)
);

-- 5. TRIAL RUNS TABLE
CREATE TABLE trial_runs (
    trial_id SERIAL PRIMARY KEY,
    model_id INT REFERENCES ai_models(model_id) ON DELETE CASCADE,
    obs_id INT REFERENCES sensor_observations(obs_id) ON DELETE CASCADE,
    region_id INT REFERENCES geospatial_regions(region_id) ON DELETE CASCADE,
    forecast_period VARCHAR(50) NOT NULL,
    confidence_level DECIMAL(5, 2)
);

-- 6. HEATWAVE ALERTS TABLE
CREATE TABLE heatwave_alerts (
    alert_id SERIAL PRIMARY KEY,
    trial_id INT REFERENCES trial_runs(trial_id) ON DELETE CASCADE,
    severity VARCHAR(20),
    message TEXT NOT NULL
);

-- 7. USER FEEDBACK TABLE
CREATE TABLE user_feedback (
    feedback_id SERIAL PRIMARY KEY,
    alert_id INT REFERENCES heatwave_alerts(alert_id) ON DELETE CASCADE,
    rating INT,
    comments TEXT
);

-- INSERT YOUR 6 CITIES
INSERT INTO climate_sensors (location, elevation, status) VALUES 
('Mumbai', 14.50, 'ACTIVE'),
('Pune', 560.00, 'ACTIVE'),
('Satara', 742.00, 'ACTIVE'),
('Kolhapur', 569.00, 'ACTIVE'),
('Nagpur', 310.00, 'ACTIVE'),
('Nashik', 600.00, 'ACTIVE');

-- Insert one default Region and Model so the AI logic works
INSERT INTO geospatial_regions (boundary_region, major_cities, vulnerability_index) VALUES 
('Maharashtra Region', 'Mumbai, Pune, Nagpur', 8.50);
INSERT INTO ai_models (name, version, accuracy) VALUES 
('HeatwavePredictNet', 'v1.2', 88.50);

-- View for easy reading
CREATE VIEW observation_log AS
SELECT 
    so.obs_id AS "Sr. No.",
    cs.location AS "Station",
    so.obs_date AS "Date",
    so.temperature AS "Temperature (°C)",
    so.rainfall AS "Rainfall (mm)",
    so.wind_speed AS "Wind Speed (km/h)",
    so.humidity AS "Humidity (%)",
    ha.severity AS "AI Severity"
FROM sensor_observations so
JOIN climate_sensors cs ON so.station_id = cs.station_id
LEFT JOIN trial_runs tr ON so.obs_id = tr.obs_id
LEFT JOIN heatwave_alerts ha ON tr.trial_id = ha.trial_id;
