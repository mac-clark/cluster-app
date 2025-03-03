import os
import ipywidgets as widgets
from IPython.display import display, clear_output

# Import your modules
import hotspot
import visualize

def run_clustering(b):
    with output:
        clear_output()
        # Ensure a file was uploaded
        if not file_uploader.value:
            print("Please upload a .csv or .xlsx file.")
            return
        
        # Save the uploaded file locally (Binder runs in a temporary directory)
        # Access the first uploaded file (assuming multiple=False)
        uploaded_file = file_uploader.value[0]
        uploaded_filename = uploaded_file['name']
        file_data = uploaded_file['content']
        
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        input_filepath = os.path.join(temp_dir, uploaded_filename)
        with open(input_filepath, "wb") as f:
            f.write(file_data)
        print(f"File saved as: {input_filepath}")
        
        # Get the radius input from the widget
        try:
            radius = float(radius_input.value)
        except ValueError:
            print("Please enter a valid numeric radius.")
            return
        
        # Set up output directory for results
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Run the clustering logic (hotspot)
        print("Running clustering...")
        hotspot.main(input_filepath, radius, output_dir)
        
        # Step 2: Run the visualization (visualize)
        summary_file = os.path.join(output_dir, "cluster_summary.csv")
        output_map = os.path.join(output_dir, "cluster_map.html")
        print("Creating map visualization...")
        visualize.main(summary_file, radius, output_map)
        
        print("\nProcessing complete!")
        print(f"Cluster summary saved to: {os.path.join(output_dir, 'cluster_summary.csv')}")
        print(f"Map saved to: {output_map}")
        print("\nYou can open the HTML file to view the interactive map.")

# Create widgets for file upload and radius input
file_uploader = widgets.FileUpload(
    accept=".csv,.xlsx",  # Acceptable file types
    multiple=False,
    description="Upload Data"
)
radius_input = widgets.Text(
    value="5",
    description="Radius (miles):",
    placeholder="Enter clustering radius"
)
run_button = widgets.Button(
    description="Run Clustering",
    button_style="success"
)
output = widgets.Output()

# Set up the button click event handler
run_button.on_click(run_clustering)

# Display the interface
display(widgets.VBox([file_uploader, radius_input, run_button, output]))
