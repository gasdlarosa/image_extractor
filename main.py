import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import webbrowser
import subprocess
from utils.logging_config import setup_logging, log_message
from processing.image_processor import ImageProcessor
from utils.document_handler import extract_images_from_document
from PIL import Image, ImageTk, ImageDraw

class ImageExtractorApp:
    def __init__(self, root):
        # This __init__ block is unchanged. Omitted for brevity.
        # Please keep your existing code here.
        self.root = root
        self.root.title("Image Extractor")
        self.root.geometry("800x650")
        self.root.resizable(False, False)
        
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('.', background='#f0f0f0', foreground='black')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TButton', background='#e1e1e1', foreground='black', borderwidth=1, padding=6)
        style.map('TButton', background=[('active', '#c0c0c0'), ('disabled', '#f0f0f0')])
        style.configure('TLabel', background='#f0f0f0', foreground='black')
        style.configure('TLabelFrame', background='#f0f0f0', foreground='black')
        style.configure('TLabelFrame.Label', background='#f0f0f0', foreground='black')

        self.always_on_top_var = tk.BooleanVar()
        self.show_logs_var = tk.BooleanVar(value=True)

        self.load_menu_icons()
        self.create_menu_bar()
        self.center_window()

        main_frame = ttk.Frame(root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        action_panel = ttk.Frame(main_frame)
        action_panel.pack(fill=tk.X, pady=5)
        self.load_button = ttk.Button(action_panel, text="Load Document or Image", command=self.load_file)
        self.load_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)
        self.reset_button = ttk.Button(action_panel, text="Reset Session", command=self.reset_session)
        self.reset_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, ipady=4)

        self.log_frame = ttk.LabelFrame(main_frame, text="Logs")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_button_panel = ttk.Frame(self.log_frame)
        self.log_button_panel.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(5, 0))
        self.clear_logs_button = ttk.Button(self.log_button_panel, text="Clear Logs", command=self.clear_logs)
        self.clear_logs_button.pack(side=tk.RIGHT, padx=5)
        self.copy_logs_button = ttk.Button(self.log_button_panel, text="Copy Logs", command=self.copy_logs)
        self.copy_logs_button.pack(side=tk.RIGHT, padx=0)
        self.log_text = tk.Text(self.log_frame, wrap=tk.WORD, state=tk.DISABLED, 
                                bg="white", fg="black", relief=tk.SOLID, borderwidth=1)
        self.log_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.status_bar = ttk.Label(main_frame, text="Ready", anchor=tk.W)
        self.status_bar.pack(fill=tk.X, pady=5)

        self.image_processor = None
        self.source_filepath = None
        self.extracted_portraits = []

        setup_logging(self.log_text)
        self.initialize_processor()

    # ... (All other methods like load_menu_icons, create_menu_bar, etc. are unchanged) ...
    # ... They are included at the end for the full file. ...

    def show_workflow(self):
        ### DEV COMMENT: This is the updated "How It Works" method.
        dialog = tk.Toplevel(self.root)
        dialog.title("How It Works")

        dialog_width = 900
        dialog_height = 600 # Increased height for more text
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (dialog_width // 2)
        y = (screen_height // 2) - (dialog_height // 2)
        
        dialog.geometry(f'{dialog_width}x{dialog_height}+{x}+{y}')
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        workflow_text = """The application uses a sophisticated, multi-step process to find and create well-proportioned portraits from various file types.

--- STEP 1: LOADING & IMAGE GATHERING ---

The process begins when you load a file.

1. File Type Detection: The application first identifies whether you've loaded a standard image file (.jpg, .png), a PDF document, or a Word document (.docx).

2. Image Extraction (for Documents): If a PDF or DOCX file is loaded, the application intelligently extracts all images embedded within the document. If no embedded images can be found in a PDF, it will render each page as a high-resolution image.

3. Processing Queue: All gathered images (either the single loaded image or all images from a document) are placed into a queue to be analyzed one by one.

--- STEP 2: THE SMART SCAN (FINDING THE PHYSICAL PHOTO) ---

For each image in the queue, the application first tries to locate the boundary of a physical photograph on the page. This is its most powerful feature.

1. Image Analysis: Using computer vision techniques (grayscale conversion, blurring, and thresholding), the document is analyzed to identify all distinct shapes.

2. Contour Filtering: Shapes are filtered based on their size and aspect ratio to find candidates that resemble a physical photograph.

3. Face Validation: For each candidate shape, the AI model (YOLOv8) checks if a human face is present inside it. This ensures we don't accidentally crop a table or a text block.

4. De-skew and Straighten: If a face is found, the application identifies the four corners of the photo, even if it's skewed. It then applies a perspective transform to create a perfectly rectangular, straightened image of just the photo. This clean image is passed to the next step.

--- STEP 3: CREATING THE FINAL PORTRAIT ---

This step takes a clean source image—either the straightened photo from Step 2 or the entire original image if Step 2 failed—and creates the final portrait.

1. Precise Face Detection: The AI model is run again on the clean source to get the exact coordinates of the face.

2. Geometric Calculation: Using the face's dimensions as a reference, the application calculates the dimensions of a new SQUARE frame. This frame is carefully calibrated to include ideal headroom above the head and adequate space for the shoulders below.

3. Final Crop: The source image is cropped to this new square frame, resulting in a well-proportioned final portrait.

--- STEP 4: COLLECTION & SAVING ---

All portraits successfully created from the source images are collected. If one or more portraits are found, you will be prompted to save them. The application will even suggest a default filename based on the original file you loaded.
"""
        
        text_frame = ttk.Frame(dialog, padding=15)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(
            text_frame, 
            wrap=tk.WORD, 
            bg="#f0f0f0", 
            fg="black", 
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            padx=10,
            pady=10
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, workflow_text)
        
        text_widget.tag_configure("heading", font=("Segoe UI", 12, "bold"), spacing1=5, spacing3=5)
        text_widget.tag_configure("bold", font=("Segoe UI", 10, "bold"))

        # ### DEV COMMENT: Updated tag indices for the new text.
        # Main Headings
        text_widget.tag_add("heading", "3.0", "3.42")  # STEP 1
        text_widget.tag_add("heading", "15.0", "15.58") # STEP 2
        text_widget.tag_add("heading", "29.0", "29.43") # STEP 3
        text_widget.tag_add("heading", "39.0", "39.36") # STEP 4

        # Keywords
        text_widget.tag_add("bold", "7.3", "7.26")      # 1. File Type Detection:
        text_widget.tag_add("bold", "9.3", "9.38")      # 2. Image Extraction (for Documents):
        text_widget.tag_add("bold", "9.68", "9.85")     # extracts all images
        text_widget.tag_add("bold", "10.60", "10.88")   # render each page as a high-resolution image
        text_widget.tag_add("bold", "12.3", "12.23")    # 3. Processing Queue:
        text_widget.tag_add("bold", "17.43", "17.61")   # physical photograph
        text_widget.tag_add("bold", "17.75", "17.96")   # most powerful feature
        text_widget.tag_add("bold", "19.3", "19.21")    # 1. Image Analysis:
        text_widget.tag_add("bold", "19.29", "19.56")   # computer vision techniques
        text_widget.tag_add("bold", "21.3", "21.23")    # 2. Contour Filtering:
        text_widget.tag_add("bold", "23.3", "23.21")    # 3. Face Validation:
        text_widget.tag_add("bold", "23.51", "23.68")   # AI model (YOLOv8)
        text_widget.tag_add("bold", "23.79", "23.89")   # human face
        text_widget.tag_add("bold", "25.3", "25.28")    # 4. De-skew and Straighten:
        text_widget.tag_add("bold", "25.59", "25.71")   # four corners
        text_widget.tag_add("bold", "25.104", "26.23")  # perspective transform
        text_widget.tag_add("bold", "26.33", "26.74")   # perfectly rectangular, straightened image
        text_widget.tag_add("bold", "31.43", "31.57")   # straightened photo
        text_widget.tag_add("bold", "31.70", "31.90")   # entire original image
        text_widget.tag_add("bold", "33.3", "33.27")    # 1. Precise Face Detection:
        text_widget.tag_add("bold", "35.3", "35.27")    # 2. Geometric Calculation:
        text_widget.tag_add("bold", "35.97", "36.9")    # SQUARE frame
        text_widget.tag_add("bold", "36.45", "36.59")   # ideal headroom
        text_widget.tag_add("bold", "36.69", "37.14")   # adequate space for the shoulders
        text_widget.tag_add("bold", "38.3", "38.15")    # 3. Final Crop:
        text_widget.tag_add("bold", "38.53", "38.88")   # well-proportioned final portrait
        text_widget.tag_add("bold", "41.52", "41.62")   # collected
        text_widget.tag_add("bold", "42.48", "42.68")   # default filename
        
        text_widget.config(state=tk.DISABLED)

        button_frame = ttk.Frame(dialog, padding=(0, 0, 0, 10))
        button_frame.pack(fill=tk.X)
        
        ok_button = ttk.Button(button_frame, text="OK", command=dialog.destroy, width=12)
        ok_button.pack()
        ok_button.focus_set()

        self.root.wait_window(dialog)


    # --- All other methods remain unchanged. They are included below for completeness. ---
    def load_menu_icons(self):
        try:
            folder_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            draw = ImageDraw.Draw(folder_img)
            draw.rectangle([(1, 3), (15, 13)], fill='#FFC107', outline='#FFA000')
            draw.rectangle([(0, 5), (6, 13)], fill='#FFC107', outline='#FFA000')
            draw.rectangle([(0, 2), (5, 4)], fill='#FFECB3', outline='#FFA000')
            self.folder_icon = ImageTk.PhotoImage(folder_img)

            web_img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            draw = ImageDraw.Draw(web_img)
            draw.ellipse([(1, 1), (14, 14)], fill='#4FC3F7', outline='#039BE5')
            draw.line([(8, 1), (8, 14)], fill='#039BE5')
            draw.line([(1, 8), (14, 8)], fill='#039BE5')
            draw.arc([(4, 1), (11, 14)], 180, 360, fill='#039BE5')
            draw.arc([(4, 1), (11, 14)], 0, 180, fill='#039BE5')
            self.web_icon = ImageTk.PhotoImage(web_img)
            
        except Exception as e:
            print(f"Could not create menu icons: {e}")
            self.folder_icon = None
            self.web_icon = None

    def create_menu_bar(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        self.file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open File...", accelerator="Ctrl+O", command=self.load_file)
        self.file_menu.add_command(label="Save Extracted Photos...", accelerator="Ctrl+S", command=self.save_images, state="disabled")
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Reset Session", accelerator="Ctrl+R", command=self.reset_session)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy Logs", accelerator="Ctrl+C", command=self.copy_logs)
        edit_menu.add_command(label="Clear Logs", accelerator="Shift+Del", command=self.clear_logs)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_checkbutton(label="Show Log Panel", onvalue=True, offvalue=False, variable=self.show_logs_var, command=self.toggle_log_panel)
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.always_on_top_var, command=self.toggle_always_on_top)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        if self.folder_icon:
            tools_menu.add_command(label="Open Model Folder...", image=self.folder_icon, compound='left', command=self.open_model_folder)
        else:
            tools_menu.add_command(label="Open Model Folder...", command=self.open_model_folder)
        tools_menu.add_separator()
        tools_menu.add_command(label="Force Reload AI Model", command=self.force_reload_model)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How It Works", command=self.show_workflow)
        help_menu.add_command(label="Developer Info", command=self.show_developer_info)
        help_menu.add_separator()
        if self.web_icon:
            help_menu.add_command(label="Check for Updates...", image=self.web_icon, compound='left', command=self.check_for_updates)
        else:
            help_menu.add_command(label="Check for Updates...", command=self.check_for_updates)
        help_menu.add_separator()
        help_menu.add_command(label="About Image Extractor", command=self.show_about)

        self.root.bind_all("<Control-o>", lambda event: self.load_file())
        self.root.bind_all("<Control-s>", lambda event: self.save_images())
        self.root.bind_all("<Control-r>", lambda event: self.reset_session())
        self.root.bind_all("<Control-c>", lambda event: self.copy_logs())
        self.root.bind_all("<Shift-Delete>", lambda event: self.clear_logs())

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        margin = int(self.root.winfo_fpixels('1i'))
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        y = max(margin, min(y, screen_height - height - margin))
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def initialize_processor(self):
        self.status_bar.config(text="Initializing AI model...")
        log_message("Initializing YOLOv8 face detection model.")
        threading.Thread(target=self._load_processor, daemon=True).start()

    def _load_processor(self):
        try:
            self.image_processor = ImageProcessor()
            self.root.after(0, self.on_processor_loaded)
        except Exception as e:
            self.root.after(0, lambda err=e: self.on_processor_load_error(err))

    def on_processor_loaded(self):
        self.status_bar.config(text="Model loaded successfully. Ready.")
        log_message("Model initialized and ready.")

    def on_processor_load_error(self, error):
        self.status_bar.config(text="Error loading model!")
        log_message(f"Error: {error}")
        messagebox.showerror("Model Load Error", f"Could not initialize the AI model: {error}")

    def load_file(self):
        if not self.image_processor:
            messagebox.showwarning("Model Not Ready", "The AI model is still initializing. Please wait a moment.")
            return

        file_types_config = [
            ("All Supported Files", "*.pdf *.docx *.jpg *.jpeg *.png *.bmp"),
            ("PDF Documents", "*.pdf"),
            ("Word Documents", "*.docx"),
            ("Image Files", "*.jpg *.jpeg *.png *.bmp"),
            ("All Files", "*.*")
        ]
        file_path = filedialog.askopenfilename(title="Select a Document or Image File", filetypes=file_types_config)
        
        if not file_path:
            return

        self.reset_session()
        self.source_filepath = file_path
        self.status_bar.config(text=f"Loading file: {os.path.basename(file_path)}...")
        log_message(f"Loaded file: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
            threading.Thread(target=self.process_image, args=(file_path,), daemon=True).start()
        elif file_extension in ['.pdf', '.docx']:
            log_message(f"Document file detected. Extracting images...")
            threading.Thread(target=self.process_document, args=(file_path,), daemon=True).start()
        else:
            unsupported_msg = f"Unsupported file type: '{file_extension}'. Please select a supported document or image file."
            log_message(f"Error: {unsupported_msg}")
            self.status_bar.config(text="Unsupported file type.")
            messagebox.showerror("Unsupported File", unsupported_msg)
    
    def process_document(self, file_path):
        try:
            images_from_doc = extract_images_from_document(file_path)
            if not images_from_doc:
                self.root.after(0, self.on_processing_complete)
                return

            log_message(f"Found {len(images_from_doc)} image(s) in the document. Searching for faces...")
            
            valid_portraits = []
            for i, pil_image in enumerate(images_from_doc):
                log_message(f"Analyzing image #{i+1} from document...")
                extracted_portrait = self.image_processor.extract_photo(pil_image)
                if extracted_portrait:
                    valid_portraits.append(extracted_portrait)
            
            self.extracted_portraits = valid_portraits
            self.root.after(0, self.on_processing_complete)

        except Exception as e:
            self.root.after(0, lambda err=e: self.on_processing_error(err))

    def process_image(self, file_path_or_pil):
        try:
            extracted_portrait = self.image_processor.extract_photo(file_path_or_pil)
            if extracted_portrait:
                self.extracted_portraits = [extracted_portrait]
            else:
                self.extracted_portraits = []
            self.root.after(0, self.on_processing_complete)
        except Exception as e:
            self.root.after(0, lambda err=e: self.on_processing_error(err))
            
    def on_processing_complete(self):
        num_found = len(self.extracted_portraits)
        
        if num_found == 0:
            self.status_bar.config(text="No usable photo found in the source file.")
            log_message("Processing complete: No photo with a detectable face was found.")
            messagebox.showinfo("Processing Complete", "Could not find a usable photo in the selected file.")
        else:
            self.file_menu.entryconfig("Save Extracted Photos...", state="normal")
            
            plural_s = "s" if num_found > 1 else ""
            self.status_bar.config(text=f"Successfully extracted {num_found} photo{plural_s}.")
            log_message(f"Successfully extracted {num_found} photo{plural_s}.")

            if num_found == 1:
                prompt = "A photo was successfully extracted.\n\nDo you want to save it?"
            else:
                prompt = f"{num_found} photos were successfully extracted.\n\nYou will be prompted to save each one individually.\n\nDo you want to proceed with saving?"

            if messagebox.askyesno("Extraction Successful", prompt):
                self.save_images()
            else:
                self.status_bar.config(text="Extraction complete. User chose not to save.")
                log_message("User chose not to save the extracted photo(s).")

    def on_processing_error(self, error):
        self.status_bar.config(text="An error occurred during processing.")
        log_message(f"Error: {error}")
        messagebox.showerror("Processing Error", f"An error occurred: {error}")

    def save_images(self):
        if not self.extracted_portraits:
            log_message("Save command issued, but no images are extracted.")
            return

        if not self.source_filepath:
            return

        base_path = os.path.splitext(self.source_filepath)[0]
        base_name = os.path.basename(base_path)
        
        num_to_save = len(self.extracted_portraits)

        for i, portrait_to_save in enumerate(self.extracted_portraits):
            if num_to_save > 1:
                suffix = f"_img_extracted{i + 1}"
            else:
                suffix = "_img_extracted"
            
            default_filename = f"{base_name}{suffix}.jpg"
            
            save_path = filedialog.asksaveasfilename(
                parent=self.root,
                title=f"Save Extracted Photo ({i + 1} of {num_to_save})",
                initialfile=default_filename,
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg")]
            )

            if save_path:
                try:
                    portrait_to_save.save(save_path, "JPEG", quality=95)
                    self.status_bar.config(text=f"Photo saved to {os.path.basename(save_path)}")
                    log_message(f"Extracted photo saved to: {save_path}")
                except Exception as e:
                    self.status_bar.config(text="Error saving image.")
                    log_message(f"Error: {e}")
                    messagebox.showerror("Save Error", f"Could not save the image: {e}")
            else:
                log_message("User cancelled save operation.")
                if num_to_save > 1:
                    if messagebox.askyesno("Cancel Saving", "Do you want to cancel saving the rest of the photos?"):
                        log_message("User aborted saving remaining photos.")
                        break
                
    def copy_logs(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.log_text.get("1.0", tk.END))
        self.status_bar.config(text="Logs copied to clipboard.")

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def reset_session(self):
        self.clear_logs()
        self.status_bar.config(text="Ready")
        self.source_filepath = None
        self.extracted_portraits = []
        if hasattr(self, 'file_menu'):
             self.file_menu.entryconfig("Save Extracted Photos...", state="disabled")
        log_message("Session has been reset.")
        
    def show_about(self):
        messagebox.showinfo(
            "About Image Extractor",
            "Image Extractor v1.4\n\n"
            "A GUI utility to automatically find and extract portraits from documents and images.\n"
            "Utilizes YOLOv8 for advanced object detection."
        )

    def show_developer_info(self):
        messagebox.showinfo(
            "Developer Information",
            "Developed by: gasdlarosa 😎\n"
            "Email: gasdlarosa@gmail.com"
        )

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def toggle_log_panel(self):
        if self.show_logs_var.get():
            self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        else:
            self.log_frame.pack_forget()

    def force_reload_model(self):
        if messagebox.askyesno("Reload Model", "This will reload the AI model, which may take a moment. Are you sure?"):
            self.load_button.config(state="disabled")
            self.reset_button.config(state="disabled")
            self.image_processor = None
            self.initialize_processor()
            self.load_button.config(state="normal")
            self.reset_button.config(state="normal")
    
    def open_model_folder(self):
        try:
            model_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "data", "models"))
            if not os.path.isdir(model_dir):
                os.makedirs(model_dir)
            
            if sys.platform == "win32":
                os.startfile(model_dir)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", model_dir])
            else:
                subprocess.Popen(["xdg-open", model_dir])
            log_message(f"Opened model folder: {model_dir}")
        except Exception as e:
            log_message(f"Error opening model folder: {e}")
            messagebox.showerror("Error", f"Could not open the model folder: {e}")

    def check_for_updates(self):
        project_url = "https://github.com/gasdlarosa" 
        log_message(f"Opening browser to {project_url}...")
        try:
            webbrowser.open(project_url, new=2)
        except Exception as e:
            log_message(f"Error opening browser: {e}")
            messagebox.showerror("Error", f"Could not open the web browser: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageExtractorApp(root)
    root.mainloop()