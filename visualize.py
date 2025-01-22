import pandas as pd
import folium
from geopy.geocoders import Nominatim
import os


def load_summary(summary_file):
    """Load the cluster summary CSV file."""
    if not os.path.exists(summary_file):
        raise FileNotFoundError(f"Summary file '{summary_file}' not found.")

    print("Progress: 10% - Loading cluster summary data...")
    return pd.read_csv(summary_file)


def create_cluster_map(summary_data, radius_miles, output_file):
    """Generate a map with cluster visualizations."""
    print("Progress: 20% - Initializing the map...")
    map_center = [39.8283, -98.5795]  # Center of the USA
    cluster_map = folium.Map(location=map_center, zoom_start=5)

    geolocator = Nominatim(user_agent="cluster_visualizer")
    total_clusters = len(summary_data)

    if total_clusters == 0:  # Handle the case where there are no clusters
        print("Progress: 1.0")
        return

    def get_marker_color(num_zip_codes):
        """Determine marker color based on the number of ZIP codes."""
        if num_zip_codes > 20:
            return "red"
        elif num_zip_codes > 10:
            return "orange"
        else:
            return "blue"

    for i, (_, row) in enumerate(summary_data.iterrows()):
        cluster_id = row['Cluster']
        num_zip_codes = row['Number of ZIP Codes']
        latitude = row['Center Latitude']
        longitude = row['Center Longitude']

        # Reverse geocode to get a location name
        try:
            location = geolocator.reverse((latitude, longitude), timeout=10)
            location_name = location.raw['address'].get('city', location.raw['address'].get('town', "Unknown Location"))
        except Exception:
            location_name = "Unknown Location"

        # Add a proportional radius to match input radius
        popup_text = (
            f"<div style='width: 250px; font-size: 14px;'>"
            f"<b>Cluster {cluster_id}</b><br>"
            f"# of Customers: {num_zip_codes}<br>"
            f"Location: {location_name}<br>"
            f"Radius: {radius_miles} miles"
            f"</div>"
        )

        folium.Circle(
            location=[latitude, longitude],
            radius=radius_miles * 1609.34,  # Convert miles to meters
            popup=popup_text,
            tooltip=f"Cluster {cluster_id}",
            color=get_marker_color(num_zip_codes),
            fill=True,
            fill_opacity=0.6
        ).add_to(cluster_map)

        # Progress output
        progress = (i + 1) / total_clusters
        print(f"Progress: {progress:.2f}")

    # Add a legend to the map
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 250px; height: 160px; 
                background-color: white; z-index:9999; font-size:14px; 
                border:1px solid black; padding: 10px;">
        <b>Cluster Legend</b><br>
        <i style="background: red; width: 10px; height: 10px; border-radius: 50%; display: inline-block;"></i>
        High Volume (>20 Customers)<br>
        <i style="background: orange; width: 10px; height: 10px; border-radius: 50%; display: inline-block;"></i>
        Medium Volume (10-20 Customers)<br>
        <i style="background: blue; width: 10px; height: 10px; border-radius: 50%; display: inline-block;"></i>
        Low Volume (<10 Customers)<br>
        <hr>
        <b>Radius: {radius_miles} miles</b>
    </div>
    '''
    cluster_map.get_root().html.add_child(folium.Element(legend_html))

    # Save the map to an HTML file
    cluster_map.save(output_file)
    print(f"Progress: 1.0")


def calculate_metrics(summary_data):
    """Calculate and display key metrics."""
    total_clusters = len(summary_data)
    largest_cluster = summary_data.loc[summary_data['Number of ZIP Codes'].idxmax()]
    smallest_cluster = summary_data.loc[summary_data['Number of ZIP Codes'].idxmin()]

    print(f"Total Clusters: {total_clusters}")
    print(f"Largest Cluster: Cluster {largest_cluster['Cluster']} with {largest_cluster['Number of ZIP Codes']} Customers")
    print(f"Smallest Cluster: Cluster {smallest_cluster['Cluster']} with {smallest_cluster['Number of ZIP Codes']} Customers")


def main(summary_file, radius_miles, output_file):
    # Load the cluster summary data
    summary_data = load_summary(summary_file)

    # Generate the map
    create_cluster_map(summary_data, radius_miles, output_file)

    # Display key metrics
    calculate_metrics(summary_data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python visualize_clusters.py <summary_file> <radius_miles> <output_file>")
        sys.exit(1)

    summary_file = sys.argv[1]
    radius_miles = float(sys.argv[2])
    output_file = sys.argv[3]

    main(summary_file, radius_miles, output_file)