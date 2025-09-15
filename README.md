This project allows users to upload a single-page PDF label, choose which of the 4 slots (on an A4 sheet) to paste it into, preview the composed A4 template, and download a PDF ready for printing.


## Features
- Convert uploaded PDF to a high-quality image (300 DPI)
- Paste into a 100x150 mm slot on an A4 template
- Preview the final composed A4 image
- Download as PDF


## Run locally
1. Install poppler (required by pdf2image): on Debian/Ubuntu: `sudo apt-get install poppler-utils`
2. Create a virtualenv and install requirements: `pip install -r requirements.txt`
3. Run: `streamlit run app.py`
4. Open http://localhost:5000


## Docker
Build: `docker build -t meesho-label-app .`
Run: `docker run -p 5000:5000 meesho-label-app`