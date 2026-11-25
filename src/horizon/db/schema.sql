-- Horizon v0.1 physical schema for LDD v0.2.
-- Load spatial and configure longitude/latitude (x/y) axis order before use.
-- Timestamp input should include a UTC offset. DuckDB stores microsecond instants.
-- Elevation uses EGM2008 MSL meters. Operational altitude uses AGL meters.

BEGIN TRANSACTION;

CREATE SEQUENCE IF NOT EXISTS data_source_id_seq;
CREATE SEQUENCE IF NOT EXISTS ingestion_run_id_seq;
CREATE SEQUENCE IF NOT EXISTS building_id_seq;
CREATE SEQUENCE IF NOT EXISTS terrain_id_seq;
CREATE SEQUENCE IF NOT EXISTS airspace_restriction_id_seq;
CREATE SEQUENCE IF NOT EXISTS controlled_airspace_id_seq;
CREATE SEQUENCE IF NOT EXISTS aircraft_id_seq;
CREATE SEQUENCE IF NOT EXISTS weather_sensor_id_seq;
CREATE SEQUENCE IF NOT EXISTS uas_facility_grid_id_seq;

CREATE TABLE IF NOT EXISTS data_source (
    source_id BIGINT PRIMARY KEY DEFAULT nextval('data_source_id_seq'),
    source_name VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    source_uri VARCHAR,
    source_description VARCHAR
);

CREATE TABLE IF NOT EXISTS ingestion_run (
    ingestion_id BIGINT PRIMARY KEY DEFAULT nextval('ingestion_run_id_seq'),
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status VARCHAR NOT NULL,
    UNIQUE (ingestion_id, source_id),
    CHECK (completed_at >= started_at)
);

-- Each imported record references the ingestion run and its source as a pair.
CREATE TABLE IF NOT EXISTS building (
    feature_id BIGINT PRIMARY KEY DEFAULT nextval('building_id_seq'),
    geometry GEOMETRY('EPSG:4326') NOT NULL,
    height_m DOUBLE CHECK (height_m >= 0),
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id)
);

-- Coverage is a vector footprint. The CRS and datum describe the external raster.
CREATE TABLE IF NOT EXISTS terrain (
    terrain_id BIGINT PRIMARY KEY DEFAULT nextval('terrain_id_seq'),
    coverage GEOMETRY('EPSG:4326') NOT NULL,
    raster_uri VARCHAR NOT NULL,
    horizontal_crs VARCHAR NOT NULL,
    vertical_datum VARCHAR NOT NULL,
    resolution_m DOUBLE CHECK (resolution_m > 0),
    source VARCHAR,
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id)
);

CREATE TABLE IF NOT EXISTS airspace_restriction (
    restriction_id BIGINT PRIMARY KEY DEFAULT nextval('airspace_restriction_id_seq'),
    name VARCHAR,
    geometry GEOMETRY('EPSG:4326') NOT NULL,
    altitude_reference VARCHAR,
    restriction_type VARCHAR,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id),
    CHECK (end_time >= start_time)
);

CREATE TABLE IF NOT EXISTS controlled_airspace (
    airspace_id BIGINT PRIMARY KEY DEFAULT nextval('controlled_airspace_id_seq'),
    name VARCHAR,
    geometry GEOMETRY('EPSG:4326') NOT NULL,
    altitude_reference VARCHAR,
    airspace_class VARCHAR,
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id)
);

-- Add cycle bounds to databases initialized before NASR ingestion.
ALTER TABLE controlled_airspace ADD COLUMN IF NOT EXISTS valid_from TIMESTAMPTZ;
ALTER TABLE controlled_airspace ADD COLUMN IF NOT EXISTS valid_to TIMESTAMPTZ;

-- Informational FAA UAS Facility Map grids and their heights above ground.
CREATE TABLE IF NOT EXISTS uas_facility_grid (
    grid_id BIGINT PRIMARY KEY DEFAULT nextval('uas_facility_grid_id_seq'),
    geometry GEOMETRY('EPSG:4326') NOT NULL,
    ceiling_agl_m DOUBLE CHECK (ceiling_agl_m >= 0),
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id)
);

CREATE TABLE IF NOT EXISTS aircraft (
    aircraft_id BIGINT PRIMARY KEY DEFAULT nextval('aircraft_id_seq'),
    aircraft_type VARCHAR,
    manufacturer VARCHAR,
    model VARCHAR,
    identifier VARCHAR,
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id)
);

-- The timestamp in the key allows multiple readings per aircraft as shown in the ERD.
CREATE TABLE IF NOT EXISTS aircraft_telemetry (
    aircraft_id BIGINT NOT NULL REFERENCES aircraft (aircraft_id),
    timestamp TIMESTAMPTZ NOT NULL,
    location GEOMETRY('EPSG:4326') NOT NULL,
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id),
    PRIMARY KEY (aircraft_id, timestamp),
    CHECK (ST_GeometryType(location) = 'POINT')
);

CREATE TABLE IF NOT EXISTS weather_sensor (
    sensor_id BIGINT PRIMARY KEY DEFAULT nextval('weather_sensor_id_seq'),
    name VARCHAR,
    location GEOMETRY('EPSG:4326') NOT NULL,
    elevation_m DOUBLE,
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id),
    CHECK (ST_GeometryType(location) = 'POINT')
);

CREATE TABLE IF NOT EXISTS weather_observations (
    observed_at TIMESTAMPTZ NOT NULL,
    sensor_id BIGINT NOT NULL REFERENCES weather_sensor (sensor_id),
    precipitation DOUBLE CHECK (precipitation >= 0),
    humidity DOUBLE CHECK (humidity >= 0),
    temperature DOUBLE,
    visibility DOUBLE CHECK (visibility >= 0),
    source_id BIGINT NOT NULL REFERENCES data_source (source_id),
    source_record_id VARCHAR,
    acquired_at TIMESTAMPTZ NOT NULL,
    ingestion_id BIGINT NOT NULL,
    FOREIGN KEY (ingestion_id, source_id) REFERENCES ingestion_run (ingestion_id, source_id),
    PRIMARY KEY (observed_at, sensor_id)
);

COMMIT;
