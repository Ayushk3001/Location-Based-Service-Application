import psycopg2
from datetime import datetime
import random
import schedule
import time

# Database connection parameters
DB_NAME = 'geofence'
DB_USER = 'postgres'
DB_PASS = '1501'
DB_HOST = 'localhost'
DB_PORT = 5432

# Enable PostGIS extension
def enable_postgis():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        c = conn.cursor()
        c.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
        conn.commit()
    except Exception as e:
        print(f"Error enabling PostGIS: {e}")
    finally:
        conn.close()

enable_postgis()

# Set up the database
def setup_database():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL UNIQUE,
                timestamp TIMESTAMPTZ NOT NULL,
                geom GEOMETRY(Point, 4326)
            );
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS geofence (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                geom GEOMETRY(Polygon, 4326)
            );
        ''')
        conn.commit()
    except Exception as e:
        print(f"Error setting up database: {e}")
    finally:
        conn.close()

setup_database()

# Insert geofence area (simple square around Bangalore)
def insert_geofence():
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        c = conn.cursor()
        geofence_wkt = 'POLYGON((77.5946 12.9716, 77.6956 12.9716, 77.6956 13.0716, 77.5946 13.0716, 77.5946 12.9716))'
        c.execute('''
            INSERT INTO geofence (name, geom)
            VALUES (%s, ST_GeomFromText(%s))
            ON CONFLICT DO NOTHING;
        ''', ('Bangalore Geofence', geofence_wkt))
        conn.commit()
    except Exception as e:
        print(f"Error inserting geofence: {e}")
    finally:
        conn.close()

insert_geofence()

# Function to get user coordinates 
def get_user_coordinates(user_id):
    blr_lat = 12.9716
    blr_lon = 77.5946

    lat_range = (blr_lat - 0.1, blr_lat + 0.1)
    lon_range = (blr_lon - 0.1, blr_lon + 0.1)

    latitude = random.uniform(*lat_range)
    longitude = random.uniform(*lon_range)
    
    return latitude, longitude

# Function to store coordinates to the database
def store_coordinates_to_db(user_id):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    latitude, longitude = get_user_coordinates(user_id)

    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        c = conn.cursor()
        geom = f'SRID=4326;POINT({longitude} {latitude})'
        c.execute('''
            INSERT INTO user_data (user_id, timestamp, geom) 
            VALUES (%s, %s, ST_GeomFromText(%s))
            ON CONFLICT (user_id)
            DO UPDATE SET timestamp = EXCLUDED.timestamp, geom = EXCLUDED.geom
        ''', (user_id, timestamp, geom))
        conn.commit()

        # Check if the user is within the geofence
        c.execute('''
            SELECT name 
            FROM geofence 
            WHERE ST_Contains(geom, ST_GeomFromText(%s))
        ''', (geom,))
        result = c.fetchone()
        
        if result:
            print(f'User {user_id} is within the geofence: {result[0]} at {timestamp}')
        else:
            print(f'User {user_id} is outside the geofence at {timestamp}')
    except Exception as e:
        print(f"Error storing coordinates to db: {e}")
    finally:
        conn.close()

# Function to schedule tasks for multiple users
def schedule_user_tasks():
    user_ids = [1, 2, 3, 4, 5]  # List of user IDs
    for user_id in user_ids:
        schedule.every(1).minutes.do(store_coordinates_to_db, user_id=user_id)

# Main script to set up database and schedule tasks
setup_database()
schedule_user_tasks()

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(1)
