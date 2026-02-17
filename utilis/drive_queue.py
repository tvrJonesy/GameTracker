"""
drive_queue.py — Google Drive job queue for GameTracker

How it works:
  1. Streamlit writes  GameTracker/jobs/job_<id>.json   (job spec)
  2. Colab polls that folder every 30 s, picks up new jobs
  3. Colab writes  GameTracker/jobs/status_<id>.json    (progress)
  4. Streamlit polls status every 5 s and updates the UI

Authentication uses a Google Service Account JSON key stored in
Streamlit Community Cloud secrets (st.secrets["gcp_service_account"]).
The same key is stored in Colab as a mounted secret.
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from typing import Optional

import streamlit as st

# ── Optional import — only needed at runtime, not syntax-check time ────────
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
    import io
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False


SCOPES = ["https://www.googleapis.com/auth/drive"]
JOBS_FOLDER_NAME = "jobs"          # subfolder inside GameTracker/
STATUS_PREFIX    = "status_"
JOB_PREFIX       = "job_"


# ── Drive client ────────────────────────────────────────────────────────────

def _get_drive_service():
    """Build and return an authenticated Drive service using st.secrets."""
    if not GDRIVE_AVAILABLE:
        raise RuntimeError(
            "google-api-python-client is not installed. "
            "Add it to requirements.txt and redeploy."
        )
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _get_or_create_folder(service, name: str, parent_id: str) -> str:
    """Return the ID of a folder inside parent, creating it if needed."""
    q = (
        f"name='{name}' and mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = service.files().list(q=q, fields="files(id)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id],
    }
    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]


def _write_json(service, folder_id: str, filename: str, data: dict) -> str:
    """Upload (or overwrite) a JSON file in a Drive folder. Returns file ID."""
    content = json.dumps(data, indent=2).encode("utf-8")
    media = MediaIoBaseUpload(
        io.BytesIO(content), mimetype="application/json", resumable=False
    )
    # Check if file already exists (overwrite)
    q = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    existing = service.files().list(q=q, fields="files(id)").execute().get("files", [])
    if existing:
        service.files().update(
            fileId=existing[0]["id"], media_body=media
        ).execute()
        return existing[0]["id"]
    else:
        meta = {"name": filename, "parents": [folder_id]}
        f = service.files().create(
            body=meta, media_body=media, fields="id"
        ).execute()
        return f["id"]


def _read_json(service, folder_id: str, filename: str) -> Optional[dict]:
    """Read a JSON file from a Drive folder. Returns None if not found."""
    q = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=q, fields="files(id)").execute()
    files = results.get("files", [])
    if not files:
        return None
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(
        buf, service.files().get_media(fileId=files[0]["id"])
    )
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    return json.loads(buf.read().decode("utf-8"))


# ── Public API ──────────────────────────────────────────────────────────────

def submit_job(root_folder_id: str, job_payload: dict) -> str:
    """
    Write a job JSON file to Drive. Returns the job_id.
    The job file is named job_<id>.json and contains the full
    match settings plus squad names and overlay config.
    """
    service   = _get_drive_service()
    jobs_folder = _get_or_create_folder(service, JOBS_FOLDER_NAME, root_folder_id)

    job_id   = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    filename = f"{JOB_PREFIX}{job_id}.json"

    payload = {
        "job_id":    job_id,
        "submitted": datetime.utcnow().isoformat(),
        "status":    "queued",
        **job_payload,
    }
    _write_json(service, jobs_folder, filename, payload)
    return job_id


def get_status(root_folder_id: str, job_id: str) -> Optional[dict]:
    """
    Poll Drive for a status file written by Colab.
    Returns the status dict or None if not yet written.

    Status dict shape (written by Colab):
    {
      "job_id":   "...",
      "status":   "queued" | "running" | "done" | "error",
      "stage":    "Stitching" | "Tracking" | ...,
      "stage_index": 3,
      "stage_total": 7,
      "progress": 0–100,
      "message":  "human-readable detail",
      "output_folder_id": "...",   # set when done
      "error":    "..."            # set on error
    }
    """
    service     = _get_drive_service()
    jobs_folder = _get_or_create_folder(service, JOBS_FOLDER_NAME, root_folder_id)
    filename    = f"{STATUS_PREFIX}{job_id}.json"
    return _read_json(service, jobs_folder, filename)


def get_heartbeat(root_folder_id: str) -> Optional[dict]:
    """
    Read the heartbeat file written by the Colab watcher every 30 seconds.
    Returns None if Colab is not running or heartbeat is stale (> 90 seconds old).

    Heartbeat file shape (written by Colab):
    {
      "alive":     true,
      "updated":   "2024-01-01T10:30:00",   # UTC ISO
      "gpu":       "Tesla T4",
      "job_count": 3                          # jobs processed this session
    }
    """
    try:
        service = _get_drive_service()
        jobs_folder = _get_or_create_folder(service, JOBS_FOLDER_NAME, root_folder_id)
        data = _read_json(service, jobs_folder, "heartbeat.json")
        if data is None:
            return None
        # Check staleness — if last update was > 90 seconds ago, Colab has died
        from datetime import timezone
        updated_str = data.get("updated", "")
        if updated_str:
            updated = datetime.fromisoformat(updated_str)
            age = (datetime.utcnow() - updated).total_seconds()
            if age > 90:
                return {"alive": False, "age_seconds": int(age)}
        return data
    except Exception:
        return None


def build_job_payload(ss) -> dict:
    """
    Build the full job payload dict from Streamlit session_state (ss).
    This is everything Colab needs to run the processing pipeline.
    """
    return {
        # Match info
        "match": {
            "home_name":    ss.get("home_name", ""),
            "away_name":    ss.get("away_name", ""),
            "match_date":   str(ss.get("match_date", "")),
            "home_colour":  ss.get("home_colour", "#ef4444"),
            "away_colour":  ss.get("away_colour", "#3b82f6"),
        },
        # Stitch settings
        "stitch": {
            "seam_auto":      ss.get("seam_auto", True),
            "overlap_pct":    ss.get("overlap_pct", 18),
            "lens_correct":   ss.get("lens_correct", True),
            "colour_match":   ss.get("colour_match", True),
            "stabilise":      ss.get("stabilise", True),
            "preview_stitch": ss.get("preview_stitch", True),
            "camera_model":   ss.get("camera_model", "Generic action camera (auto-calibrate)"),
        },
        # Tracking settings
        "tracking": {
            "shirt_min":      ss.get("shirt_min", 20),
            "shirt_max":      ss.get("shirt_max", 35),
            "ball_colour":    ss.get("ball_colour", "White (standard)"),
            "kalman_window":  ss.get("kalman_window", 1.5),
            "goal_conf":      ss.get("goal_conf", 75),
            "halftime_mins":  ss.get("halftime_mins", 10),
        },
        # Squad names  { "20": "JAMES", "21": "OLIVER", ... }
        "squad": {
            "home": {
                str(k): v
                for k, v in ss.get("squad_home", {}).items() if v
            },
            "away": {
                str(k): v
                for k, v in ss.get("squad_away", {}).items() if v
            },
        },
        # Output settings
        "output": {
            "follow_ball":    ss.get("follow_ball", True),
            "resolution":     ss.get("resolution", "1920×1080 (1080p)"),
            "fps":            ss.get("fps", "60 fps"),
            "export_fmt":     ss.get("export_fmt", "MP4 (H.264)"),
            "overlays": {
                "score":      ss.get("ov_score", True),
                "timer":      ss.get("ov_timer", True),
                "names":      ss.get("ov_names", True),
                "numbers":    ss.get("ov_numbers", True),
                "ball_trail": ss.get("ov_ball_trail", True),
                "speed":      ss.get("ov_speed", False),
                "heatmap":    ss.get("ov_heatmap", False),
                "goal_alert": ss.get("ov_goal_alert", False),
            },
        },
        # File names (uploaded to Drive's raw/ folder by the app)
        "files": {
            "cam_a": ss.get("cam_a_filename", ""),
            "cam_b": ss.get("cam_b_filename", ""),
        },
    }
