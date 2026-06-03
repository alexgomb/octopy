import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.extractor import E2EProcessor
from PIL import Image

class SingleModeUI(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.current_file_path = None
        self.current_e2e_file = None
        self.volumes = []

        self.setup_ui()

    def setup_ui(self):
        # Top Panel: File Selection
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.top_frame.grid_columnconfigure(1, weight=1)

        self.btn_select = ctk.CTkButton(self.top_frame, text="Select E2E File", command=self.select_file)
        self.btn_select.grid(row=0, column=0, padx=10, pady=10)

        self.lbl_filepath = ctk.CTkLabel(self.top_frame, text="No file selected", text_color="gray")
        self.lbl_filepath.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Metadata Panel
        self.meta_frame = ctk.CTkFrame(self)
        self.meta_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.lbl_metadata = ctk.CTkLabel(self.meta_frame, text="File Information:\nWaiting for selection...", justify="left")
        self.lbl_metadata.pack(padx=10, pady=10, anchor="w")

        # Center Panel: Image Preview
        self.preview_frame = ctk.CTkFrame(self)
        self.preview_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.preview_frame.grid_rowconfigure(0, weight=1)
        self.preview_frame.grid_columnconfigure(0, weight=1)

        self.lbl_preview = ctk.CTkLabel(self.preview_frame, text="Central Volume Preview (B-Scan)")
        self.lbl_preview.grid(row=0, column=0, padx=10, pady=10)

        # Bottom Panel: Export Options
        self.bottom_frame = ctk.CTkFrame(self)
        self.bottom_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.bottom_frame, text="Export Formats:").grid(row=0, column=0, padx=10, pady=10)

        self.chk_png_var = ctk.StringVar(value="png")
        self.chk_png = ctk.CTkCheckBox(self.bottom_frame, text="PNG", variable=self.chk_png_var, onvalue="png", offvalue="")
        self.chk_png.grid(row=0, column=1, padx=10, pady=10)

        self.chk_tiff_var = ctk.StringVar(value="")
        self.chk_tiff = ctk.CTkCheckBox(self.bottom_frame, text="TIFF", variable=self.chk_tiff_var, onvalue="tiff", offvalue="")
        self.chk_tiff.grid(row=0, column=2, padx=10, pady=10)

        self.btn_export = ctk.CTkButton(self.bottom_frame, text="Export Volume(s)", command=self.export_data, state="disabled")
        self.btn_export.grid(row=0, column=4, padx=20, pady=10, sticky="e")
        self.bottom_frame.grid_columnconfigure(4, weight=1)

    def select_file(self):
        filepath = filedialog.askopenfilename(
            title="Select E2E file",
            filetypes=[("E2E Files", "*.e2e"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        self.current_file_path = filepath
        self.lbl_filepath.configure(text=os.path.basename(filepath), text_color="white")
        self.btn_select.configure(state="disabled")
        self.lbl_metadata.configure(text="Loading file... Please wait.")
        
        # Load file in a separate thread
        threading.Thread(target=self._load_file_thread, args=(filepath,), daemon=True).start()

    def _load_file_thread(self, filepath):
        success, e2e_file, error_msg = E2EProcessor.load_file(filepath)
        
        # Update UI from main thread
        self.after(0, self._on_file_loaded, success, e2e_file, error_msg)

    def _on_file_loaded(self, success, e2e_file, error_msg):
        self.btn_select.configure(state="normal")
        
        if not success:
            messagebox.showerror("Error", error_msg)
            self.lbl_metadata.configure(text="Error loading file.")
            return

        self.current_e2e_file = e2e_file
        self.volumes = e2e_file.read_oct_volume()
        
        if not self.volumes:
            messagebox.showwarning("Warning", "No OCT volumes found in this file.")
            self.lbl_metadata.configure(text="No volumes found.")
            return

        # Metadatos básicos (patient_id, date, etc.) si están disponibles
        # oct-converter guarda estos datos en e2e_file, pero dependen del archivo.
        # Mostramos información genérica sobre los volúmenes encontrados.
        fundus_count = 0
        try:
             fundus_images = e2e_file.read_fundus_image()
             if fundus_images:
                  fundus_count = len(fundus_images)
        except:
             pass

        meta_text = f"File loaded successfully.\nOCT Volumes found: {len(self.volumes)}\nFundus (Sweep) images: {fundus_count}"
        self.lbl_metadata.configure(text=meta_text)
        
        self.btn_export.configure(state="normal")

        # Mostrar preview del primer volumen válido
        for vol in self.volumes:
            if vol is not None and vol.volume is not None:
                img = E2EProcessor.get_preview_image(vol)
                if img:
                    # Redimensionar para la vista previa
                    img.thumbnail((400, 300), Image.Resampling.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                    self.lbl_preview.configure(image=ctk_img, text="")
                    self.lbl_preview.image = ctk_img # Keep reference
                break

    def export_data(self):
        formats = [fmt for fmt in (self.chk_png_var.get(), self.chk_tiff_var.get()) if fmt]
        if not formats:
            messagebox.showwarning("Attention", "Please select at least one export format.")
            return

        output_dir = filedialog.askdirectory(title="Select destination directory")
        if not output_dir:
            return

        self.btn_export.configure(state="disabled")
        self.lbl_metadata.configure(text=self.lbl_metadata.cget("text") + "\nExporting... Please wait.")

        # Export in a separate thread
        threading.Thread(target=self._export_thread, args=(output_dir, formats), daemon=True).start()

    def _export_thread(self, output_dir, formats):
        try:
            file_base = os.path.splitext(os.path.basename(self.current_file_path))[0]
            # Create a folder for this file
            file_output_dir = os.path.join(output_dir, file_base)
            os.makedirs(file_output_dir, exist_ok=True)
            
            for v_idx, volume in enumerate(self.volumes):
                if volume is None or volume.volume is None:
                    continue
                vol_prefix = f"vol_{v_idx}"
                E2EProcessor.export_volume(volume, file_output_dir, vol_prefix, formats)
            
            # Export fundus/sweep images as well
            try:
                fundus_images = self.current_e2e_file.read_fundus_image()
                if fundus_images:
                    for f_idx, fundus in enumerate(fundus_images):
                        fundus_prefix = f"barrido_{f_idx}"
                        E2EProcessor.export_fundus(fundus, file_output_dir, fundus_prefix)
            except Exception as e:
                pass # Fail silently for fundus in single mode if error occurs

            self.after(0, self._on_export_finished, True, "Export completed successfully.")
        except Exception as e:
            self.after(0, self._on_export_finished, False, f"Error during export:\n{str(e)}")

    def _on_export_finished(self, success, message):
        self.btn_export.configure(state="normal")
        if success:
            messagebox.showinfo("Success", message)
            meta_text = self.lbl_metadata.cget("text").replace("\nExporting... Please wait.", "\nExport finished.")
            self.lbl_metadata.configure(text=meta_text)
        else:
            messagebox.showerror("Error", message)
            meta_text = self.lbl_metadata.cget("text").replace("\nExporting... Please wait.", "\nExport failed.")
            self.lbl_metadata.configure(text=meta_text)
