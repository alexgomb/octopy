import customtkinter as ctk
import webbrowser
import os
from PIL import Image
from ui.single_mode_ui import SingleModeUI
from ui.batch_mode_ui import BatchModeUI

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window configuration
        self.title("OCToPy - Heidelberg E2E OCT Extractor")
        self.geometry("800x600")
        self.minsize(700, 500)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)

        self.tab_single = self.tabview.add("Single File Mode")
        self.tab_batch = self.tabview.add("Batch Processing")
        self.tab_about = self.tabview.add("About")

        # Layout for tabs
        self.tab_single.grid_rowconfigure(0, weight=1)
        self.tab_single.grid_columnconfigure(0, weight=1)

        self.tab_batch.grid_rowconfigure(0, weight=1)
        self.tab_batch.grid_columnconfigure(0, weight=1)

        self.tab_about.grid_rowconfigure(0, weight=1)
        self.tab_about.grid_columnconfigure(0, weight=1)

        # UI Components
        self.single_mode = SingleModeUI(self.tab_single)
        self.single_mode.pack(fill="both", expand=True)

        self.batch_mode = BatchModeUI(self.tab_batch)
        self.batch_mode.pack(fill="both", expand=True)

        # About Tab Components
        self._build_about_tab()

    def _build_about_tab(self):
        about_frame = ctk.CTkScrollableFrame(self.tab_about)
        about_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Load and display logo
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                # Ensure the logo is displayed at a reasonable size
                logo_ctk = ctk.CTkImage(light_image=logo_img, dark_image=logo_img, size=(180, 180))
                lbl_logo = ctk.CTkLabel(about_frame, text="", image=logo_ctk)
                lbl_logo.pack(pady=(10, 5))
        except Exception as e:
            pass

        title_font = ctk.CTkFont(size=28, weight="bold")
        ctk.CTkLabel(about_frame, text="OCToPy", font=title_font).pack(pady=(5, 5))
        ctk.CTkLabel(about_frame, text="Heidelberg E2E OCT Extractor", font=ctk.CTkFont(size=14)).pack(pady=(0, 15))

        ctk.CTkLabel(about_frame, text="Developed by:", font=ctk.CTkFont(weight="bold", size=14)).pack(pady=(10, 5))
        ctk.CTkLabel(about_frame, text="Alejandro Gombau Garcia").pack()

        link_font = ctk.CTkFont(underline=True)

        lbl_linkedin = ctk.CTkLabel(about_frame, text="LinkedIn", font=link_font, text_color="#1f6aa5", cursor="hand2")
        lbl_linkedin.pack(pady=(10, 5))
        lbl_linkedin.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.linkedin.com/in/alejandro-gombau/"))

        lbl_github = ctk.CTkLabel(about_frame, text="GitHub", font=link_font, text_color="#1f6aa5", cursor="hand2")
        lbl_github.pack(pady=5)
        lbl_github.bind("<Button-1>", lambda e: webbrowser.open_new("https://github.com/alexgomb"))

        ctk.CTkLabel(about_frame, text="Email: alex.gombau96@gmail.com").pack(pady=(10, 10))

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
