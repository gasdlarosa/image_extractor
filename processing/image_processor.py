import cv2
import numpy as np
from ultralytics import YOLO
from PIL import Image
import os

class ImageProcessor:
    def __init__(self, model_filename="model.pt"):
        # Construct the model path relative to the script's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "..", "data", "models", model_filename)
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at '{model_path}'. "
                f"Please ensure 'model.pt' is in the 'data/models' directory relative to the script."
            )
        
        self.model = YOLO(model_path)
        self.model.conf = 0.4 # Confidence threshold

    def _find_photo_shape_on_document(self, image_cv):
        """
        Finds the physical photo on the document and returns a de-skewed PIL image.
        """
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0) 
        
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 11, 2)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=5)
        
        contours, _ = cv2.findContours(closed.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_h, img_w = image_cv.shape[:2]
        total_image_area = img_w * img_h
        
        min_photo_area_ratio = 0.01
        max_photo_area_ratio = 0.30
        
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(contour)
            
            if not (min_photo_area_ratio * total_image_area < area < max_photo_area_ratio * total_image_area):
                continue

            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.03 * perimeter, True)
            
            if len(approx) == 4:
                (x, y, w, h) = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)
                
                if 0.75 <= aspect_ratio <= 1.35:
                    candidate_region_cv = image_cv[y:y+h, x:x+w]
                    
                    try:
                        candidate_pil = Image.fromarray(cv2.cvtColor(candidate_region_cv, cv2.COLOR_BGR2RGB))
                    except cv2.error as cv_err:
                        print(f"CV Error converting candidate region to PIL: {cv_err}")
                        continue

                    results = self.model(candidate_pil, verbose=False)
                    
                    if results and results[0].boxes and len(results[0].boxes) > 0:
                        pts = approx.reshape(4, 2).astype("float32")
                        
                        rect = np.zeros((4, 2), dtype="float32")
                        s = pts.sum(axis=1)
                        rect[0] = pts[np.argmin(s)]
                        rect[2] = pts[np.argmax(s)]
                        diff = np.diff(pts, axis=1)
                        rect[1] = pts[np.argmin(diff)]
                        rect[3] = pts[np.argmax(diff)]
                        
                        widthA = np.sqrt(((rect[2][0] - rect[3][0]) ** 2) + ((rect[2][1] - rect[3][1]) ** 2))
                        widthB = np.sqrt(((rect[1][0] - rect[0][0]) ** 2) + ((rect[1][1] - rect[0][1]) ** 2))
                        maxWidth = max(int(widthA), int(widthB))
                        
                        heightA = np.sqrt(((rect[1][0] - rect[2][0]) ** 2) + ((rect[1][1] - rect[2][1]) ** 2))
                        heightB = np.sqrt(((rect[0][0] - rect[3][0]) ** 2) + ((rect[0][1] - rect[3][1]) ** 2))
                        maxHeight = max(int(heightA), int(heightB))
                        
                        dst = np.array([
                            [0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]
                        ], dtype="float32")
                        
                        M = cv2.getPerspectiveTransform(rect, dst)
                        warped_cv = cv2.warpPerspective(image_cv, M, (maxWidth, maxHeight))
                        
                        return Image.fromarray(cv2.cvtColor(warped_cv, cv2.COLOR_BGR2RGB))
        
        return None

    def _perform_portrait_crop(self, source_image_pil):
        """
        Takes a clean image and creates the final, proportionate SQUARE portrait.
        """
        if source_image_pil.mode != 'RGB':
            source_image_pil = source_image_pil.convert('RGB')

        results = self.model(source_image_pil, verbose=False)
        
        if not results or not results[0].boxes or len(results[0].boxes) == 0:
            print("INFO: No faces detected in the source image for final cropping.")
            return None

        face_box = results[0].boxes[0].xyxy[0].tolist()
        face_x1, face_y1, face_x2, face_y2 = face_box
        face_w = face_x2 - face_x1
        face_h = face_y2 - face_y1
        face_center_x = (face_x1 + face_x2) / 2

        # --- DEFINITIVE SQUARE FRAME GEOMETRIC CONSTRUCTION ---
        headroom_ratio = 0.35
        shoulder_room_ratio = 0.7
        headroom = face_h * headroom_ratio
        shoulder_room = face_h * shoulder_room_ratio
        required_height = face_h + headroom + shoulder_room

        horizontal_padding_ratio = 0.4
        horizontal_padding = face_w * horizontal_padding_ratio
        required_width = face_w + (2 * horizontal_padding)
        
        side_length = max(required_height, required_width)

        crop_x1 = face_center_x - (side_length / 2)
        crop_x2 = face_center_x + (side_length / 2)
        
        crop_y1 = face_y1 - headroom
        crop_y2 = crop_y1 + side_length
        
        # --- END OF LOGIC ---

        img_w, img_h = source_image_pil.size
        final_crop_box = (
            max(0, crop_x1),
            max(0, crop_y1),
            min(img_w, crop_x2),
            min(img_h, crop_y2)
        )
        
        try:
            cropped_image = source_image_pil.crop(final_crop_box)
        except Exception as crop_err:
            print(f"Error during PIL crop operation: {crop_err}")
            return None
        
        return cropped_image

    def extract_photo(self, image_path_or_pil):
        """
        Main function. Takes a file path or a PIL Image object and returns the final, 
        cropped PIL image.
        """
        image_cv = None
        source_image_pil = None

        # --- Load and Prepare Image ---
        if isinstance(image_path_or_pil, str): # If input is a file path
            if not os.path.exists(image_path_or_pil):
                raise FileNotFoundError(f"Image file not found at: {image_path_or_pil}")
            
            image_cv = cv2.imread(image_path_or_pil)
            if image_cv is None:
                raise ValueError(f"Could not read the image file with OpenCV at: {image_path_or_pil}")
            
            try:
                source_image_pil = Image.open(image_path_or_pil)
            except Exception as pil_err:
                raise IOError(f"Could not open image file with PIL at {image_path_or_pil}: {pil_err}")

        elif isinstance(image_path_or_pil, Image.Image): # If input is already a PIL Image object
            source_image_pil = image_path_or_pil
            image_cv_array = np.array(source_image_pil)
            image_cv = cv2.cvtColor(image_cv_array, cv2.COLOR_RGB2BGR) # Convert PIL RGB to OpenCV BGR
        else:
            raise TypeError("Input must be a file path (str) or a PIL Image object.")

        if image_cv is None or source_image_pil is None:
            raise ValueError("Failed to load image data.")

        # --- Stage 1: Find Distinct Photo Shape ---
        print("INFO: Attempting to find distinct photo shape on document...")
        straightened_photo_pil = self._find_photo_shape_on_document(image_cv)

        final_portrait = None
        # --- Stage 2: Perform Cropping ---
        if straightened_photo_pil:
            print("INFO: Distinct photo shape detected. Proceeding with crop on straightened photo.")
            final_portrait = self._perform_portrait_crop(straightened_photo_pil)
        else:
            print("INFO: No distinct photo shape found. Falling back to processing the full image for face detection.")
            final_portrait = self._perform_portrait_crop(source_image_pil)
        
        return final_portrait
# --- END OF FILE image_processor.py ---