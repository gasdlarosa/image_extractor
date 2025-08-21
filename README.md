# Image Extractor GUI

An intelligent desktop utility built with Python and YOLOv8 to automatically detect, de-skew, and extract perfectly cropped portrait photos from scanned documents and images.

![Image Extractor Screenshot](https://i.imgur.com/your-screenshot-url.png)
> **Note:** You should replace the link above with a real screenshot of your application. Consider creating a GIF of the workflow for the best showcase!

---

## The Problem

Manually cropping portrait photos from scanned documents (like IDs, passports, or résumés) is a tedious and time-consuming process. The photos are often skewed, and getting a perfectly proportioned, professional-looking headshot requires multiple steps in an image editor.

This tool automates the entire process with a single click.

## Key Features

- **Automatic Photo Detection:** Intelligently scans a document to find the physical boundaries of a photograph, ignoring text and other elements.
- **Multi-Format Support:** Load and process standard image files (`.jpg`, `.png`), PDF documents (`.pdf`), and Word documents (`.docx`).
- **De-skew & Straighten:** Automatically corrects the perspective of skewed or rotated photos, creating a perfectly rectangular image.
- **AI-Powered Smart Cropping:** Uses a YOLOv8 face detection model to calculate the ideal crop, ensuring proper headroom and shoulder space for a professional portrait.
- **Batch Processing from Documents:** Extracts and processes **all** valid portraits found within a multi-page or multi-image document.
- **Smart Filename Suggestions:** Automatically suggests a logical filename for saving (e.g., `original-file_img_extracted1.jpg`).
- **User-Friendly GUI:** A clean and intuitive interface built with Tkinter, featuring a detailed menu bar, keyboard shortcuts, and a real-time log panel.

## How It Works

The application uses a sophisticated multi-step pipeline:

1.  **Image Gathering:** It first identifies the input file type. For PDFs and DOCX files, it extracts all embedded images. If a PDF has no embedded images, it renders each page into an image.
2.  **Smart Scan:** For each image, it uses computer vision (OpenCV) to find candidate shapes that look like a physical photo.
3.  **Face Validation:** A YOLOv8 model validates each shape by checking for the presence of a human face.
4.  **Perspective Correction:** If a valid, skewed photo is found, a perspective transform is applied to straighten it perfectly.
5.  **Final Portrait Crop:** The YOLOv8 model is run again on the clean image to get precise face coordinates. The application then geometrically calculates a square frame with ideal headroom and crops the final portrait.
6.  **Collection & Saving:** All successfully extracted portraits are collected and presented to the user to be saved.

## Tech Stack

- **Language:** Python 3.10+
- **GUI Framework:** Tkinter (via Python's standard library)
- **AI / Machine Learning:** `ultralytics` (for YOLOv8 object detection)
- **Image Processing:** `Pillow` (PIL), `OpenCV`
- **Document Handling:** `PyMuPDF` (for PDFs), `python-docx` (for Word), `pdf2image`

## Installation & Usage

Follow these steps to get the application running on your local machine.

#### 1. Prerequisites
- Python 3.10 or newer installed.
- Git for cloning the repository.
- Poppler (for the `pdf2image` fallback on Windows). Follow the instructions [here](https://github.com/oschwartz10612/poppler-windows/releases/) to install and add it to your system's PATH.

#### 2. Clone the Repository
```bash
git clone https://github.com/your-username/image-extractor.git
cd image-extractor