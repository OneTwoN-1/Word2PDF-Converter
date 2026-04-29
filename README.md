# 📄 Word2PDF — Local Document Converter

A lightweight Flask web app that converts documents between **PDF ↔ Word (.docx/.doc)** entirely on your machine. No cloud, no uploads to third parties, no nonsense.

&emsp; Built as a personal project.

---

## 1.Features

- **PDF → DOCX** conversion using `pdf2docx`
- **DOCX / DOC → PDF** conversion using LibreOffice headless
- Auto-detects file type on drop and switches mode automatically
- Displays PDF metadata (pages, title, author) before converting
- Files are automatically deleted from the server after **5 minutes**
- 50 MB file size limit
- Runs fully local — nothing leaves your machine

---

## 2.Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask |
| PDF → Word | `pdf2docx` + `PyMuPDF` (pinned to 1.23.8) |
| Word → PDF | LibreOffice (headless CLI via `soffice`) |
| PDF metadata | `pypdf` |
| Frontend | Vanilla HTML / CSS / JavaScript |

---

## 3.Requirements

### System dependency (must install manually)

In the requirements.txt file will be all the dependencies required by this project to work. Just hit `pip freeze > requirements.txt`
Down below will be all the steps that you have to go through to get this up and running. I know it's a bit demanding, but once you go trough all of this, you will have a perfectly working local converter. 

LibreOffice is required for Word → PDF conversion. It is **not** installable via pip.

```bash
# Ubuntu / Debian / WSL
sudo apt update && sudo apt install -y libreoffice

# macOS
brew install --cask libreoffice
```

Verify it works:
```bash
soffice --version
```

### Python dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ **Important:** `PyMuPDF` is pinned to `1.23.8` on purpose. Versions `≥ 1.24` break `pdf2docx` with a `Rect.get_area()` error. Do not upgrade it.

---

## 4. Running the App
 
```bash
# Clone the repo
git clone https://github.com/OneTwoN-1/Word2PDF-Converter.git
cd Word2PDF-Converter
```
I highly recommend to use a virtual environment to keep dependencies isolated and avoid conflicts with your systems Python.

```bash
#Install virtual environment
python -m venv venv

#Activate environment-mac
source venv/bin/activate
#venv/Scripts/activate -for windows

# Install Python dependencies
pip install -r requirements.txt

# Run
python Converter.py
```

Then open your browser at: **http://127.0.0.1:5001**

---

## 5. Project Structure

```
docshift/
│
├── app.py                 # Flask backend — all conversion logic
├── requirements.txt       # Python dependencies (pinned)
│
├── templates/
│   └── page.html          # Single-page frontend (HTML + CSS + JS)
│
├── uploads/               # Temp folder — uploaded files (auto-deleted)
└── converted/             # Temp folder — converted output (auto-deleted)
```

> The `uploads/` and `converted/` folders are created automatically on first run. You don't need to create them manually.
NOTE: The files will be deleted only if you keep the app running. If you close it, the folders will remain on your machine

---

## 6. How It Works

```
User drops file
      │
      ▼
POST /info  ──► Flask reads PDF metadata (pages, title, author)
                and returns JSON to display in the UI
      │
      ▼
POST /convert ──► Flask detects file extension
                      │
                      ├── .pdf   ──► pdf2docx ──► .docx
                      │
                      ├── .docx  ──► LibreOffice soffice ──► .pdf
                      │
                      └── .doc   ──► LibreOffice (doc→docx first)
                                         └──► LibreOffice ──► .pdf
                      │
                      ▼
               send_file() streams result back to browser
               (files scheduled for deletion after 5 min)
```

---
