import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from core.extractor import E2EProcessor

class BatchModeUI(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)

        self.input_dir = None
        self.output_dir = None

        self.setup_ui()

    def setup_ui(self):
        # Top Panel: Directory Selection
        self.dir_frame = ctk.CTkFrame(self)
        self.dir_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.dir_frame.grid_columnconfigure(1, weight=1)

        self.btn_input = ctk.CTkButton(self.dir_frame, text="Source Folder (E2E)", command=self.select_input_dir)
        self.btn_input.grid(row=0, column=0, padx=10, pady=10)

        self.lbl_input = ctk.CTkLabel(self.dir_frame, text="No folder selected", text_color="gray")
        self.lbl_input.grid(row=0, column=1, padx=10, pady=10, sticky="w")

        self.btn_output = ctk.CTkButton(self.dir_frame, text="Destination Folder", command=self.select_output_dir)
        self.btn_output.grid(row=1, column=0, padx=10, pady=10)

        self.lbl_output = ctk.CTkLabel(self.dir_frame, text="No folder selected", text_color="gray")
        self.lbl_output.grid(row=1, column=1, padx=10, pady=10, sticky="w")

        # Options Panel
        self.options_frame = ctk.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.options_frame, text="Export Formats:").grid(row=0, column=0, padx=10, pady=10)

        self.chk_png_var = ctk.StringVar(value="png")
        self.chk_png = ctk.CTkCheckBox(self.options_frame, text="PNG", variable=self.chk_png_var, onvalue="png", offvalue="")
        self.chk_png.grid(row=0, column=1, padx=10, pady=10)

        self.chk_tiff_var = ctk.StringVar(value="")
        self.chk_tiff = ctk.CTkCheckBox(self.options_frame, text="TIFF", variable=self.chk_tiff_var, onvalue="tiff", offvalue="")
        self.chk_tiff.grid(row=0, column=2, padx=10, pady=10)

        # Action Panel
        self.action_frame = ctk.CTkFrame(self)
        self.action_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.action_frame.grid_columnconfigure(0, weight=1)
        
        self.btn_start = ctk.CTkButton(self.action_frame, text="Start Batch Processing", command=self.start_batch, fg_color="green", hover_color="darkgreen")
        self.btn_start.grid(row=0, column=0, padx=10, pady=10)

        # Progress Panel
        self.progress_frame = ctk.CTkFrame(self)
        self.progress_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        self.progress_frame.grid_columnconfigure(0, weight=1)

        self.lbl_progress = ctk.CTkLabel(self.progress_frame, text="Progress: 0%")
        self.lbl_progress.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        self.progressbar = ctk.CTkProgressBar(self.progress_frame)
        self.progressbar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.progressbar.set(0)

        # Log Panel
        self.log_textbox = ctk.CTkTextbox(self, wrap="word")
        self.log_textbox.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
        self.log_textbox.insert("0.0", "Waiting to start...\n")
        self.log_textbox.configure(state="disabled")

    def select_input_dir(self):
        folder = filedialog.askdirectory(title="Select source folder (E2E files)")
        if folder:
            self.input_dir = folder
            self.lbl_input.configure(text=folder, text_color="white")

    def select_output_dir(self):
        folder = filedialog.askdirectory(title="Select destination folder")
        if folder:
            self.output_dir = folder
            self.lbl_output.configure(text=folder, text_color="white")

    def log_message(self, message):
        """Thread-safe logging function"""
        def append_text():
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", message + "\n")
            self.log_textbox.see("end")
            self.log_textbox.configure(state="disabled")
        self.after(0, append_text)

    def update_progress(self, current, total):
        """Thread-safe progress update function"""
        def set_prog():
            percentage = current / total if total > 0 else 0
            self.progressbar.set(percentage)
            self.lbl_progress.configure(text=f"Progress: {int(percentage*100)}% ({current}/{total})")
        self.after(0, set_prog)

    def start_batch(self):
        if not self.input_dir or not self.output_dir:
            messagebox.showwarning("Missing directories", "Please select source and destination folders.")
            return

        formats = [fmt for fmt in (self.chk_png_var.get(), self.chk_tiff_var.get()) if fmt]
        if not formats:
            messagebox.showwarning("No formats", "Please select at least one export format.")
            return

        # Disable UI
        self.btn_input.configure(state="disabled")
        self.btn_output.configure(state="disabled")
        self.btn_start.configure(state="disabled")
        
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("0.0", "end")
        self.log_textbox.configure(state="disabled")

        self.progressbar.set(0)
        self.lbl_progress.configure(text="Progress: 0%")

        # Start thread
        threading.Thread(target=self._batch_thread, args=(formats,), daemon=True).start()

    def _batch_thread(self, formats):
        try:
            E2EProcessor.process_batch(
                self.input_dir, 
                self.output_dir, 
                formats, 
                progress_callback=self.update_progress, 
                log_callback=self.log_message
            )
            self.after(0, self._on_batch_finished, True)
        except Exception as e:
            self.log_message(f"[CRITICAL ERROR] {str(e)}")
            self.after(0, self._on_batch_finished, False)

    def _on_batch_finished(self, success):
        self.btn_input.configure(state="normal")
        self.btn_output.configure(state="normal")
        self.btn_start.configure(state="normal")
        if success:
            messagebox.showinfo("Completed", "Batch processing has finished.")
        else:
            messagebox.showerror("Error", "An unexpected error occurred during processing.")
