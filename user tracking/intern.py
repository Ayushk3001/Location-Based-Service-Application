import psycopg2
from datetime import datetime
import random
import schedule
import time

# Database connection parameters
DB_NAME = 'db'
DB_USER = 'postgres'
DB_PASS = '1501'
DB_HOST = 'localhost'
DB_PORT = 5432

# Enable PostGIS extension
def enable_postgis():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
    c = conn.cursor()
    c.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    conn.commit()
    conn.close()

enable_postgis()

# Set up the database
def setup_database():
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
    conn.commit()
    conn.close()

setup_database()

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
    conn.close()

    print(f'Stored/updated data for user {user_id}: {timestamp}, {latitude}, {longitude}')

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
