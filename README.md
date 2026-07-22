# GameTranslator

GameTranslator is a lightweight desktop OCR translation tool for Windows. It allows you to create one or more translation regions anywhere on your screen, automatically recognize text with OCR, translate it, and display the translated result in a transparent overlay.

The application is designed for games, visual novels, manga readers, livestreams, and other software that does not provide built-in translation.

---

## Features

- OCR text recognition using EasyOCR
- Multiple independent translation regions
- Automatic translation mode
- Manual translation by double-click
- Google Translate support
- Baidu Translate support
- Switch translation providers at runtime
- Overlay excluded from screen capture
- Transparent click-through overlay
- Adjustable translation region size
- Independent translation cache for better performance

---

## Screenshots

Add screenshots here.

Example:

```
screenshots/main_window.png
screenshots/overlay.png
```

---

## Requirements

- Windows 10 / Windows 11
- Python 3.10 or newer

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourname/GameTranslator.git
cd GameTranslator
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Command Prompt:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Running

Start the application:

```bash
python main.py
```

---

## Usage

### Create a Translation Region

Click **Add Region** to create a new translation area.

Move and resize the region so that it covers the text you want to translate.

---

### Manual Translation

Double-click inside the translation region.

The application will:

1. Capture the selected area.
2. Perform OCR.
3. Translate the recognized text.
4. Display the translation in the overlay.

---

### Automatic Translation

Right-click a translation region to enable automatic translation.

The application will periodically:

- Capture the region
- Detect text changes
- Translate only when necessary

Right-click again to stop automatic translation.

You can also stop every translation region simultaneously using **Stop All Auto Translation**.

---

### Edit Mode

When Edit Mode is enabled you can:

- Move regions
- Resize regions
- Delete regions

When Edit Mode is disabled:

- Regions become click-through
- Only translated text remains visible

---

## Translation Providers

### Google Translate

No additional configuration is required.

---

### Baidu Translate

To use Baidu Translate you need:

- APP ID
- Secret Key

Enter both values in the settings panel.

If either value is missing, translation will fail.

---

## Controls

| Action | Description |
|----------|-------------|
| Double-click | Translate once |
| Right-click | Toggle automatic translation |
| Drag | Move translation region |
| Bottom-right corner | Resize region |
| Close button | Delete translation region |

---

## Building

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the executable:

```bash
pyinstaller --noconfirm --clean --noupx --windowed --name GameTranslator --collect-all easyocr --collect-all torch --collect-all torchvision main.py
```

The executable will be generated in:

```
dist/GameTranslator/
```

---

## Project Structure

```
GameTranslator
│
├── main.py
├── main_window.py
├── translation_region.py
├── overlay_window.py
├── translation_engine.py
├── translation_worker.py
├── translator.py
├── ocr.py
├── screenshot.py
├── requirements.txt
└── README.md
```

---

## Known Limitations

- Windows only
- OCR accuracy depends on image quality
- Google Translate requires an Internet connection
- Baidu Translate requires a valid APP ID and Secret Key

---

## License

This project is licensed under the MIT License.
