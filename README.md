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

---

## Quick Start for Users

You do not need to install Python or configure a development environment to use GameTranslator.

### Download

Download the latest Windows version here:

**[Download GameTranslator for Windows](https://github.com/ADLXZ/game-translator/releases/latest)**


After downloading:

1. Extract the ZIP file to a folder.
2. Open the extracted folder.
3. Double-click `GameTranslator.exe`.
4. Wait for the application to start.

> Do not run the application directly from inside the ZIP file. Extract all files first.
>
> The first launch may take longer because the OCR system needs additional time to initialize.

---

## Basic Setup

### 1. Select a Translation Provider

Choose a translation provider from the main window:

- **Google Translate** — ready to use without additional configuration.
- **Baidu Translate** — requires your own APP ID and Secret Key.

For most users, Google Translate is the easiest option.

### 2. Select the Source and Target Languages

Choose:

- **Source Language** — the language shown in the game or application.
- **Target Language** — the language you want the text translated into.

Selecting the correct source language can improve OCR accuracy.

### 3. Create a Translation Region

Click **Add Region**.

A translation box will appear on the screen. Move and resize it so that it covers the text you want to translate.

For better OCR results:

- Keep the region close to the text.
- Avoid including character portraits, icons, or unrelated interface elements.
- Make sure the text is clearly visible.
- Create separate regions for text that appears in different parts of the screen.

---

## Main Window Buttons

| Button / Setting | Function |
|---|---|
| **Add Region** | Creates a new translation region on the screen. |
| **Edit Mode** | Allows you to move, resize, and delete translation regions. |
| **Stop All Auto Translation** | Stops automatic translation in every active region. |
| **Translation Provider** | Switches between Google Translate and Baidu Translate. |
| **Source Language** | Selects the language that GameTranslator should recognize. |
| **Target Language** | Selects the language used for the translated result. |
| **APP ID** | Your Baidu Translate APP ID. Only required when using Baidu Translate. |
| **Secret Key** | Your Baidu Translate Secret Key. Only required when using Baidu Translate. |

---

## Translation Region Controls

### Translate Once

**Double-click inside a translation region** to translate it once.

GameTranslator will:

1. Capture the selected screen area.
2. Recognize the text using OCR.
3. Translate the recognized text.
4. Display the result inside the transparent overlay.

### Start Automatic Translation

**Right-click inside a translation region** to start automatic translation.

The region will periodically check the selected area and translate new text when it detects a change.

### Stop Automatic Translation

**Right-click the region again** to stop automatic translation for that region.

To stop all regions at the same time, click **Stop All Auto Translation** in the main window.

### Move a Region

Enable **Edit Mode**, then drag the region to a new position.

### Resize a Region

Enable **Edit Mode**, then drag the bottom-right corner of the region.

### Delete a Region

Enable **Edit Mode**, then click the close button on the translation region.

### Click Through the Overlay

Disable **Edit Mode** when you finish positioning your regions.

The translation regions will become click-through, allowing you to continue controlling the game or application underneath them.

---

## Controls Summary

| Control | Action |
|---|---|
| **Double-click inside a region** | Translate once |
| **Right-click inside a region** | Start or stop automatic translation |
| **Drag the region** | Move the region while Edit Mode is enabled |
| **Drag the bottom-right corner** | Resize the region while Edit Mode is enabled |
| **Close button** | Delete the selected region |
| **Edit Mode enabled** | Move, resize, and delete regions |
| **Edit Mode disabled** | Make regions click-through |
| **Stop All Auto Translation** | Stop automatic translation in every region |

---

## Recommended Workflow

1. Start GameTranslator.
2. Select the source and target languages.
3. Keep **Google Translate** selected unless you want to use Baidu Translate.
4. Open your game or application.
5. Click **Add Region**.
6. Move and resize the region over the dialogue text.
7. Double-click the region to test the translation.
8. Right-click the region to enable automatic translation.
9. Disable **Edit Mode** so that the overlay no longer blocks mouse input.
10. Use **Stop All Auto Translation** when you want to pause every region.

---

## Troubleshooting

### The program does not start

- Make sure the ZIP file has been fully extracted.
- Do not move only `GameTranslator.exe`; keep all files in the extracted folder together.
- Try running the application as administrator.
- Check whether Windows Security or antivirus software has blocked the application.

### Automatic translation starts, but no translation appears

- Double-click the region to test manual translation.
- Make sure the translation region covers visible text.
- Check your Internet connection.
- Try switching the translation provider.
- Make sure the correct source language is selected.
- Restart the application if OCR initialization appears to be stuck.

### OCR does not recognize the text correctly

- Make the translation region smaller and keep it close to the text.
- Avoid including images, borders, or unrelated text.
- Increase the game’s text size when possible.
- Use clear, high-contrast text.
- Create separate regions for separate text areas.

### Google Translate does not work

Google Translate requires an active Internet connection. It may also be unavailable on some networks.

Try another network or use Baidu Translate instead.

### Baidu Translate does not work

Make sure:

- The APP ID is correct.
- The Secret Key is correct.
- Both fields have been entered.
- Your Baidu Translate account and API service are active.

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
