import pandas as pd
from geopy.geocoders import Nominatim
from sklearn.cluster import DBSCAN
import numpy as np
import os
import json
import sys

def load_data(file_path, zip_col, inactive_col=None):
    """Load client data and filter inactive clients."""
    if file_path.endswith('.csv'):
        data = pd.read_csv(file_path, dtype={zip_col: str})  # Preserve leading zeros
    elif file_path.endswith('.xlsx'):
        data = pd.read_excel(file_path, dtype={zip_col: str})
    else:
        raise ValueError("Unsupported file format. Please provide a .csv or .xlsx file.")

    if inactive_col and inactive_col in data.columns:
        data = data[data[inactive_col].str.lower() != 'yes']  # Filter out inactive clients
        print(f"Filtered inactive clients. Remaining rows: {len(data)}")
    
    zip_codes = data[zip_col].dropna().unique()  # Unique ZIP codes only
    print(f"Loaded {len(zip_codes)} unique ZIP codes.")
    return zip_codes

def geocode_zip_codes(zip_codes, cache_file="geocode_cache.json"):
    """Convert ZIP codes to latitude and longitude with caching."""
    geolocator = Nominatim(user_agent="zip_geocoding")
    lat_lng = {}

    # Load cache if it exists (cache persists in the repo)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            lat_lng = json.load(f)

    new_cache = False
    total = len(zip_codes)  # For progress tracking

    if total == 0:
        sys.stdout.write("\rProgress: 1.0")
        sys.stdout.flush()
        return lat_lng

    for i, zip_code in enumerate(zip_codes):
        if zip_code in lat_lng:
            continue  # Skip if already cached

        try:
            location = geolocator.geocode(f"{zip_code}, USA", timeout=10)
            if location:
                lat_lng[zip_code] = (location.latitude, location.longitude)
            else:
                print(f"\nFailed to geocode ZIP code: {zip_code}")
        except Exception as e:
            print(f"\nError geocoding ZIP code {zip_code}: {e}")

        new_cache = True

        # Update progress on the same line
        progress = (i + 1) / total
        sys.stdout.write(f"\rProgress: {progress:.2f}")
        sys.stdout.flush()

    # Save updated cache (persisted in the repo if you commit changes)
    if new_cache:
        with open(cache_file, 'w') as f:
            json.dump(lat_lng, f)

    sys.stdout.write("\rProgress: 1.0\n")
    sys.stdout.flush()
    return lat_lng

def cluster_lat_lng(lat_lng, radius_miles):
    """Cluster latitude and longitude data using DBSCAN."""
    coords = np.array(list(lat_lng.values()))
    radius_km = radius_miles * 1.60934  # Convert miles to kilometers
    eps = radius_km / 6371.0  # Convert kilometers to radians

    clustering = DBSCAN(eps=eps, min_samples=2, metric='haversine').fit(np.radians(coords))
    clusters = clustering.labels_

    # Map clusters back to ZIP codes
    zip_cluster_map = {zip_code: cluster for zip_code, cluster in zip(lat_lng.keys(), clusters)}

    # Update progress (single update)
    sys.stdout.write("\rProgress: 0.75 (Clustering completed)\n")
    sys.stdout.flush()
    return zip_cluster_map

def summarize_clusters(zip_cluster_map, lat_lng):
    """Summarize clusters by calculating centroid and customer count."""
    cluster_summary = {}

    for zip_code, cluster_id in zip_cluster_map.items():
        if cluster_id == -1:  # Skip noise
            continue
        if cluster_id not in cluster_summary:
            cluster_summary[cluster_id] = {
                "zip_codes": [],
                "latitudes": [],
                "longitudes": []
            }
        cluster_summary[cluster_id]["zip_codes"].append(zip_code)
        cluster_summary[cluster_id]["latitudes"].append(lat_lng[zip_code][0])
        cluster_summary[cluster_id]["longitudes"].append(lat_lng[zip_code][1])

    # Calculate centroids and cluster sizes
    summary = []
    for cluster_id, data in cluster_summary.items():
        center_lat = np.mean(data["latitudes"])
        center_lon = np.mean(data["longitudes"])
        summary.append({
            "Cluster": cluster_id,
            "Number of ZIP Codes": len(data["zip_codes"]),
            "Center Latitude": center_lat,
            "Center Longitude": center_lon
        })

    sys.stdout.write("\rProgress: 0.90 (Summary completed)\n")
    sys.stdout.flush()
    return pd.DataFrame(summary)

def main(file_path, radius_miles, output_dir="."):
    # Ensure the output directory exists (temp/session files)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    zip_col = "Billing Zip"
    inactive_col = "Inactive"

    # Step 1: Load and filter data
    zip_codes = load_data(file_path, zip_col, inactive_col)

    # Step 2: Geocode ZIP codes
    lat_lng = geocode_zip_codes(zip_codes)

    # Step 3: Cluster data
    zip_cluster_map = cluster_lat_lng(lat_lng, radius_miles)

    # Step 4: Summarize clusters
    cluster_summary = summarize_clusters(zip_cluster_map, lat_lng)

    # Save results (in session-only folder)
    cluster_summary_file = os.path.join(output_dir, 'cluster_summary.csv')
    clustered_zip_file = os.path.join(output_dir, 'clustered_zip_codes.csv')

    pd.DataFrame.from_dict(zip_cluster_map, orient='index', columns=['Cluster']).to_csv(clustered_zip_file)
    cluster_summary.to_csv(cluster_summary_file, index=False)

    sys.stdout.write("\rProgress: 1.0\n")
    sys.stdout.flush()
    print(f"Clustering completed. Results saved to {clustered_zip_file} and {cluster_summary_file}.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python hotspot.py <file_path> <radius_miles> <output_dir>")
        sys.exit(1)

    file_path = sys.argv[1]
    radius_miles = float(sys.argv[2])
    output_dir = sys.argv[3]

    main(file_path, radius_miles, output_dir)
