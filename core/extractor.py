import os
import cv2
import numpy as np
from PIL import Image
from oct_converter.readers import E2E

class E2EProcessor:
    @staticmethod
    def load_file(filepath):
        """
        Loads an E2E file and extracts volumes.
        Returns a tuple: (success, result, error_message)
        If success is True, result is the file object.
        """
        try:
            # The library handles reading the binary file
            e2e_file = E2E(filepath)
            # Accessing volumes to make sure it's valid
            volumes = e2e_file.read_oct_volume()
            if not volumes:
                return False, None, "The E2E file does not contain recognizable OCT volumes."
            return True, e2e_file, ""
        except Exception as e:
            return False, None, f"Error reading the E2E file:\n{str(e)}"

    @staticmethod
    def apply_scale(img_data, pixel_spacing):
        """
        Resizes the image array to maintain correct physical aspect ratio based on pixel_spacing.
        Usually spacing is [width_spacing (x), height_spacing (z), distance_between_slices (y)].
        """
        if pixel_spacing is None or len(pixel_spacing) < 2:
            return img_data
        
        spacing_x = pixel_spacing[0]
        spacing_z = pixel_spacing[1]
        
        if spacing_x <= 0 or spacing_z <= 0:
            return img_data
            
        # We stretch the width based on the ratio of X spacing to Z spacing
        scale_width = spacing_x / spacing_z
        
        if abs(scale_width - 1.0) < 0.01:
            return img_data
            
        height, width = img_data.shape
        new_width = int(round(width * scale_width))
        
        return cv2.resize(img_data, (new_width, height), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def draw_scale_bar(img_data, pixel_spacing):
        """
        Draws a scale bar on the bottom left of the image.
        Assumes img_data has already been scaled to uniform pixel spacing via apply_scale,
        meaning both X and Z pixels represent pixel_spacing[1] (spacing_z) mm.
        """
        if pixel_spacing is None or len(pixel_spacing) < 2:
            return img_data
            
        spacing_z = pixel_spacing[1]
        if spacing_z <= 0:
            return img_data
            
        h, w = img_data.shape[:2]
        img_physical_width_mm = w * spacing_z
        
        # Decide bar length
        if img_physical_width_mm > 5.0:
            bar_length_mm = 1.0
            text = "1 mm"
        elif img_physical_width_mm > 2.0:
            bar_length_mm = 0.5
            text = "500 um"
        elif img_physical_width_mm > 0.5:
            bar_length_mm = 0.2
            text = "200 um"
        else:
            bar_length_mm = 0.1
            text = "100 um"
            
        bar_pixels = int(round(bar_length_mm / spacing_z))
        if bar_pixels <= 0:
            return img_data
            
        # Convert to BGR if grayscale
        if len(img_data.shape) == 2:
            img_color = cv2.cvtColor(img_data, cv2.COLOR_GRAY2RGB)
        else:
            img_color = img_data.copy()
            
        margin_x = max(10, int(w * 0.02))
        margin_y = max(10, int(h * 0.05))
        
        start_point = (margin_x, h - margin_y)
        end_point = (margin_x + bar_pixels, h - margin_y)
        
        color = (255, 255, 255)
        thickness = max(2, int(h * 0.005))
        
        # Horizontal line
        cv2.line(img_color, start_point, end_point, color, thickness)
        # Vertical ticks
        cv2.line(img_color, (start_point[0], start_point[1] - thickness*2), (start_point[0], start_point[1] + thickness*2), color, thickness)
        cv2.line(img_color, (end_point[0], end_point[1] - thickness*2), (end_point[0], end_point[1] + thickness*2), color, thickness)
        
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.4, h * 0.001)
        text_thickness = max(1, int(h * 0.002))
        
        text_size, _ = cv2.getTextSize(text, font, font_scale, text_thickness)
        text_x = start_point[0] + max(0, (bar_pixels - text_size[0]) // 2)
        text_y = start_point[1] - thickness * 3 - 2
        
        # Text shadow and text
        cv2.putText(img_color, text, (text_x+1, text_y+1), font, font_scale, (0,0,0), text_thickness)
        cv2.putText(img_color, text, (text_x, text_y), font, font_scale, color, text_thickness)
        
        return img_color

    @staticmethod
    def get_preview_image(volume):
        """
        Generates a preview image from the volume.
        We return the middle slice of the volume as a PIL Image.
        """
        try:
            vol_data = volume.volume
            if vol_data is None or len(vol_data) == 0:
                return None
            
            # Get the middle slice
            mid_idx = len(vol_data) // 2
            mid_slice = vol_data[mid_idx]
            
            # Normalize to 0-255 for visualization
            if mid_slice.max() > 0:
                mid_slice = (mid_slice / mid_slice.max() * 255).astype(np.uint8)
            else:
                mid_slice = mid_slice.astype(np.uint8)
            # Apply aspect ratio scaling and scale bar
            if hasattr(volume, 'pixel_spacing'):
                mid_slice = E2EProcessor.apply_scale(mid_slice, volume.pixel_spacing)
                mid_slice = E2EProcessor.draw_scale_bar(mid_slice, volume.pixel_spacing)
            
            img = Image.fromarray(mid_slice)
            return img
        except Exception:
            return None

    @staticmethod
    def export_volume(volume, output_dir, file_prefix, formats):
        """
        Exports a single volume to the specified formats inside output_dir.
        Formats can include 'png', 'tiff', 'avi'.
        """
        os.makedirs(output_dir, exist_ok=True)
        vol_data = volume.volume

        if 'png' in formats:
            png_dir = os.path.join(output_dir, f"{file_prefix}_png")
            os.makedirs(png_dir, exist_ok=True)
            for i, slice_data in enumerate(vol_data):
                # Normalize slice if needed
                if slice_data.max() > 0 and slice_data.max() <= 1.0:
                     slice_data_norm = (slice_data * 255).astype(np.uint8)
                else:
                     # Some oct converters return 0-255 directly, let's keep it safe
                     slice_data_norm = slice_data.astype(np.uint8)
                
                if hasattr(volume, 'pixel_spacing'):
                     slice_data_norm = E2EProcessor.apply_scale(slice_data_norm, volume.pixel_spacing)
                     slice_data_norm = E2EProcessor.draw_scale_bar(slice_data_norm, volume.pixel_spacing)
                     
                img = Image.fromarray(slice_data_norm)
                img.save(os.path.join(png_dir, f"{file_prefix}_slice_{i:03d}.png"))
                
        if 'tiff' in formats:
            # Save as a multi-page TIFF
            tiff_path = os.path.join(output_dir, f"{file_prefix}.tiff")
            images = []
            for slice_data in vol_data:
                if slice_data.max() > 0 and slice_data.max() <= 1.0:
                     slice_data_norm = (slice_data * 255).astype(np.uint8)
                else:
                     slice_data_norm = slice_data.astype(np.uint8)
                     
                if hasattr(volume, 'pixel_spacing'):
                     slice_data_norm = E2EProcessor.apply_scale(slice_data_norm, volume.pixel_spacing)
                     slice_data_norm = E2EProcessor.draw_scale_bar(slice_data_norm, volume.pixel_spacing)
                     
                images.append(Image.fromarray(slice_data_norm))
            
            if images:
                images[0].save(
                    tiff_path, save_all=True, append_images=images[1:], compression="tiff_deflate"
                )

    @staticmethod
    def export_fundus(fundus_img, output_dir, file_prefix):
        """
        Exports a fundus (scout/sweep) image to PNG.
        """
        os.makedirs(output_dir, exist_ok=True)
        try:
            if hasattr(fundus_img, 'image') and fundus_img.image is not None:
                img_data = fundus_img.image
                # Check for normalization if needed
                if img_data.max() > 0 and img_data.max() <= 1.0:
                     img_data_norm = (img_data * 255).astype(np.uint8)
                else:
                     img_data_norm = img_data.astype(np.uint8)
                     
                if hasattr(fundus_img, 'pixel_spacing'):
                     img_data_norm = E2EProcessor.draw_scale_bar(img_data_norm, fundus_img.pixel_spacing)
                     
                # Convert to RGB if draw_scale_bar didn't already or if it returned color array
                if len(img_data_norm.shape) == 3 and img_data_norm.shape[2] == 3:
                     # OpenCV uses BGR, but PIL expects RGB, wait! draw_scale_bar doesn't explicitly use colors except white
                     # Actually cvtColor converts GRAY to RGB, so we are fine. But OpenCV line colors are BGR.
                     # White is (255,255,255), so RGB/BGR doesn't matter for the white bar and black shadow!
                     pass

                img = Image.fromarray(img_data_norm)
                img.save(os.path.join(output_dir, f"{file_prefix}.png"))
        except Exception as e:
            pass # Skip if fails to save fundus
            
    @staticmethod
    def process_batch(input_dir, output_dir, formats, progress_callback=None, log_callback=None):
        """
        Iterates over all .e2e files in input_dir, and exports their volumes.
        progress_callback: function(current, total)
        log_callback: function(str)
        """
        e2e_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.e2e')]
        total_files = len(e2e_files)
        
        if total_files == 0:
            if log_callback: log_callback("No .e2e files found in the source directory.")
            return

        if log_callback: log_callback(f"Starting processing of {total_files} files...")

        for i, filename in enumerate(e2e_files):
            filepath = os.path.join(input_dir, filename)
            file_base = os.path.splitext(filename)[0]
            
            if log_callback: log_callback(f"\nProcessing file ({i+1}/{total_files}): {filename}")
            
            success, e2e_file, error_msg = E2EProcessor.load_file(filepath)
            
            if not success:
                if log_callback: log_callback(f"  [ERROR] {error_msg}")
            else:
                try:
                    volumes = e2e_file.read_oct_volume()
                    if log_callback: log_callback(f"  Found {len(volumes)} volume(s). Exporting...")
                    
                    # Create a specific folder for this E2E file
                    file_output_dir = os.path.join(output_dir, file_base)
                    os.makedirs(file_output_dir, exist_ok=True)
                    
                    for v_idx, volume in enumerate(volumes):
                        # Some volumes might be None or invalid
                        if volume is None or volume.volume is None:
                            continue
                            
                        vol_prefix = f"vol_{v_idx}"
                        E2EProcessor.export_volume(volume, file_output_dir, vol_prefix, formats)
                    
                    # Extract and save fundus/sweep images
                    try:
                        fundus_images = e2e_file.read_fundus_image()
                        if fundus_images:
                            if log_callback: log_callback(f"  Found {len(fundus_images)} fundus image(s). Exporting...")
                            for f_idx, fundus in enumerate(fundus_images):
                                fundus_prefix = f"fundus_{f_idx}"
                                E2EProcessor.export_fundus(fundus, file_output_dir, fundus_prefix)
                    except Exception as e:
                        if log_callback: log_callback(f"  [WARNING] Could not extract fundus images: {str(e)}")
                        
                    if log_callback: log_callback(f"  Completed successfully: {filename}")
                except Exception as e:
                    if log_callback: log_callback(f"  [ERROR] An error occurred during export: {str(e)}")

            if progress_callback:
                progress_callback(i + 1, total_files)
                
        if log_callback: log_callback("\nBatch processing finished.")
