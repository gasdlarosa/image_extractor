import fitz  # PyMuPDF
from docx import Document
from PIL import Image
import io
from pdf2image import convert_from_path
import os

def extract_images_from_document(file_path):
    """
    Extracts PIL Image objects from a given document file (PDF or DOCX).

    Args:
        file_path (str): The path to the document.

    Returns:
        list: A list of PIL Image objects found in the document.
              Returns an empty list if no images are found or the file type is unsupported.
    """
    images = []
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == '.pdf':
        try:
            # First, try to extract embedded images directly (more efficient)
            doc = fitz.open(file_path)
            if doc.page_count > 0:
                for page in doc:
                    image_list = page.get_images(full=True)
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        images.append(pil_image)
            doc.close()

            # If no embedded images were found, render pages as images (robust fallback)
            if not images:
                print("No embedded images found in PDF, falling back to page rendering...")
                # You may need to provide the poppler path for Windows
                # images = convert_from_path(file_path, poppler_path=r"C:\path\to\poppler\bin")
                images = convert_from_path(file_path)

        except Exception as e:
            print(f"Error processing PDF file '{os.path.basename(file_path)}': {e}")
            return []

    elif file_extension == '.docx':
        try:
            doc = Document(file_path)
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image_bytes = rel.target_part.blob
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    images.append(pil_image)
        except Exception as e:
            print(f"Error processing DOCX file '{os.path.basename(file_path)}': {e}")
            return []

    return images