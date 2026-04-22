from __future__ import annotations

import ipaddress
import os
import mimetypes
import re
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any
from werkzeug.middleware.proxy_fix import ProxyFix

from dotenv import load_dotenv
load_dotenv()



from flask import Flask, jsonify, request, send_file, Response
from yt_dlp import YoutubeDL

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

FILE_TTL_SECONDS = 30 * 60
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".opus", ".flac"}


def read_int_env(name: str, default: int, minimum: int = 1) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return max(value, minimum)


RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "1") == "1"
RATE_LIMIT_API_ONLY = os.getenv("RATE_LIMIT_API_ONLY", "1") == "1"
RATE_LIMIT_WINDOW_SECONDS = read_int_env("RATE_LIMIT_WINDOW_SECONDS", default=60)
RATE_LIMIT_MAX_REQUESTS = read_int_env("RATE_LIMIT_MAX_REQUESTS", default=120)
RATE_LIMIT_BAN_SECONDS = read_int_env("RATE_LIMIT_BAN_SECONDS", default=300)
RATE_LIMIT_STATE_TTL_SECONDS = RATE_LIMIT_BAN_SECONDS + RATE_LIMIT_WINDOW_SECONDS + 60
YTDLP_USE_X_FORWARDED_FOR = os.getenv("YTDLP_USE_X_FORWARDED_FOR", "1") == "1"
PROXY_JUMPS = read_int_env("PROXIES", default=1)  # Default to 1 for typical Nginx setup

app = Flask(__name__, static_folder="files", static_url_path="/files")

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=PROXY_JUMPS, x_proto=PROXY_JUMPS, x_host=PROXY_JUMPS, x_prefix=PROXY_JUMPS
)

jobs: dict[str, dict[str, Any]] = {}
jobs_lock = threading.Lock()
rate_limit_state: dict[str, dict[str, Any]] = {}
rate_limit_lock = threading.Lock()


def now_ts() -> float:
    return time.time()


def get_client_ip() -> str:
    if PROXY_JUMPS > 0:
        # ProxyFix has already processed the headers
        return request.remote_addr or "unknown"
    
    # Fallback for when ProxyFix is disabled (PROXY_JUMPS=0)
    # Parse X-Forwarded-For manually
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        first_hop = forwarded_for.split(",")[0].strip()
        if first_hop:
            return first_hop

    return request.remote_addr or "unknown"


def get_ytdlp_xff_ip() -> str | None:
    if not YTDLP_USE_X_FORWARDED_FOR:
        return None

    # Use the already-validated client IP from get_client_ip()
    client_ip = get_client_ip()
    if client_ip == "unknown":
        return None

    # Validate it's a proper IP address
    try:
        ipaddress.ip_address(client_ip)
        return client_ip
    except ValueError:
        return None


def get_expected_api_key() -> str | None:
    configured_key = os.getenv("key") or os.getenv("API_KEY")
    if configured_key is None:
        return None

    normalized = configured_key.strip()
    if not normalized:
        return None

    return normalized


def get_provided_api_key(payload: dict[str, Any]) -> str:
    header_key = request.headers.get("X-Api-Key", "").strip()
    if header_key:
        return header_key

    auth_header = request.headers.get("Authorization", "").strip()
    if auth_header.lower().startswith("bearer "):
        bearer_key = auth_header[7:].strip()
        if bearer_key:
            return bearer_key

    return str(payload.get("key", "")).strip()


def check_rate_limit(ip_address: str) -> tuple[bool, int]:
    now = now_ts()

    with rate_limit_lock:
        state = rate_limit_state.setdefault(
            ip_address,
            {
                "hits": deque(),
                "banned_until": 0.0,
                "last_seen": now,
            },
        )

        state["last_seen"] = now
        banned_until = float(state.get("banned_until", 0.0))
        if banned_until > now:
            retry_after = max(1, int(banned_until - now))
            return False, retry_after

        hits = state["hits"]
        while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()

        hits.append(now)

        if len(hits) > RATE_LIMIT_MAX_REQUESTS:
            state["banned_until"] = now + RATE_LIMIT_BAN_SECONDS
            hits.clear()
            return False, RATE_LIMIT_BAN_SECONDS

    return True, 0


def to_iso(ts: float | None) -> str | None:
    if ts is None:
        return None
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def cleanup_rate_limit_state_loop() -> None:
    while True:
        cutoff = now_ts() - RATE_LIMIT_STATE_TTL_SECONDS

        with rate_limit_lock:
            stale_ips = [
                ip
                for ip, state in rate_limit_state.items()
                if float(state.get("last_seen", 0.0)) < cutoff
            ]

            for ip in stale_ips:
                rate_limit_state.pop(ip, None)

        time.sleep(60)


@app.before_request
def enforce_rate_limit():
    if not RATE_LIMIT_ENABLED:
        return None

    path = request.path
    if RATE_LIMIT_API_ONLY and not path.startswith("/api/"):
        return None

    ip_address = get_client_ip()
    allowed, retry_after = check_rate_limit(ip_address)
    if allowed:
        return None

    response = jsonify(
        {
            "error": "Too many requests from this IP. Try again later.",
            "ip": ip_address,
            "retryAfterSeconds": retry_after,
        }
    )
    response.status_code = 429
    response.headers["Retry-After"] = str(retry_after)
    return response


def is_valid_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def sanitize_filename(name: str | None) -> str:
    if not name:
        return "download"

    cleaned = re.sub(r"[\\/:*?\"<>|]+", "", name).strip()
    return cleaned[:120] if cleaned else "download"


def sanitize_video_id(video_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "", video_id).strip()
    if not cleaned:
        raise ValueError("Could not determine a valid video ID from the URL")
    return cleaned


def resolve_video_id(url: str) -> str:
    ydl_options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extract_flat": True,
    }

    with YoutubeDL(ydl_options) as ydl:  # type: ignore
        info = ydl.extract_info(url, download=False)

    if not isinstance(info, dict):
        raise ValueError("Could not read video metadata")

    raw_video_id = str(info.get("id", "")).strip()
    if not raw_video_id:
        raise ValueError("Could not resolve a video ID from the URL")

    return sanitize_video_id(raw_video_id)


def infer_mode_from_file(file_path: Path, requested_mode: str) -> str:
    if file_path.suffix.lower() in AUDIO_EXTENSIONS:
        return "audio"
    return requested_mode


def build_completed_job(video_id: str, mode: str, file_path: Path) -> dict[str, Any]:
    title = sanitize_filename(file_path.stem)
    return {
        "id": video_id,
        "url": "",
        "mode": mode,
        "status": "completed",
        "error": None,
        "title": title,
        "display_name": file_path.name,
        "file_path": str(file_path),
        "created_at": now_ts(),
        "completed_at": now_ts(),
        "delete_after": now_ts() + FILE_TTL_SECONDS,
        "deleted_at": None,
        "delete_reason": None,
        "ytdlp_xff_ip": None,
    }


def job_has_live_file(job: dict[str, Any]) -> bool:
    if job.get("status") != "completed":
        return False

    file_path = Path(job["file_path"]) if job.get("file_path") else None
    return bool(file_path and file_path.exists())


def find_downloaded_file(job_id: str) -> Path | None:
    matching_files = sorted(
        DOWNLOAD_DIR.glob(f"{job_id}.*"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for file_path in matching_files:
        if file_path.is_file():
            return file_path
    return None


def serialize_job(job: dict[str, Any]) -> dict[str, Any]:
    file_path = Path(job["file_path"]) if job.get("file_path") else None
    has_file = bool(job.get("status") == "completed" and file_path and file_path.exists())

    return {
        "id": job["id"],
        "videoId": job["id"],
        "mode": job["mode"],
        "status": job["status"],
        "title": job.get("title"),
        "error": job.get("error"),
        "hasFile": has_file,
        "previewUrl": f"/api/jobs/{job['id']}/preview" if has_file else None,
        "downloadUrl": f"/api/jobs/{job['id']}/download" if has_file and job["status"] == "completed" else None,
        "createdAt": to_iso(job.get("created_at")),
        "completedAt": to_iso(job.get("completed_at")),
        "expiresAt": to_iso(job.get("delete_after")),
        "deletedAt": to_iso(job.get("deleted_at")),
        "deleteReason": job.get("delete_reason"),
    }


def delete_job_file(job_id: str, reason: str) -> bool:
    with jobs_lock:
        job = jobs.get(job_id)
        if not job or not job.get("file_path"):
            return False
        file_path = Path(job["file_path"])

    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        return False

    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return True
        job["file_path"] = None
        job["delete_after"] = None
        job["deleted_at"] = now_ts()
        job["delete_reason"] = reason
        if job["status"] == "completed":
            job["status"] = "deleted"

    return True


def cleanup_expired_files_loop() -> None:
    while True:
        now = now_ts()
        expired_job_ids: list[str] = []

        with jobs_lock:
            for job_id, job in jobs.items():
                if job.get("status") != "completed":
                    continue

                delete_after = job.get("delete_after")
                if delete_after is not None and now >= delete_after:
                    expired_job_ids.append(job_id)

        for job_id in expired_job_ids:
            delete_job_file(job_id, "expired")

        time.sleep(15)


def download_worker(job_id: str, url: str, mode: str, ytdlp_xff_ip: str | None) -> None:
    def progress_hook(progress_data: dict[str, Any]) -> None:
        filename = progress_data.get("filename")
        status = progress_data.get("status")

        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return

            if status == "downloading":
                job["status"] = "downloading"

            if filename:
                job["file_path"] = str(Path(filename))

    with jobs_lock:
        job = jobs.get(job_id)
        if job:
            job["status"] = "downloading"

    try:
        ydl_options: dict[str, Any] = {
            "format": "bestaudio/best" if mode == "audio" else "best[ext=mp4]/best",
            "outtmpl": str(DOWNLOAD_DIR / f"{job_id}.%(ext)s"),
            "noplaylist": True,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "no_warnings": True,
        }

        if ytdlp_xff_ip:
            ydl_options["http_headers"] = {"X-Forwarded-For": ytdlp_xff_ip}

        if mode == "audio":
            ydl_options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ]

        with YoutubeDL(ydl_options) as ydl: # type: ignore
            info = ydl.extract_info(url, download=True)

        final_file = find_downloaded_file(job_id)
        if final_file is None:
            raise FileNotFoundError("Downloaded file could not be found.")

        title = sanitize_filename(info.get("title") if isinstance(info, dict) else None)
        display_name = f"{title}{final_file.suffix}"

        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return

            job["status"] = "completed"
            job["title"] = title
            job["display_name"] = display_name
            job["file_path"] = str(final_file)
            job["completed_at"] = now_ts()
            job["delete_after"] = now_ts() + FILE_TTL_SECONDS

    except Exception as exc:
        with jobs_lock:
            job = jobs.get(job_id)
            if not job:
                return
            job["status"] = "failed"
            job["error"] = str(exc)


@app.get("/")
def index() -> Response:
    return send_file(FILES_DIR / "index.html")

@app.get('/files/index.js')
def indexjs() -> Response:
    return send_file(FILES_DIR / "index.js")

@app.get('/files/index.css')
def indexcss() -> Response:
    return send_file(FILES_DIR / "index.css")


@app.post("/api/download")
def create_download_job():
    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url", "")).strip()
    mode = str(payload.get("mode", "video")).strip().lower()

    expected_api_key = get_expected_api_key()
    if expected_api_key is not None:
        provided_api_key = get_provided_api_key(payload)
        if not provided_api_key or provided_api_key != expected_api_key:
            return jsonify({"error": "Missing or invalid key."}), 401

    if mode == "a":
        mode = "audio"
    elif mode == "v":
        mode = "video"

    if not is_valid_url(url):
        return jsonify({"error": "Please provide a valid URL starting with http:// or https://"}), 400

    if mode not in {"audio", "video"}:
        return jsonify({"error": "mode must be 'audio' or 'video'"}), 400

    ytdlp_xff_ip = get_ytdlp_xff_ip()

    try:
        video_id = resolve_video_id(url)
    except Exception as exc:
        return jsonify({"error": f"Could not resolve video ID: {exc}"}), 400

    with jobs_lock:
        existing_job = jobs.get(video_id)

        if existing_job and existing_job.get("status") in {"queued", "downloading"}:
            response_payload = serialize_job(existing_job)
            response_payload["reused"] = True
            return jsonify(response_payload), 202

        if existing_job and job_has_live_file(existing_job):
            response_payload = serialize_job(existing_job)
            response_payload["reused"] = True
            return jsonify(response_payload), 200

    existing_file = find_downloaded_file(video_id)
    if existing_file:
        recovered_mode = infer_mode_from_file(existing_file, mode)
        recovered_job = build_completed_job(video_id, recovered_mode, existing_file)

        with jobs_lock:
            jobs[video_id] = recovered_job

        response_payload = serialize_job(recovered_job)
        response_payload["reused"] = True
        return jsonify(response_payload), 200

    job_id = video_id
    job = {
        "id": job_id,
        "url": url,
        "mode": mode,
        "status": "queued",
        "error": None,
        "title": None,
        "display_name": None,
        "file_path": None,
        "created_at": now_ts(),
        "completed_at": None,
        "delete_after": None,
        "deleted_at": None,
        "delete_reason": None,
        "ytdlp_xff_ip": ytdlp_xff_ip,
    }

    with jobs_lock:
        existing_job = jobs.get(job_id)
        if existing_job and existing_job.get("status") in {"queued", "downloading"}:
            response_payload = serialize_job(existing_job)
            response_payload["reused"] = True
            return jsonify(response_payload), 202

        jobs[job_id] = job

    threading.Thread(target=download_worker, args=(job_id, url, mode, ytdlp_xff_ip), daemon=True).start()

    response_payload = serialize_job(job)
    response_payload["reused"] = False
    return jsonify(response_payload), 202


@app.get("/api/jobs/<job_id>")
def get_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(serialize_job(job))


@app.get("/api/jobs/<job_id>/preview")
def preview_job_file(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job["status"] != "completed":
            return jsonify({"error": "File is not ready for preview yet"}), 409

        file_path = Path(job["file_path"]) if job.get("file_path") else None
        mode = job["mode"]

    if not file_path or not file_path.exists():
        return jsonify({"error": "File is no longer available"}), 410

    mime_type = mimetypes.guess_type(file_path.name)[0]
    if mime_type is None:
        mime_type = "audio/mpeg" if mode == "audio" else "video/mp4"

    return send_file(
        file_path,
        as_attachment=False,
        mimetype=mime_type,
    )


@app.post("/api/jobs/<job_id>/delete")
def delete_job(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        status = job["status"]

    if status == "deleted":
        with jobs_lock:
            current_job = jobs.get(job_id)
            if not current_job:
                return jsonify({"error": "Job not found"}), 404
            return jsonify(serialize_job(current_job))

    if status != "completed":
        return jsonify({"error": "Only completed files can be deleted"}), 409

    deleted = delete_job_file(job_id, "user_deleted")
    if not deleted:
        return jsonify({"error": "File is currently in use. Stop preview/playback and try delete again."}), 409

    with jobs_lock:
        current_job = jobs.get(job_id)
        if not current_job:
            return jsonify({"error": "Job not found"}), 404
        return jsonify(serialize_job(current_job))


@app.get("/api/jobs/<job_id>/download")
def download_job_file(job_id: str):
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        if job["status"] != "completed":
            return jsonify({"error": "File is not ready for download yet"}), 409

        file_path = Path(job["file_path"]) if job.get("file_path") else None
        download_name = job.get("display_name") or "download"

    if not file_path or not file_path.exists():
        return jsonify({"error": "File is no longer available"}), 410

    response = send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
        conditional=True,
    )

    @response.call_on_close
    def delete_after_response() -> None:
        delete_job_file(job_id, "downloaded")

    return response


threading.Thread(target=cleanup_expired_files_loop, daemon=True).start()
threading.Thread(target=cleanup_rate_limit_state_loop, daemon=True).start()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)