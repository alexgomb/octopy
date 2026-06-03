# OCToPy - Heidelberg E2E OCT Extractor

A desktop GUI application built in Python to easily read, visualize, and export Optical Coherence Tomography (OCT) volumes and fundus images from Heidelberg Engineering's proprietary `.e2e` files. 

This tool is designed for researchers, clinicians, and users without programming knowledge who need a reliable and user-friendly way to convert proprietary clinical data into standard image formats.

## Purpose
The application leverages the `oct-converter` library to parse `.e2e` files. It bridges the gap between raw clinical data and downstream analysis by providing an intuitive graphical interface to browse scans and batch-export them without writing a single line of code.

## Features
* **Single File Mode**: Open an `.e2e` file, view metadata, preview the central B-Scan with correct anatomical proportions, and export it.
* **Batch Processing Mode**: Select an input directory containing multiple `.e2e` files and a destination folder. The app will process everything unattended in the background, showing a progress bar and a detailed log.
* **Multiple Export Formats**: 
  * `PNG` (Individual slices)
  * `TIFF` (Multi-page stacked volume)
* **Anatomical Scale Preservation**: Unlike raw data arrays, this tool automatically recalculates and stretches the images using the device's metadata (`pixel_spacing`) so the exported images maintain their true physical aspect ratios.
* **Automatic Scale Bar**: A scale bar (1mm, 500um, 200um, or 100um) is automatically drawn at the bottom-left corner of all exported OCT B-Scans and Fundus (sweep) images to allow accurate measurements in external software.
* **Responsive UI**: Built with `CustomTkinter` and multi-threading, ensuring the interface never freezes during heavy I/O operations.

## Libraries and Tech Stack
* **UI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
* **OCT Engine**: [oct-converter](https://github.com/marksgraham/OCT-Converter)
* **Image Processing**: `numpy`, `Pillow`, `opencv-python`
* **Deployment**: `pyinstaller`

## Installation Guide

### Prerequisites
Python 3.8 or higher is required. 

### Installation on Windows
1. Clone or download this repository to your local machine.
2. Open a terminal (Command Prompt or PowerShell) and navigate to the project folder:
   ```cmd
   cd path\to\e2e_exporter
   ```
3. Create a virtual environment:
   ```cmd
   python -m venv venv
   ```
4. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
5. Install the required dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
6. Run the application:
   ```cmd
   python app.py
   ```

### Installation on Linux (Ubuntu/Debian)
1. Ensure the Python `tkinter` package is installed on your system:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-tk python3-venv
   ```
2. Clone or download this repository to your local machine.
3. Open a terminal and navigate to the project folder:
   ```bash
   cd path/to/e2e_exporter
   ```
4. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
5. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
6. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
7. Run the application:
   ```bash
   python app.py
   ```

## Dockerization (Reproducibility)
If you prefer not to install Python or manage local dependencies, you can run the application inside an isolated Docker container. This guarantees a 100% reproducible environment.

### 1. Build the Docker Image
Open a terminal in the project folder and build the image:
```bash
docker build -t e2e-extractor .
```

### 2. Run the Container
Running a GUI application from Docker requires passing the display environment and mounting a volume so the app can read your `.e2e` files and save the exports to your host machine.

**On Linux:**
You need to allow local connections to the X server, then run the container mapping your current directory to `/workspace` inside the container:
```bash
xhost +local:docker
docker run -it --rm \
    --env="DISPLAY" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$(pwd):/workspace" \
    e2e-extractor
```
*(When the app opens, navigate to `/workspace` in the file explorer to access your host files).*

**On Windows:**
You will need an X11 server for Windows (such as [VcXsrv](https://sourceforge.net/projects/vcxsrv/)). 
1. Start VcXsrv (XLaunch) with "Multiple windows" and check "Disable access control".
2. Run the container:
```cmd
docker run -it --rm ^
    --env="DISPLAY=host.docker.internal:0.0" ^
    --volume="%cd%:/workspace" ^
    e2e-extractor
```

## Building a Standalone Executable
If you want to share the application with users who do not have Python installed, you can compile it into a single executable file.

With your virtual environment activated, run the included build script:
```bash
python build_script.py
```
Wait for the compilation to finish. The standalone executable (e.g., `E2E_Extractor.exe` on Windows or a binary on Linux) will be generated inside the `dist/` folder.
