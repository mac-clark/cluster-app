import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import os
import sys
import threading


class ClusterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Cluster Visualizer")
        self.root.geometry("500x400")

        # Input file
        self.file_label = tk.Label(root, text="Select Input File:")
        self.file_label.pack(pady=5)

        self.file_button = tk.Button(root, text="Choose File", command=self.select_file)
        self.file_button.pack(pady=5)

        self.file_path = tk.StringVar()
        self.file_entry = tk.Entry(root, textvariable=self.file_path, width=40)
        self.file_entry.pack(pady=5)

        # Radius input
        self.radius_label = tk.Label(root, text="Enter Radius (miles):")
        self.radius_label.pack(pady=5)

        self.radius_entry = tk.Entry(root, width=10)
        self.radius_entry.pack(pady=5)

        # Output directory
        self.output_label = tk.Label(root, text="Select Output Directory:")
        self.output_label.pack(pady=5)

        self.output_button = tk.Button(root, text="Choose Directory", command=self.select_output_dir)
        self.output_button.pack(pady=5)

        self.output_path = tk.StringVar()
        self.output_entry = tk.Entry(root, textvariable=self.output_path, width=40)
        self.output_entry.pack(pady=5)

        # Run button
        self.run_button = tk.Button(root, text="Run", command=self.run_process)
        self.run_button.pack(pady=10)

        # Text area for updates
        self.status_text = tk.Text(root, height=10, width=60, state='disabled')
        self.status_text.pack(pady=10)

    def select_file(self):
        filetypes = (('Excel files', '*.xlsx'), ('CSV files', '*.csv'), ('All files', '*.*'))
        file_path = filedialog.askopenfilename(title="Open a file", filetypes=filetypes)
        self.file_path.set(file_path)

    def select_output_dir(self):
        dir_path = filedialog.askdirectory(title="Select Output Directory")
        self.output_path.set(dir_path)

    def append_status(self, message):
        """Append a status message to the text area."""
        self.status_text.configure(state='normal')  # Enable editing
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)  # Scroll to the end
        self.status_text.configure(state='disabled')  # Disable editing

    def run_process(self):
        file_path = self.file_path.get()
        radius = self.radius_entry.get()
        output_dir = self.output_path.get()

        if not file_path or not radius or not output_dir:
            messagebox.showerror("Error", "Please fill out all fields.")
            return

        try:
            radius = float(radius)
        except ValueError:
            messagebox.showerror("Error", "Radius must be a valid number.")
            return

        self.append_status("Starting process...")

        def background_task():
            python_exec = sys.executable
            try:
                # Run geocoding and clustering
                self.append_status("Running geocoding and clustering...")
                self.append_status("Please wait, geocoding may take a few minutes.")
                subprocess.run(
                    [python_exec, "hotspot.py", file_path, str(radius), output_dir],
                    check=True,
                )

                # Run visualization
                self.append_status("Generating visualization...")
                self.append_status("Please wait, generating the map may take a minute.")
                cluster_summary = os.path.join(output_dir, "cluster_summary.csv")
                map_output = os.path.join(output_dir, "cluster_map.html")
                subprocess.run(
                    [python_exec, "visualize.py", cluster_summary, str(radius), map_output],
                    check=True,
                )

                # Completion
                self.append_status("Process complete! Results saved.")
                messagebox.showinfo("Success", f"Process completed! Map saved to {map_output}")
            except subprocess.CalledProcessError as e:
                self.append_status(f"Error occurred: {e}")
                messagebox.showerror("Error", f"An error occurred: {e}")

        threading.Thread(target=background_task, daemon=True).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ClusterApp(root)
    root.mainloop()