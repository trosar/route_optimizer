from flask import Flask, render_template, request
import requests
import json
import io
import csv
import os

app = Flask(__name__)

# --- Configuration Variables ---
APP_PASSWORD = os.getenv("APP_PASSWORD")
SHEET_CSV_URL = os.getenv("SHEET_CSV_URL")
DEFAULT_CHURCH_ADDRESS = "22209 58th Ave W, Mountlake Terrace, WA 98043"
DEFAULT_CHURCH_COORDS = (47.797121, -122.310876)
coordinate_cache = {}

# Column Indices (based on above CSV file)
ADDRESS_COL_INDEX = 3 # Column D (4th column)
LAT_COL_INDEX = 5     # Column F (6th column)
LON_COL_INDEX = 6     # Column G (7th column)



# --- Core Logic Functions ---
def get_addresses_from_sheet(url):
    """Fetches addresses and coordinates from the Google Sheet and caches it"""
    global coordinate_cache
    
    # Reset cache for fresh run
    coordinate_cache = {} 
    
    try:
        response = requests.get(url)
        response.raise_for_status() 
        
        csv_data = io.StringIO(response.text)
        reader = csv.reader(csv_data)
        next(reader, None) # Skip the header row
        
        addresses = []
        for row in reader:
            if len(row) > LON_COL_INDEX:
                address = row[ADDRESS_COL_INDEX].strip()
                
                try:
                    lat = float(row[LAT_COL_INDEX].strip())
                    lon = float(row[LON_COL_INDEX].strip())
                    
                    if address:
                        coordinate_cache[address] = (lat, lon)
                        addresses.append(address)
                        
                except ValueError:
                    # Skip row with bad coordinate data
                    continue 
                
        return addresses

    except requests.exceptions.RequestException as e:
        # Return a tuple with an error message to handle it in the route
        return f"Error fetching sheet data: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def get_coordinates(address):
    """Retrieves coordinates from the global cache."""
    return coordinate_cache.get(address)


def get_travel_time(coord1, coord2):
    """Retrieves actual travel time in minutes between two coordinates using OSRM."""
    if not coord1 or not coord2:
        return float('inf')
    
    url = f"http://router.project-osrm.org/route/v1/driving/{coord1[1]},{coord1[0]};{coord2[1]},{coord2[0]}?overview=false"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data and data['routes']:
            duration_seconds = data['routes'][0]['duration'] 
            return duration_seconds / 60
        else:
            return float('inf') 
            
    except requests.exceptions.RequestException:
        return float('inf')
    except json.JSONDecodeError:
        return float('inf')


def plan_trips(church_address, pickup_addresses, fixed_time_limit_minutes, wait_time_minutes):
    """Plans pickup trips starting and ending at the church within a time limit."""
    
    warehouse_coords = get_coordinates(church_address)
    delivery_coords = coordinate_cache
    
    if not warehouse_coords:
        return f"Error: Church address '{church_address}' coordinates not found in cache."

    valid_pickup_addresses = [addr for addr in pickup_addresses if addr in delivery_coords]

    if not valid_pickup_addresses:
        return "Warning: No valid pickup addresses!!!"

    unvisited_addresses = list(valid_pickup_addresses)
    trips = []
    trip_number = 1

    while unvisited_addresses:
        current_trip = [church_address]
        current_trip_time = 0
        last_location = church_address

        while unvisited_addresses:
            best_next_address = None
            min_travel_time_to_next = float('inf')

            current_location_coords = delivery_coords.get(last_location) if last_location != church_address else warehouse_coords
            if not current_location_coords: break 

            for address in unvisited_addresses:
                next_location_coords = delivery_coords.get(address)
                if next_location_coords:
                    time_to_next = get_travel_time(current_location_coords, next_location_coords)
                    
                    if time_to_next < min_travel_time_to_next:
                        min_travel_time_to_next = time_to_next
                        best_next_address = address

            if best_next_address:
                next_location_coords = delivery_coords[best_next_address]

                travel_and_wait_for_next = min_travel_time_to_next + wait_time_minutes

                time_to_warehouse_from_next = get_travel_time(next_location_coords, warehouse_coords)

                total_trip_time_if_added = current_trip_time + travel_and_wait_for_next + time_to_warehouse_from_next

                if total_trip_time_if_added <= fixed_time_limit_minutes:
                    current_trip.append(best_next_address)
                    current_trip_time += travel_and_wait_for_next
                    unvisited_addresses.remove(best_next_address)
                    last_location = best_next_address
                else:
                    break
            else:
                break

        trip_end_location_coords = delivery_coords.get(last_location) if last_location != church_address else warehouse_coords
        return_time = get_travel_time(trip_end_location_coords, warehouse_coords) if trip_end_location_coords and warehouse_coords else 0

        current_trip.append(church_address)

        trips.append({
            "trip_number": trip_number,
            "addresses": current_trip,
            "total_estimated_time": current_trip_time + return_time
        })
        trip_number += 1

    return trips

# --- Flask Route Handlers ---

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 1. Get user input from the form
        passwd = request.form.get('passwd', "NOT_SET")

        church_address = request.form.get('church_address', DEFAULT_CHURCH_ADDRESS)
        try:
            time_limit = int(request.form['time_limit'])
            wait_time = int(request.form['wait_time'])
        except ValueError:
            return render_template('index.html', error="Time limit and Wait time must be integers.", trips=None)

        # 2. Fetch data from Google Sheet
        all_addresses = get_addresses_from_sheet(SHEET_CSV_URL)

        # Check for sheet fetching errors
        if isinstance(all_addresses, str):
             # It's an error message string
            return render_template('index.html', error=all_addresses, trips=None)

        # 3. If Church Address is not in the CSV sheet, then use defaults
        if church_address not in coordinate_cache:
            coordinate_cache[church_address] = DEFAULT_CHURCH_COORDS
            church_address = DEFAULT_CHURCH_ADDRESS
        
        # Remove church address from all addresses
        pickup_addresses = [addr for addr in all_addresses if addr.strip() != church_address.strip()]
        
        if passwd != APP_PASSWORD:
            #return render_template('index.html', error="Incorrect password.", trips=None)
            pickup_addresses = {}

        # 4. Run the trip planning algorithm
        trip_plan = plan_trips(church_address, pickup_addresses, time_limit, wait_time)

        # 5. Handle trip planning Errors/Warnings
        if isinstance(trip_plan, str):
            return render_template('index.html', error=trip_plan, trips=None)
        
        # 6. Format results for display
        results = {
            'limit': time_limit,
            'wait': wait_time,
            'total_trips': len(trip_plan),
            'trips': trip_plan
        }

        return render_template('index.html', results=results)

    # Initial GET request (show an empty form)
    return render_template('index.html', results=None)

if __name__ == '__main__':
    # Run the app with Flask
    app.run(debug=True)
