import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageFilter
import os
import numpy as np
import openai
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Set your OpenAI API key
openai.api_key = "your_openai_api_key_here"

# Global variables
loaded_image = None
filtered_image = None
image_label = None
hist_canvas = None

# Function to load an image
def load_image():
    global loaded_image, image_label
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg;*.jpeg;*.png;*.bmp"), ("All files", "*.*")]
    )
    if file_path:
        loaded_image = Image.open(file_path)
        tk_image = ImageTk.PhotoImage(loaded_image.resize((300, 300)))
        if image_label:
            image_label.config(image=tk_image)
            image_label.image = tk_image
        else:
            image_label = tk.Label(image_frame, image=tk_image)
            image_label.image = tk_image
            image_label.pack(pady=10)
        display_image_stats()
        display_histogram()

# Function to calculate and display image statistics
def display_image_stats():
    if not loaded_image:
        return
    image_array = np.array(loaded_image)
    mean = np.mean(image_array)
    std = np.std(image_array)
    min_val = np.min(image_array)
    max_val = np.max(image_array)
    stats_text = (f"Image Statistics:\n"
                  f"Mean: {mean:.2f}\n"
                  f"Standard Deviation: {std:.2f}\n"
                  f"Min Value: {min_val}\n"
                  f"Max Value: {max_val}")
    stats_label.config(text=stats_text)
    get_gpt_insights(mean, std, min_val, max_val)

# Function to display RGB histogram
def display_histogram():
    global hist_canvas
    if not loaded_image:
        return
    image_array = np.array(loaded_image)
    if len(image_array.shape) == 3:  # RGB image
        # Clear previous histogram
        for widget in hist_frame.winfo_children():
            widget.destroy()

        fig, ax = plt.subplots(figsize=(5, 2))
        for i, color in enumerate(['Red', 'Green', 'Blue']):
            ax.hist(image_array[:, :, i].ravel(), bins=256, color=color.lower(), alpha=0.5, label=f'{color} Channel')
        ax.set_title('RGB Histogram')
        ax.set_xlabel('Pixel Intensity')
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(False)
        plt.tight_layout()

        # Embed the plot in Tkinter
        hist_canvas = FigureCanvasTkAgg(fig, master=hist_frame)
        canvas_widget = hist_canvas.get_tk_widget()
        canvas_widget.pack(anchor="center")
        hist_canvas.draw()

# Function to get insights from GPT API based on image statistics
def get_gpt_insights(mean, std, min_val, max_val):
    try:
        messages = [
            {"role": "system", "content": "You are an assistant providing insights based on image statistics."},
            {"role": "user", "content": (
                f"Given the image statistics:\nMean: {mean:.2f}, Std: {std:.2f}, Min: {min_val}, Max: {max_val},\n"
                "please provide a detailed insight.")}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        insights = response["choices"][0]["message"]["content"].strip()
        insights_text.delete("1.0", tk.END)
        insights_text.insert(tk.END, insights)
    except Exception as e:
        insights_text.delete("1.0", tk.END)
        insights_text.insert(tk.END, f"Error fetching insights: {e}")

# Function to apply a selected filter
def apply_filter():
    global loaded_image, filtered_image
    if not loaded_image:
        messagebox.showwarning("Warning", "Please load an image first")
        return

    selected_filter = filter_listbox.get(tk.ACTIVE)
    if selected_filter == "Filter 1: Brightness Adjustment":
        filtered_image = loaded_image.point(lambda p: p * 1.2)
    elif selected_filter == "Filter 2: Edge Detection":
        filtered_image = loaded_image.filter(ImageFilter.FIND_EDGES)
    elif selected_filter == "Filter 3: Contrast Enhancement":
        filtered_image = loaded_image.filter(ImageFilter.CONTOUR)
    elif selected_filter == "Filter 4: Noise Reduction":
        filtered_image = loaded_image.filter(ImageFilter.SMOOTH)
    else:
        messagebox.showwarning("Warning", "Please select a filter")
        return

    tk_image = ImageTk.PhotoImage(filtered_image.resize((300, 300)))
    image_label.config(image=tk_image)
    image_label.image = tk_image

# Function to save the filtered image
def save_filtered_image():
    if not filtered_image:
        messagebox.showwarning("Warning", "No filtered image to save")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg"), ("All files", "*.*")]
    )
    if file_path:
        filtered_image.save(file_path)
        messagebox.showinfo("Success", f"Filtered image saved to {file_path}")

# Function to get filter recommendation and code from GPT API
def get_filter_recommendation():
    try:
        user_input = user_input_entry.get()
        if not user_input:
            messagebox.showwarning("Warning", "Please enter a description of what you want to do.")
            return

        messages = [
            {"role": "system", "content": "You are an assistant that suggests image filters and provides Python code based on user requests."},
            {"role": "user", "content": f"Suggest an image filter and provide Python code for the following task: {user_input}"}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages
        )
        recommendation = response["choices"][0]["message"]["content"].strip()
        recommendation_text.delete("1.0", tk.END)
        recommendation_text.insert("1.0", recommendation)
    except Exception as e:
        recommendation_text.delete("1.0", tk.END)
        recommendation_text.insert("1.0", f"Error fetching recommendation: {e}")

# Main application window
root = tk.Tk()
root.title("Image Processing and Insights GUI")
root.geometry("700x900")

# Add a scrollable canvas
canvas = tk.Canvas(root)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Frame to display the image
image_frame = tk.Frame(scrollable_frame)
image_frame.pack(pady=20, anchor="center")

# Button to load an image
load_button = tk.Button(scrollable_frame, text="Load Image", command=load_image)
load_button.pack(pady=5, anchor="center")

# Label to display image statistics
stats_label = tk.Label(scrollable_frame, text="", justify=tk.LEFT, fg="green")
stats_label.pack(pady=10, anchor="center")

# Frame for histogram
hist_frame = tk.Frame(scrollable_frame)
hist_frame.pack(pady=20, anchor="center")

# Text widget to display GPT insights
insights_text = tk.Text(scrollable_frame, height=10, wrap=tk.WORD, fg="blue")
insights_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Frame for the filter list
filter_frame = tk.Frame(scrollable_frame)
filter_frame.pack(pady=10, anchor="center")

filter_label = tk.Label(filter_frame, text="Available Filters:")
filter_label.pack()

filter_listbox = tk.Listbox(filter_frame, height=6)
filters = ["Filter 1: Brightness Adjustment", "Filter 2: Edge Detection", 
           "Filter 3: Contrast Enhancement", "Filter 4: Noise Reduction"]
for filter_item in filters:
    filter_listbox.insert(tk.END, filter_item)
filter_listbox.pack()

apply_filter_button = tk.Button(filter_frame, text="Apply Filter", command=apply_filter)
apply_filter_button.pack(pady=5)

# Button to save the filtered image
save_button = tk.Button(scrollable_frame, text="Save Filtered Image", command=save_filtered_image)
save_button.pack(pady=10, anchor="center")

# User input for custom task
task_frame = tk.Frame(scrollable_frame)
task_frame.pack(pady=10, anchor="center")

user_input_label = tk.Label(task_frame, text="Describe what you want to do:")
user_input_label.pack()

user_input_entry = tk.Entry(task_frame, width=50)
user_input_entry.pack(pady=5)

recommend_button = tk.Button(task_frame, text="Get Recommendation", command=get_filter_recommendation)
recommend_button.pack(pady=5)

# Text widget to display GPT recommendation
recommendation_text = tk.Text(scrollable_frame, height=15, wrap=tk.WORD, fg="purple")
recommendation_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

# Run the application
root.mainloop()
