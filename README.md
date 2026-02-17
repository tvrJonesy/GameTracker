# GameTracker ⚽

**Dual-camera football match processor** — stitch, track, and follow the ball automatically.

Built for 9v9 Under-11s football with two action cameras on a tall tripod.

---

## Features

- 🪡 **Panorama stitching** — auto-detects and removes overlap at the centre of the pitch
- 🏃 **Player tracking** — YOLO detection + OCR reads shirt numbers #20–35
- 🏷️ **Player name tags** — first names float above each player in kit colours
- ⚽ **Ball tracking** — Kalman filter keeps lock even during occlusion
- 🥅 **Auto goal detection** — ball-crossing-line detection with manual confirmation
- 🎬 **Ball-following video** — smooth virtual camera output with all overlays

---

## How to Deploy (Streamlit Community Cloud)

### 1. Fork / push this repo to GitHub

```bash
git init
git add .
git commit -m "Initial GameTracker app"
git remote add origin https://github.com/YOUR_USERNAME/gametracker.git
git push -u origin main
```

### 2. Deploy on Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repo, branch `main`, and set **Main file path** to `app.py`
5. Click **Deploy**

Your app will be live at `https://YOUR_USERNAME-gametracker-app-XXXX.streamlit.app` in ~2 minutes.

---

## Processing Backend (Google Colab)

This Streamlit app is the **front-end only**. Actual video processing runs in a free Google Colab notebook with GPU.

See the **GameTracker Processing Engine Guide** (Word document) for full setup instructions.

### Quick start

1. Open [Google Colab](https://colab.research.google.com)
2. Set runtime to **T4 GPU** (Runtime → Change runtime type)
3. Run the setup cells (install dependencies, mount Drive, start server)
4. Copy the ngrok URL into the web app at Step 5

---

## Project Structure

```
gametracker/
├── app.py                  # Main entry point — wizard navigation
├── requirements.txt        # Streamlit only (processing deps live in Colab)
├── .streamlit/
│   └── config.toml         # Dark theme config
└── pages/
    ├── step1_upload.py     # File upload + match details + kit colours
    ├── step2_stitch.py     # Panorama stitch settings
    ├── step3_tracking.py   # Player, ball and goal tracking settings
    ├── step3b_squad.py     # Player name entry + live tag preview
    ├── step4_output.py     # Output mode + overlay selection
    └── step5_processing.py # Settings review + job submission + progress
```

---

## Camera Setup

| Setting | Recommendation |
|---------|----------------|
| Tripod height | Minimum 4m at the halfway line |
| Camera angle | 30–40° downward from horizontal |
| Resolution | 1080p @ 60fps |
| Stabilisation | **OFF** — warps stitching |
| Exposure | Locked if possible |
| Overlap | Aim for 15–20% at centre circle |
| Sync method | Loud clap in front of both cameras |

---

## Free Software Stack (Processing Backend)

| Library | Purpose |
|---------|---------|
| OpenCV 4.x | Lens correction, feature matching, stitching, blending |
| FFmpeg | Video decode/encode, audio sync |
| YOLOv8 (Ultralytics) | Player and ball detection |
| EasyOCR | Shirt number reading (#20–35) |
| FilterPy | Kalman filter for ball tracking |
| FastAPI | Job submission API in Colab |
| ngrok | Temporary public URL for Colab session |

**Total software cost: £0**

---

*Built for grassroots football. Free and open source.*
