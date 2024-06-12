CREATE EXTENSION postgis;

CREATE TABLE gps_records (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMP NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geom GEOMETRY(Point, 4326)
);

CREATE OR REPLACE FUNCTION update_geom() RETURNS TRIGGER AS $$
BEGIN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_geom
BEFORE INSERT ON gps_records
FOR EACH ROW
EXECUTE FUNCTION update_geom();



INSERT INTO gps_records (recorded_at, latitude, longitude) VALUES 
('2024-06-11 10:00:00', 12.9716, 77.5946), -- Bangalore
('2024-06-11 10:30:00', 12.8210893,77.4105730), -- Bidadi
('2024-06-11 10:45:00', 12.7460862,77.2737759), -- Ramanagara
('2024-06-11 11:00:00', 12.6550243,77.1759088), -- Channapatna
('2024-06-11 11:30:00', 12.5436044,76.8944748), -- Mandya
('2024-06-11 11:45:00', 12.4124295,76.6995819), -- Srirangapatna
('2024-06-11 12:00:00', 12.2958, 76.6394); -- Mysore

SELECT id, recorded_at, latitude, longitude, ST_AsText(geom) AS geom FROM gps_records;

