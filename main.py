import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import threading
import os
import json
import subprocess
import sys
from io import BytesIO
from datetime import datetime
import urllib.request
from PIL import Image, ImageDraw


# ============================================================
# ROCKTUBE DOWNLOADER
# Version 2.2.1
# ============================================================

APP_NAME = "RockTube Downloader"
APP_VERSION = "2.2.1"
DEVELOPER = "Mr.Sulim.Inc"

# ------------------------------------------------------------
# Application files
# ------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FFmpeg is bundled in the candidate's internal runtime folder.
FFMPEG_DIR = os.path.join(
    getattr(sys, "_MEIPASS", BASE_DIR),
    "ffmpeg"
)

LOGO_FILE = os.path.join(BASE_DIR, "rocktube_logo.png")
ICON_FILE = os.path.join(BASE_DIR, "rocktube.ico")

# ------------------------------------------------------------
# App data
# ------------------------------------------------------------

APP_DATA = os.path.join(
    os.getenv("APPDATA") or os.path.expanduser("~"),
    "RockTube Downloader"
)

os.makedirs(APP_DATA, exist_ok=True)

HISTORY_FILE = os.path.join(APP_DATA, "history.json")
SETTINGS_FILE = os.path.join(APP_DATA, "settings.json")


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_SETTINGS = {
    "download_folder": os.path.join(
        os.path.expanduser("~"),
        "Downloads"
    ),
    "theme": "Dark",
    "quality": "Best Available"
}


# ============================================================
# JSON FUNCTIONS
# ============================================================

def load_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass

    if isinstance(default, dict):
        return default.copy()

    if isinstance(default, list):
        return list(default)

    return default


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=4,
                ensure_ascii=False
            )
        return True
    except Exception:
        return False


settings = load_json(
    SETTINGS_FILE,
    DEFAULT_SETTINGS
)

if not isinstance(settings, dict):
    settings = DEFAULT_SETTINGS.copy()


download_folder = settings.get(
    "download_folder",
    DEFAULT_SETTINGS["download_folder"]
)

if not os.path.isdir(download_folder):
    download_folder = DEFAULT_SETTINGS["download_folder"]

settings["download_folder"] = download_folder

history = load_json(
    HISTORY_FILE,
    []
)

if not isinstance(history, list):
    history = []


# ============================================================
# APPEARANCE
# ============================================================

ctk.set_appearance_mode(
    settings.get("theme", "Dark")
)

ctk.set_default_color_theme(
    "dark-blue"
)


# ============================================================
# COLORS
# ============================================================

BG = "#080808"
SIDEBAR = "#0D0D0D"
CARD = "#111111"
CARD_2 = "#151515"
RED = "#E50914"
RED_HOVER = "#B80710"
TEXT = "#F5F5F5"
MUTED = "#8E8E8E"
GREEN = "#24D05A"
BORDER = "#242424"


# ============================================================
# GLOBAL VARIABLES
# ============================================================

video_info = None
thumbnail_image = None
about_logo_image = None
sidebar_logo_image = None
app_icon_image = None

current_ydl = None
download_cancelled = False
download_running = False

app = None
content_frame = None

url_entry = None
quality_combo = None
folder_label = None

thumbnail_label = None
title_label = None
duration_label = None
size_label = None
status_label = None
progress_bar = None
percent_label = None
speed_label = None
remaining_label = None

download_button = None
cancel_button = None

home_button = None
history_button = None
settings_button = None
about_button = None


# ============================================================
# LOGO CREATION
# ============================================================

def create_default_logo():
    """
    Creates a clean RockTube logo automatically if no logo
    file exists. This means the app can still display branding
    even before an external logo is supplied.
    """

    if os.path.exists(LOGO_FILE):
        return

    try:
        size = 512

        image = Image.new(
            "RGBA",
            (size, size),
            (8, 8, 8, 255)
        )

        draw = ImageDraw.Draw(image)

        # Outer rounded border
        draw.rounded_rectangle(
            (25, 25, 487, 487),
            radius=95,
            outline=(229, 9, 20, 255),
            width=18
        )

        # RockTube play symbol
        draw.polygon(
            [
                (175, 125),
                (175, 387),
                (395, 256)
            ],
            fill=(229, 9, 20, 255)
        )

        # Inner cutout
        draw.polygon(
            [
                (230, 190),
                (230, 322),
                (338, 256)
            ],
            fill=(8, 8, 8, 255)
        )

        image.save(LOGO_FILE)

    except Exception:
        pass


create_default_logo()


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def format_bytes(size):
    if size is None:
        return "Unknown"

    try:
        size = float(size)
    except Exception:
        return "Unknown"

    if size < 1024:
        return f"{size:.0f} B"

    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"

    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.1f} MB"

    return f"{size / (1024 ** 3):.2f} GB"


def format_time(seconds):
    if seconds is None:
        return "--:--"

    try:
        seconds = int(seconds)
    except Exception:
        return "--:--"

    if seconds < 0:
        return "--:--"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def get_duration_text(seconds):
    if not seconds:
        return "Duration: Unknown"

    return f"Duration: {format_time(seconds)}"


def open_path(path):
    try:
        if not os.path.exists(path):
            messagebox.showwarning(
                "File Not Found",
                "This file no longer exists."
            )
            return

        os.startfile(path)

    except Exception as e:
        messagebox.showerror(
            "Unable to Open",
            str(e)
        )


def open_folder(path):
    try:
        if not os.path.isdir(path):
            os.makedirs(
                path,
                exist_ok=True
            )

        os.startfile(path)

    except Exception as e:
        messagebox.showerror(
            "Unable to Open Folder",
            str(e)
        )


def get_friendly_error(error):
    text = str(error)

    lower = text.lower()

    if "private video" in lower:
        return (
            "This video is private and cannot be downloaded."
        )

    if "video unavailable" in lower:
        return (
            "This video is unavailable or has been removed."
        )

    if "age-restricted" in lower:
        return (
            "This video is age-restricted and cannot be "
            "accessed by RockTube."
        )

    if "sign in" in lower:
        return (
            "This video requires sign-in or authentication."
        )

    if "network" in lower or "connection" in lower:
        return (
            "A network connection problem occurred.\n\n"
            "Please check your internet connection and try again."
        )

    if "unsupported url" in lower:
        return (
            "This URL is not supported."
        )

    return text


# ============================================================
# SIDEBAR
# ============================================================

def set_active_button(active):
    buttons = [
        home_button,
        history_button,
        settings_button,
        about_button
    ]

    for button in buttons:
        if button is not None:
            button.configure(
                fg_color=(
                    RED
                    if button == active
                    else "transparent"
                )
            )


def sidebar_button(parent, text, command):
    button = ctk.CTkButton(
        parent,
        text=text,
        height=46,
        corner_radius=8,
        anchor="w",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        ),
        fg_color="transparent",
        hover_color="#1B1B1B",
        text_color=TEXT,
        command=command
    )

    button.pack(
        fill="x",
        padx=14,
        pady=4
    )

    return button


# ============================================================
# CLEAR CONTENT
# ============================================================

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()


# ============================================================
# HOME
# ============================================================

def show_home():

    global url_entry
    global quality_combo
    global folder_label
    global thumbnail_label
    global title_label
    global duration_label
    global size_label
    global status_label
    global progress_bar
    global percent_label
    global speed_label
    global remaining_label
    global download_button
    global cancel_button

    clear_content()
    set_active_button(home_button)

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    header = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    header.pack(
        fill="x",
        padx=30,
        pady=(25, 10)
    )

    ctk.CTkLabel(
        header,
        text="ROCKTUBE",
        font=ctk.CTkFont(
            size=30,
            weight="bold"
        ),
        text_color=TEXT
    ).pack(anchor="w")

    ctk.CTkLabel(
        header,
        text="Fast. Clean. Powerful.",
        font=ctk.CTkFont(size=14),
        text_color=RED
    ).pack(anchor="w")

    # --------------------------------------------------------
    # URL CARD
    # --------------------------------------------------------

    url_card = ctk.CTkFrame(
        content_frame,
        fg_color=CARD,
        corner_radius=14,
        border_width=1,
        border_color=BORDER
    )

    url_card.pack(
        fill="x",
        padx=30,
        pady=10
    )

    ctk.CTkLabel(
        url_card,
        text="VIDEO URL",
        font=ctk.CTkFont(
            size=12,
            weight="bold"
        ),
        text_color=MUTED
    ).pack(
        anchor="w",
        padx=20,
        pady=(15, 5)
    )

    url_entry = ctk.CTkEntry(
        url_card,
        height=46,
        placeholder_text=(
            "Paste a YouTube video URL here..."
        ),
        font=ctk.CTkFont(size=14),
        fg_color="#0B0B0B",
        border_color="#292929"
    )

    url_entry.pack(
        fill="x",
        padx=20,
        pady=(0, 15)
    )

    analyze_button = ctk.CTkButton(
        url_card,
        text="ANALYZE VIDEO",
        height=42,
        corner_radius=8,
        fg_color=RED,
        hover_color=RED_HOVER,
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        ),
        command=analyze_video
    )

    analyze_button.pack(
        padx=20,
        pady=(0, 20),
        fill="x"
    )

    # --------------------------------------------------------
    # VIDEO INFORMATION
    # --------------------------------------------------------

    info_card = ctk.CTkFrame(
        content_frame,
        fg_color=CARD,
        corner_radius=14,
        border_width=1,
        border_color=BORDER
    )

    info_card.pack(
        fill="x",
        padx=30,
        pady=10
    )

    thumbnail_label = ctk.CTkLabel(
        info_card,
        text="VIDEO\nPREVIEW",
        width=260,
        height=150,
        fg_color="#090909",
        corner_radius=8,
        text_color=MUTED,
        font=ctk.CTkFont(size=13)
    )

    thumbnail_label.pack(
        side="left",
        padx=20,
        pady=20
    )

    details = ctk.CTkFrame(
        info_card,
        fg_color="transparent"
    )

    details.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(5, 20),
        pady=20
    )

    title_label = ctk.CTkLabel(
        details,
        text="No video analyzed",
        font=ctk.CTkFont(
            size=18,
            weight="bold"
        ),
        text_color=TEXT,
        anchor="w",
        justify="left",
        wraplength=650
    )

    title_label.pack(
        fill="x",
        pady=(5, 10)
    )

    duration_label = ctk.CTkLabel(
        details,
        text="Duration: --:--",
        font=ctk.CTkFont(size=13),
        text_color=MUTED,
        anchor="w"
    )

    duration_label.pack(
        fill="x",
        pady=3
    )

    size_label = ctk.CTkLabel(
        details,
        text="Estimated size: Unknown",
        font=ctk.CTkFont(size=13),
        text_color=MUTED,
        anchor="w"
    )

    size_label.pack(
        fill="x",
        pady=3
    )

    # --------------------------------------------------------
    # DOWNLOAD SETTINGS
    # --------------------------------------------------------

    settings_card = ctk.CTkFrame(
        content_frame,
        fg_color=CARD,
        corner_radius=14,
        border_width=1,
        border_color=BORDER
    )

    settings_card.pack(
        fill="x",
        padx=30,
        pady=10
    )

    settings_inner = ctk.CTkFrame(
        settings_card,
        fg_color="transparent"
    )

    settings_inner.pack(
        fill="x",
        padx=20,
        pady=18
    )

    # Quality
    quality_area = ctk.CTkFrame(
        settings_inner,
        fg_color="transparent"
    )

    quality_area.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 10)
    )

    ctk.CTkLabel(
        quality_area,
        text="QUALITY",
        font=ctk.CTkFont(
            size=11,
            weight="bold"
        ),
        text_color=MUTED
    ).pack(anchor="w")

    quality_combo = ctk.CTkComboBox(
        quality_area,
        values=["Best Available"],
        height=40,
        state="readonly",
        command=quality_changed
    )

    saved_quality = settings.get(
        "quality",
        "Best Available"
    )

    quality_combo.set(saved_quality)

    quality_combo.pack(
        fill="x",
        pady=(5, 0)
    )

    # Folder
    folder_area = ctk.CTkFrame(
        settings_inner,
        fg_color="transparent"
    )

    folder_area.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(10, 0)
    )

    ctk.CTkLabel(
        folder_area,
        text="DOWNLOAD FOLDER",
        font=ctk.CTkFont(
            size=11,
            weight="bold"
        ),
        text_color=MUTED
    ).pack(anchor="w")

    folder_row = ctk.CTkFrame(
        folder_area,
        fg_color="transparent"
    )

    folder_row.pack(
        fill="x",
        pady=(5, 0)
    )

    folder_label = ctk.CTkLabel(
        folder_row,
        text=download_folder,
        height=40,
        fg_color="#0B0B0B",
        corner_radius=7,
        text_color=TEXT,
        anchor="w"
    )

    folder_label.pack(
        side="left",
        fill="x",
        expand=True
    )

    ctk.CTkButton(
        folder_row,
        text="Browse",
        width=85,
        height=40,
        command=choose_folder,
        fg_color="#292929",
        hover_color="#383838"
    ).pack(
        side="right",
        padx=(8, 0)
    )

    # --------------------------------------------------------
    # PROGRESS
    # --------------------------------------------------------

    progress_card = ctk.CTkFrame(
        content_frame,
        fg_color=CARD,
        corner_radius=14,
        border_width=1,
        border_color=BORDER
    )

    progress_card.pack(
        fill="x",
        padx=30,
        pady=10
    )

    progress_bar = ctk.CTkProgressBar(
        progress_card,
        height=10,
        corner_radius=5,
        progress_color=RED,
        fg_color="#292929"
    )

    progress_bar.set(0)

    progress_bar.pack(
        fill="x",
        padx=20,
        pady=(20, 10)
    )

    stats_row = ctk.CTkFrame(
        progress_card,
        fg_color="transparent"
    )

    stats_row.pack(
        fill="x",
        padx=20,
        pady=(0, 15)
    )

    percent_label = ctk.CTkLabel(
        stats_row,
        text="0%",
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        ),
        text_color=TEXT
    )

    percent_label.pack(side="left")

    speed_label = ctk.CTkLabel(
        stats_row,
        text="Speed: --",
        text_color=MUTED
    )

    speed_label.pack(
        side="left",
        padx=20
    )

    remaining_label = ctk.CTkLabel(
        stats_row,
        text="Remaining: --:--",
        text_color=MUTED
    )

    remaining_label.pack(
        side="right"
    )

    status_label = ctk.CTkLabel(
        progress_card,
        text="Ready",
        font=ctk.CTkFont(size=12),
        text_color=MUTED
    )

    status_label.pack(
        anchor="w",
        padx=20,
        pady=(0, 15)
    )

    # --------------------------------------------------------
    # BUTTONS
    # --------------------------------------------------------

    buttons = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    buttons.pack(
        fill="x",
        padx=30,
        pady=(5, 30)
    )

    download_button = ctk.CTkButton(
        buttons,
        text="DOWNLOAD VIDEO",
        height=48,
        corner_radius=9,
        fg_color=RED,
        hover_color=RED_HOVER,
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        ),
        command=download_video
    )

    download_button.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(0, 7)
    )

    cancel_button = ctk.CTkButton(
        buttons,
        text="CANCEL",
        height=48,
        width=120,
        corner_radius=9,
        fg_color="#292929",
        hover_color="#3A3A3A",
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        ),
        command=cancel_download,
        state="disabled"
    )

    cancel_button.pack(
        side="right",
        padx=(7, 0)
    )


# ============================================================
# QUALITY
# ============================================================

def quality_changed(choice):
    settings["quality"] = choice
    save_json(
        SETTINGS_FILE,
        settings
    )

    update_estimated_size()


# ============================================================
# ANALYZE VIDEO
# ============================================================

def analyze_video():

    global video_info

    if url_entry is None:
        return

    url = url_entry.get().strip()

    if not url:
        messagebox.showwarning(
            "Missing URL",
            "Please paste a video URL first."
        )
        return

    status_label.configure(
        text="Analyzing video...",
        text_color=RED
    )

    title_label.configure(
        text="Analyzing..."
    )

    size_label.configure(
        text="Estimated size: Calculating..."
    )

    threading.Thread(
        target=analyze_worker,
        args=(url,),
        daemon=True
    ).start()


def analyze_worker(url):

    global video_info

    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True
    }

    try:

        with yt_dlp.YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=False
            )

        video_info = info

        app.after(
            0,
            analysis_success
        )

    except Exception as e:

        error_text = get_friendly_error(e)

        app.after(
            0,
            lambda: analysis_failed(error_text)
        )


def analysis_failed(error):

    status_label.configure(
        text="Analysis failed",
        text_color=RED
    )

    title_label.configure(
        text="Unable to analyze this video"
    )

    size_label.configure(
        text="Estimated size: Unknown"
    )

    messagebox.showerror(
        "Analysis Error",
        error
    )


def analysis_success():

    if not video_info:
        return

    title = video_info.get(
        "title",
        "Unknown title"
    )

    duration = video_info.get(
        "duration"
    )

    title_label.configure(
        text=title
    )

    duration_label.configure(
        text=get_duration_text(duration)
    )

    status_label.configure(
        text="Video analyzed successfully",
        text_color=GREEN
    )

    # --------------------------------------------------------
    # Quality options
    # --------------------------------------------------------

    heights = set()

    for fmt in video_info.get("formats", []):
        height = fmt.get("height")
        video_codec = fmt.get("vcodec")

        # Ignore audio-only and DRM-protected formats.
        if (
            height
            and video_codec not in (None, "none")
            and not fmt.get("has_drm")
        ):
            try:
                heights.add(int(height))
            except (TypeError, ValueError):
                pass

    quality_values = [
        "Best Available"
    ]

    sorted_heights = sorted(
        heights,
        reverse=True
    )

    for height in sorted_heights:

        quality_values.append(
            f"{height}p"
        )

    quality_combo.configure(
        values=quality_values
    )

    saved_quality = settings.get(
        "quality",
        "Best Available"
    )

    if saved_quality in quality_values:

        quality_combo.set(
            saved_quality
        )

    else:

        quality_combo.set(
            "Best Available"
        )

    # --------------------------------------------------------
    # Thumbnail
    # --------------------------------------------------------

    thumbnail_url = video_info.get(
        "thumbnail"
    )

    if thumbnail_url:

        threading.Thread(
            target=load_thumbnail,
            args=(thumbnail_url,),
            daemon=True
        ).start()

    update_estimated_size()


# ============================================================
# THUMBNAIL
# ============================================================

def load_thumbnail(url):

    global thumbnail_image

    try:

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:

            data = response.read()

        image = Image.open(
            BytesIO(data)
        ).convert("RGB")

        image.thumbnail(
            (260, 150)
        )

        thumbnail_image = ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=image.size
        )

        app.after(
            0,
            lambda: thumbnail_label.configure(
                image=thumbnail_image,
                text=""
            )
        )

    except Exception:
        pass


# ============================================================
# ESTIMATED SIZE
# ============================================================

def get_selected_height():

    if quality_combo is None:
        return None

    selected = quality_combo.get()

    if selected == "Best Available":
        return None

    try:
        return int(
            selected.replace(
                "p",
                ""
            )
        )

    except Exception:
        return None


def calculate_estimated_size():

    if not video_info:
        return None

    selected_height = get_selected_height()

    formats = video_info.get(
        "formats",
        []
    )

    candidates = []

    for fmt in formats:

        height = fmt.get(
            "height"
        )

        filesize = (
            fmt.get("filesize")
            or fmt.get("filesize_approx")
        )

        if not filesize:
            continue

        if selected_height:

            if (
                height
                and height <= selected_height
            ):

                candidates.append(
                    (
                        height,
                        filesize
                    )
                )

        else:

            candidates.append(
                (
                    height or 0,
                    filesize
                )
            )

    if not candidates:
        return None

    if selected_height:

        candidates.sort(
            key=lambda x: x[0],
            reverse=True
        )

        return candidates[0][1]

    candidates.sort(
        key=lambda x: x[1],
        reverse=True
    )

    return candidates[0][1]


def update_estimated_size():

    if not video_info:
        return

    size = calculate_estimated_size()

    if size:

        size_label.configure(
            text=(
                "Estimated size: "
                f"{format_bytes(size)}"
            )
        )

    else:

        size_label.configure(
            text="Estimated size: Unknown"
        )


# ============================================================
# FOLDER
# ============================================================

def choose_folder():

    global download_folder

    folder = filedialog.askdirectory(
        initialdir=download_folder
    )

    if folder:

        download_folder = folder

        settings["download_folder"] = folder

        save_json(
            SETTINGS_FILE,
            settings
        )

        if folder_label:
            folder_label.configure(
                text=folder
            )


# ============================================================
# DOWNLOAD PROGRESS
# ============================================================

def progress_hook(data):

    if download_cancelled:

        raise yt_dlp.utils.DownloadCancelled(
            "Download cancelled by user"
        )

    if data["status"] == "downloading":

        downloaded = data.get(
            "downloaded_bytes",
            0
        )

        total = (
            data.get("total_bytes")
            or data.get("total_bytes_estimate")
            or 0
        )

        speed = data.get(
            "speed"
        )

        eta = data.get(
            "eta"
        )

        if total:
            percent = downloaded / total
        else:
            percent = 0

        app.after(
            0,
            lambda: update_progress(
                percent,
                downloaded,
                total,
                speed,
                eta
            )
        )

    elif data["status"] == "finished":

        app.after(
            0,
            lambda: update_progress(
                1,
                data.get(
                    "downloaded_bytes",
                    0
                ),
                data.get(
                    "total_bytes",
                    0
                ),
                None,
                0
            )
        )


def update_progress(
    percent,
    downloaded,
    total,
    speed,
    eta
):

    if progress_bar is None:
        return

    progress_bar.set(
        max(
            0,
            min(
                1,
                percent
            )
        )
    )

    percent_label.configure(
        text=f"{percent * 100:.1f}%"
    )

    if total:

        status_label.configure(
            text=(
                f"{format_bytes(downloaded)} / "
                f"{format_bytes(total)}"
            )
        )

    if speed:

        speed_label.configure(
            text=(
                f"Speed: "
                f"{format_bytes(speed)}/s"
            )
        )

    else:

        speed_label.configure(
            text="Speed: --"
        )

    remaining_label.configure(
        text=(
            f"Remaining: "
            f"{format_time(eta)}"
        )
    )


# ============================================================
# DOWNLOAD
# ============================================================

def download_video():

    global download_running
    global download_cancelled

    if download_running:
        return

    if not video_info:

        messagebox.showwarning(
            "No Video",
            "Please analyze a video first."
        )

        return

    if not os.path.isdir(
        download_folder
    ):

        try:

            os.makedirs(
                download_folder,
                exist_ok=True
            )

        except Exception as e:

            messagebox.showerror(
                "Folder Error",
                str(e)
            )

            return

    download_cancelled = False
    download_running = True

    download_button.configure(
        state="disabled"
    )

    cancel_button.configure(
        state="normal"
    )

    status_label.configure(
        text="Starting download...",
        text_color=RED
    )

    progress_bar.set(0)

    percent_label.configure(
        text="0%"
    )

    speed_label.configure(
        text="Speed: --"
    )

    remaining_label.configure(
        text="Remaining: --:--"
    )

    quality = quality_combo.get()

    settings["quality"] = quality

    save_json(
        SETTINGS_FILE,
        settings
    )

    threading.Thread(
        target=download_worker,
        args=(quality,),
        daemon=True
    ).start()


def download_worker(quality):

    global current_ydl
    global download_running

    url = video_info.get(
        "webpage_url"
    )

    if not url:

        url = video_info.get(
            "original_url"
        )

    output_template = os.path.join(
        download_folder,
        "%(title)s.%(ext)s"
    )

    # --------------------------------------------------------
    # Format selection: prefer device-compatible H.264/AAC MP4.
    # No video re-encoding is performed. If compatible video/audio streams
    # are separate, FFmpeg only muxes them into MP4.
    # Fall back to MP4, then the source's best format, if H.264/AAC is absent.
    try:
        height = (
            720
            if quality == "Best Available"
            else int(quality.replace("p", ""))
        )
    except (TypeError, ValueError, AttributeError):
        height = 720

    height = max(144, min(height, 2160))

    format_string = (
        f"best[ext=mp4][vcodec^=avc1][acodec^=mp4a][height<={height}]/"
        "best[ext=mp4][vcodec^=avc1][acodec^=mp4a]/"
        f"bestvideo[ext=mp4][vcodec^=avc1][height<={height}]"
        "+bestaudio[ext=m4a][acodec^=mp4a]/"
        "bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a][acodec^=mp4a]/"
        f"best[ext=mp4][height<={height}]/best[ext=mp4]/best"
    )

    options = {
        "format": format_string,
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [
            progress_hook
        ],
        "windowsfilenames": True
    }

    if os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg.exe")):
        options["ffmpeg_location"] = FFMPEG_DIR

    try:

        with yt_dlp.YoutubeDL(
            options
        ) as ydl:

            current_ydl = ydl

            info = ydl.extract_info(
                url,
                download=True
            )

            prepared_path = ydl.prepare_filename(info)

        # Find the actual output file after any format merging.
        base_path = os.path.splitext(prepared_path)[0]
        candidates = [base_path + ".mp4", info.get("_filename")]

        for requested in info.get("requested_downloads", []) or []:
            if isinstance(requested, dict):
                candidates.extend([
                    requested.get("filepath"),
                    requested.get("filename"),
                ])

        candidates.append(prepared_path)

        final_path = next(
            (
                os.path.abspath(path)
                for path in candidates
                if path and os.path.isfile(path)
            ),
            prepared_path
        )
        app.after(
            0,
            lambda: download_success(
                info,
                final_path,
                quality
            )
        )

    except Exception as e:

        error_text = get_friendly_error(e)

        if (
            "cancel" in str(e).lower()
            or download_cancelled
        ):

            app.after(
                0,
                download_cancelled_ui
            )

        else:

            app.after(
                0,
                lambda: download_failed(
                    error_text
                )
            )

    finally:

        current_ydl = None
        download_running = False


# ============================================================
# CANCEL
# ============================================================

def cancel_download():

    global download_cancelled

    if not download_running:
        return

    download_cancelled = True

    status_label.configure(
        text="Cancelling...",
        text_color=RED
    )

    cancel_button.configure(
        state="disabled"
    )


def download_cancelled_ui():

    global download_running

    download_running = False

    download_button.configure(
        state="normal"
    )

    cancel_button.configure(
        state="disabled"
    )

    status_label.configure(
        text="Download cancelled",
        text_color=MUTED
    )


# ============================================================
# DOWNLOAD SUCCESS
# ============================================================

def download_success(
    info,
    final_path,
    quality
):

    global download_running

    download_running = False

    progress_bar.set(1)

    percent_label.configure(
        text="100%"
    )

    speed_label.configure(
        text="Complete"
    )

    remaining_label.configure(
        text="Remaining: 00:00"
    )

    status_label.configure(
        text="Download completed successfully",
        text_color=GREEN
    )

    download_button.configure(
        state="normal"
    )

    cancel_button.configure(
        state="disabled"
    )

    # --------------------------------------------------------
    # History
    # --------------------------------------------------------

    title = info.get(
        "title",
        "Unknown title"
    )

    file_size = None

    try:

        if os.path.exists(
            final_path
        ):

            file_size = os.path.getsize(
                final_path
            )

    except Exception:
        pass

    history_item = {
        "title": title,
        "url": info.get(
            "webpage_url",
            info.get(
                "original_url",
                ""
            )
        ),
        "path": final_path,
        "quality": quality,
        "size": file_size,
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    history.insert(
        0,
        history_item
    )

    del history[100:]

    save_json(
        HISTORY_FILE,
        history
    )

    # --------------------------------------------------------
    # Completion dialog
    # --------------------------------------------------------

    result = messagebox.askyesno(
        "Download Complete",
        (
            f"{title}\n\n"
            "Your video has been downloaded "
            "successfully.\n\n"
            "Open the downloaded file?"
        )
    )

    if result:

        open_path(
            final_path
        )

    else:

        folder_result = messagebox.askyesno(
            "Download Complete",
            "Would you like to open the download folder?"
        )

        if folder_result:

            open_folder(
                download_folder
            )


# ============================================================
# DOWNLOAD FAILED
# ============================================================

def download_failed(error):

    global download_running

    download_running = False

    download_button.configure(
        state="normal"
    )

    cancel_button.configure(
        state="disabled"
    )

    status_label.configure(
        text="Download failed",
        text_color=RED
    )

    messagebox.showerror(
        "Download Error",
        error
    )


# ============================================================
# HISTORY
# ============================================================

def show_history():

    clear_content()
    set_active_button(history_button)

    header = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    header.pack(
        fill="x",
        padx=30,
        pady=(25, 10)
    )

    ctk.CTkLabel(
        header,
        text="DOWNLOAD HISTORY",
        font=ctk.CTkFont(
            size=28,
            weight="bold"
        ),
        text_color=TEXT
    ).pack(
        side="left"
    )

    ctk.CTkButton(
        header,
        text="Clear History",
        width=120,
        height=38,
        fg_color="#292929",
        hover_color=RED,
        command=clear_history
    ).pack(
        side="right"
    )

    scroll = ctk.CTkScrollableFrame(
        content_frame,
        fg_color="transparent"
    )

    scroll.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=10
    )

    if not history:

        empty = ctk.CTkFrame(
            scroll,
            fg_color=CARD,
            corner_radius=14
        )

        empty.pack(
            fill="x",
            pady=10
        )

        ctk.CTkLabel(
            empty,
            text="No downloads yet.",
            font=ctk.CTkFont(
                size=17,
                weight="bold"
            ),
            text_color=TEXT
        ).pack(
            pady=(30, 5)
        )

        ctk.CTkLabel(
            empty,
            text=(
                "Your completed downloads "
                "will appear here."
            ),
            text_color=MUTED
        ).pack(
            pady=(0, 30)
        )

        return

    for item in history:

        row = ctk.CTkFrame(
            scroll,
            fg_color=CARD,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )

        row.pack(
            fill="x",
            pady=6
        )

        left = ctk.CTkFrame(
            row,
            fg_color="transparent"
        )

        left.pack(
            side="left",
            fill="x",
            expand=True,
            padx=18,
            pady=15
        )

        title = item.get(
            "title",
            "Unknown"
        )

        ctk.CTkLabel(
            left,
            text=title,
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            ),
            text_color=TEXT,
            anchor="w",
            justify="left",
            wraplength=600
        ).pack(
            fill="x"
        )

        date = item.get(
            "date",
            "Unknown date"
        )

        quality = item.get(
            "quality",
            "Unknown"
        )

        size = item.get(
            "size"
        )

        size_text = format_bytes(
            size
        )

        ctk.CTkLabel(
            left,
            text=(
                f"{date}  •  "
                f"{quality}  •  "
                f"{size_text}"
            ),
            font=ctk.CTkFont(
                size=11
            ),
            text_color=MUTED,
            anchor="w"
        ).pack(
            fill="x",
            pady=(5, 0)
        )

        path = item.get(
            "path",
            ""
        )

        if os.path.exists(path):

            ctk.CTkButton(
                row,
                text="OPEN",
                width=90,
                height=36,
                fg_color=RED,
                hover_color=RED_HOVER,
                command=lambda p=path: open_path(p)
            ).pack(
                side="right",
                padx=(5, 18)
            )

        else:

            ctk.CTkLabel(
                row,
                text="FILE MISSING",
                text_color="#777777",
                font=ctk.CTkFont(
                    size=10
                )
            ).pack(
                side="right",
                padx=18
            )


def clear_history():

    global history

    if not history:
        return

    result = messagebox.askyesno(
        "Clear History",
        (
            "Are you sure you want to "
            "clear your download history?"
        )
    )

    if not result:
        return

    history = []

    save_json(
        HISTORY_FILE,
        history
    )

    show_history()


# ============================================================
# SETTINGS
# ============================================================

def show_settings():

    clear_content()
    set_active_button(settings_button)

    ctk.CTkLabel(
        content_frame,
        text="SETTINGS",
        font=ctk.CTkFont(
            size=28,
            weight="bold"
        ),
        text_color=TEXT
    ).pack(
        anchor="w",
        padx=30,
        pady=(25, 20)
    )

    card = ctk.CTkFrame(
        content_frame,
        fg_color=CARD,
        corner_radius=14,
        border_width=1,
        border_color=BORDER
    )

    card.pack(
        fill="x",
        padx=30,
        pady=10
    )

    ctk.CTkLabel(
        card,
        text="GENERAL",
        font=ctk.CTkFont(
            size=14,
            weight="bold"
        ),
        text_color=RED
    ).pack(
        anchor="w",
        padx=20,
        pady=(20, 15)
    )

    # --------------------------------------------------------
    # Download folder
    # --------------------------------------------------------

    ctk.CTkLabel(
        card,
        text="Default download folder",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        )
    ).pack(
        anchor="w",
        padx=20
    )

    folder_row = ctk.CTkFrame(
        card,
        fg_color="transparent"
    )

    folder_row.pack(
        fill="x",
        padx=20,
        pady=(7, 20)
    )

    settings_folder_label = ctk.CTkLabel(
        folder_row,
        text=download_folder,
        height=42,
        fg_color="#0B0B0B",
        corner_radius=8,
        anchor="w"
    )

    settings_folder_label.pack(
        side="left",
        fill="x",
        expand=True
    )

    def settings_choose_folder():

        global download_folder

        folder = filedialog.askdirectory(
            initialdir=download_folder
        )

        if folder:

            download_folder = folder

            settings["download_folder"] = folder

            save_json(
                SETTINGS_FILE,
                settings
            )

            settings_folder_label.configure(
                text=folder
            )

            if folder_label is not None:

                folder_label.configure(
                    text=folder
                )

    ctk.CTkButton(
        folder_row,
        text="Browse",
        width=90,
        height=42,
        fg_color="#292929",
        hover_color="#3A3A3A",
        command=settings_choose_folder
    ).pack(
        side="right",
        padx=(10, 0)
    )

    # --------------------------------------------------------
    # Appearance
    # --------------------------------------------------------

    ctk.CTkLabel(
        card,
        text="Appearance",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        )
    ).pack(
        anchor="w",
        padx=20,
        pady=(0, 7)
    )

    theme_combo = ctk.CTkComboBox(
        card,
        values=[
            "Dark",
            "Light",
            "System"
        ],
        state="readonly",
        height=42
    )

    theme_combo.set(
        settings.get(
            "theme",
            "Dark"
        )
    )

    theme_combo.pack(
        fill="x",
        padx=20,
        pady=(0, 20)
    )

    # --------------------------------------------------------
    # Default quality
    # --------------------------------------------------------

    ctk.CTkLabel(
        card,
        text="Default video quality",
        text_color=TEXT,
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        )
    ).pack(
        anchor="w",
        padx=20,
        pady=(0, 7)
    )

    settings_quality_combo = ctk.CTkComboBox(
        card,
        values=[
            "Best Available",
            "2160p",
            "1440p",
            "1080p",
            "720p",
            "480p",
            "360p"
        ],
        state="readonly",
        height=42
    )

    settings_quality_combo.set(
        settings.get(
            "quality",
            "Best Available"
        )
    )

    settings_quality_combo.pack(
        fill="x",
        padx=20,
        pady=(0, 20)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save_settings():

        selected_theme = theme_combo.get()

        selected_quality = (
            settings_quality_combo.get()
        )

        settings["theme"] = selected_theme
        settings["download_folder"] = download_folder
        settings["quality"] = selected_quality

        save_json(
            SETTINGS_FILE,
            settings
        )

        ctk.set_appearance_mode(
            selected_theme
        )

        if folder_label is not None:

            folder_label.configure(
                text=download_folder
            )

        messagebox.showinfo(
            "Settings Saved",
            "Your settings have been saved successfully."
        )

    ctk.CTkButton(
        card,
        text="SAVE SETTINGS",
        height=45,
        fg_color=RED,
        hover_color=RED_HOVER,
        font=ctk.CTkFont(
            size=13,
            weight="bold"
        ),
        command=save_settings
    ).pack(
        fill="x",
        padx=20,
        pady=(0, 20)
    )


# ============================================================
# ABOUT
# ============================================================

def show_about():

    global about_logo_image

    clear_content()
    set_active_button(about_button)

    container = ctk.CTkFrame(
        content_frame,
        fg_color="transparent"
    )

    container.pack(
        fill="both",
        expand=True
    )

    # --------------------------------------------------------
    # Logo
    # --------------------------------------------------------

    try:

        if os.path.exists(
            LOGO_FILE
        ):

            logo = Image.open(
                LOGO_FILE
            ).convert("RGBA")

            about_logo_image = ctk.CTkImage(
                light_image=logo,
                dark_image=logo,
                size=(120, 120)
            )

            ctk.CTkLabel(
                container,
                image=about_logo_image,
                text=""
            ).pack(
                pady=(50, 15)
            )

    except Exception:
        pass

    ctk.CTkLabel(
        container,
        text="ROCKTUBE",
        font=ctk.CTkFont(
            size=38,
            weight="bold"
        ),
        text_color=RED
    ).pack(
        pady=(0, 3)
    )

    ctk.CTkLabel(
        container,
        text="Downloader",
        font=ctk.CTkFont(
            size=21,
            weight="bold"
        ),
        text_color=TEXT
    ).pack()

    ctk.CTkLabel(
        container,
        text=f"Version {APP_VERSION}",
        text_color=MUTED,
        font=ctk.CTkFont(
            size=13
        )
    ).pack(
        pady=(10, 30)
    )

    ctk.CTkLabel(
        container,
        text=(
            "A clean and powerful desktop video downloader.\n\n"
            "Fast. Clean. Powerful.\n\n"
            f"Built by {DEVELOPER}"
        ),
        text_color=TEXT,
        justify="center",
        font=ctk.CTkFont(
            size=14
        )
    ).pack(
        pady=5
    )

    ctk.CTkLabel(
        container,
        text="© 2026 RockTube Downloader",
        text_color="#555555",
        font=ctk.CTkFont(
            size=11
        )
    ).pack(
        pady=(25, 0)
    )


# ============================================================
# MAIN APPLICATION
# ============================================================

def create_app():

    global app
    global content_frame
    global home_button
    global history_button
    global settings_button
    global about_button
    global app_icon_image

    app = ctk.CTk()

    app.title(
        f"{APP_NAME} {APP_VERSION}"
    )

    app.geometry(
        "1180x780"
    )

    app.minsize(
        950,
        650
    )

    app.configure(
        fg_color=BG
    )

    # --------------------------------------------------------
    # Window icon
    # --------------------------------------------------------

    try:

        if os.path.exists(
            ICON_FILE
        ):

            app.iconbitmap(
                ICON_FILE
            )

        elif os.path.exists(
            LOGO_FILE
        ):

            icon_image = Image.open(
                LOGO_FILE
            ).convert("RGBA")

            app_icon_image = ctk.CTkImage(
                light_image=icon_image,
                dark_image=icon_image,
                size=(32, 32)
            )

            app.iconphoto(
                False,
                icon_image
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # Sidebar
    # --------------------------------------------------------

    sidebar = ctk.CTkFrame(
        app,
        width=210,
        corner_radius=0,
        fg_color=SIDEBAR
    )

    sidebar.pack(
        side="left",
        fill="y"
    )

    sidebar.pack_propagate(False)

    # --------------------------------------------------------
    # Sidebar logo
    # --------------------------------------------------------

    logo = ctk.CTkFrame(
        sidebar,
        fg_color="transparent"
    )

    logo.pack(
        fill="x",
        padx=18,
        pady=(20, 25)
    )

    try:

        if os.path.exists(
            LOGO_FILE
        ):

            logo_image = Image.open(
                LOGO_FILE
            ).convert("RGBA")

            sidebar_logo_image = ctk.CTkImage(
                light_image=logo_image,
                dark_image=logo_image,
                size=(58, 58)
            )

            ctk.CTkLabel(
                logo,
                image=sidebar_logo_image,
                text=""
            ).pack(
                anchor="w",
                pady=(0, 8)
            )

    except Exception:
        pass

    ctk.CTkLabel(
        logo,
        text="ROCKTUBE",
        font=ctk.CTkFont(
            size=23,
            weight="bold"
        ),
        text_color=RED
    ).pack(
        anchor="w"
    )

    ctk.CTkLabel(
        logo,
        text=f"v{APP_VERSION}",
        font=ctk.CTkFont(
            size=10
        ),
        text_color=MUTED
    ).pack(
        anchor="w",
        pady=(3, 0)
    )

    # --------------------------------------------------------
    # Navigation
    # --------------------------------------------------------

    home_button = sidebar_button(
        sidebar,
        "⌂   HOME",
        show_home
    )

    history_button = sidebar_button(
        sidebar,
        "▣   HISTORY",
        show_history
    )

    settings_button = sidebar_button(
        sidebar,
        "⚙   SETTINGS",
        show_settings
    )

    about_button = sidebar_button(
        sidebar,
        "ⓘ   ABOUT",
        show_about
    )

    # --------------------------------------------------------
    # Bottom branding
    # --------------------------------------------------------

    ctk.CTkLabel(
        sidebar,
        text=(
            "ROCKTUBE DOWNLOADER\n"
            "Built by Mr.Sulim.Inc"
        ),
        font=ctk.CTkFont(
            size=9
        ),
        text_color="#555555",
        justify="center"
    ).pack(
        side="bottom",
        pady=18
    )

    # --------------------------------------------------------
    # Main content
    # --------------------------------------------------------

    content_frame = ctk.CTkScrollableFrame(
        app,
        fg_color=BG,
        corner_radius=0
    )

    content_frame.pack(
        side="left",
        fill="both",
        expand=True
    )

    show_home()

    # --------------------------------------------------------
    # Start
    # --------------------------------------------------------

    app.mainloop()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    create_app()