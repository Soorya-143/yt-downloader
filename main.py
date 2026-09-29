import flet as ft
import yt_dlp
import os
import json
import threading
import random
import time
from datetime import datetime

# Storage for history
HISTORY_FILE = "download_history.json"

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
    except: pass
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[-20:], f, indent=2)
    except: pass

def main(page: ft.Page):
    page.title = "YT Downloader - ULTIMATE"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#0A0A14"
    page.padding = 0
    page.window_width = 440
    page.window_height = 900
    page.scroll = ft.ScrollMode.AUTO

    history = load_history()
    selected_quality = "Best Quality"
    is_dark = True
    thumb_url = None

    # Refs
    url_field = ft.Ref[ft.TextField]()
    title_text = ft.Ref[ft.Text]()
    channel_text = ft.Ref[ft.Text]()
    progress_bar = ft.Ref[ft.ProgressBar]()
    percent_text = ft.Ref[ft.Text]()
    status_text = ft.Ref[ft.Text]()
    speed_text = ft.Ref[ft.Text]()
    download_btn = ft.Ref[ft.ElevatedButton]()
    thumb_image = ft.Ref[ft.Image]()
    thumb_container = ft.Ref[ft.Container]()
    history_col = ft.Ref[ft.Column]()
    theme_btn = ft.Ref[ft.IconButton]()

    # Colors
    NEON = ["#FF006A", "#7B00FF", "#00F0FF", "#00FF88", "#FFD700"]

    def get_format(q):
        if q == "1080p": return "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best"
        if q == "720p": return "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best"
        if q == "480p": return "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best"
        if q == "Audio Only (mp3)": return "bestaudio/best"
        return "bestvideo+bestaudio/best"

    def select_quality(e):
        nonlocal selected_quality
        selected_quality = e.control.data
        # Update all quality buttons
        for btn in quality_buttons:
            if btn.data == selected_quality:
                btn.bgcolor = btn.data_color
                btn.style = ft.ButtonStyle(
                    side=ft.BorderSide(2.5, ft.Colors.WHITE),
                    shape=ft.RoundedRectangleBorder(radius=20)
                )
            else:
                btn.bgcolor = "#1E1E3A"
                btn.style = ft.ButtonStyle(
                    side=ft.BorderSide(0, ft.Colors.TRANSPARENT),
                    shape=ft.RoundedRectangleBorder(radius=20)
                )
        page.update()

    def toggle_theme(e):
        nonlocal is_dark
        is_dark = not is_dark
        page.theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.bgcolor = "#0A0A14" if is_dark else "#F5F5FF"
        theme_btn.current.icon = ft.Icons.DARK_MODE if is_dark else ft.Icons.LIGHT_MODE
        status_text.current.value = "🌙 Dark Neon" if is_dark else "☀️ Light Pastel"
        page.update()

    def refresh_history():
        history_col.current.controls.clear()
        if not history:
            history_col.current.controls.append(
                ft.Text("No downloads yet 📭", size=11, color="#666688", text_align=ft.TextAlign.CENTER)
            )
        else:
            for entry in reversed(history[-5:]):
                card = ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=ft.Column([
                                ft.Text(entry["title"][:45], size=12, weight=ft.FontWeight.BOLD, color="white" if is_dark else "black", max_lines=2),
                                ft.Text(f"{entry['time']} • {entry['quality']}", size=10, color="#8888AA")
                            ], spacing=2),
                            expand=True
                        ),
                        ft.Container(width=10, height=10, bgcolor=entry["color"], border_radius=10)
                    ]),
                    bgcolor="#1E1E3A" if is_dark else "#EDEEFF",
                    border=ft.border.all(1, entry["color"]),
                    border_radius=12,
                    padding=10,
                    margin=ft.margin.only(bottom=6)
                )
                history_col.current.controls.append(card)
        page.update()

    def show_confetti():
        # Simple confetti dialog
        confetti_icons = ["🎉", "🎊", "✨", "💜", "🔥", "🌈", "⭐"]
        page.overlay.append(
            ft.Container(
                content=ft.Column([
                    ft.Text(" ".join([random.choice(confetti_icons) for _ in range(12)]), size=30, text_align=ft.TextAlign.CENTER),
                    ft.Text("BOOM! Completed! 🎉", size=22, weight=ft.FontWeight.BOLD, color="#00FF88", text_align=ft.TextAlign.CENTER),
                    ft.Text("File saved to Videos/", size=12, color="#8888AA", text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton("Awesome! 🎊", bgcolor="#00FF88", color="black",
                                      on_click=lambda e: close_confetti())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
                bgcolor="#1A1A2E",
                border=ft.border.all(3, "#00FF88"),
                border_radius=20,
                padding=20,
                alignment=ft.alignment.center,
                width=360,
                height=200
            )
        )
        page.update()

    def close_confetti():
        if page.overlay:
            page.overlay.clear()
            page.update()

    def on_progress(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = downloaded / total if total else 0
            progress_bar.current.value = percent
            percent_text.current.value = f"{int(percent*100)}%"
            speed_text.current.value = f"🚀 {d.get('_speed_str','')} • ⏳ {d.get('_eta_str','')}"
            status_text.current.value = f"⚡ Downloading {int(percent*100)}%"
            # Rainbow progress color
            progress_bar.current.color = random.choice(NEON)
            page.update()

    def fetch_preview(e):
        url = url_field.current.value.strip()
        if not url:
            status_text.current.value = "⚠️ Paste a link first!"
            status_text.current.color = "#FF5252"
            page.update()
            return
        
        status_text.current.value = "🔍 Fetching preview..."
        status_text.current.color = "#00F0FF"
        download_btn.current.disabled = True
        download_btn.current.text = "Fetching..."
        page.update()

        def thread():
            try:
                ydl_opts = {"quiet": True, "noplaylist": True, "skip_download": True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    title = info.get('title', 'Unknown')
                    channel = info.get('uploader', 'Unknown')
                    dur = info.get('duration', 0)
                    dur_str = f"{dur//60}:{dur%60:02d}" if dur else "--:--"
                    thumb = info.get('thumbnail')
                    
                    title_text.current.value = f"🎬 {title[:70]}"
                    channel_text.current.value = f"👤 {channel} • ⏱️ {dur_str} • 👀 {info.get('view_count','?')} views"
                    
                    if thumb:
                        thumb_image.current.src = thumb
                        thumb_image.current.visible = True
                        thumb_container.current.bgcolor = "#000000"
                    
                    status_text.current.value = "✅ Preview loaded! Pick quality"
                    status_text.current.color = "#00FF88"
            except Exception as ex:
                title_text.current.value = f"❌ {str(ex)[:60]}"
                status_text.current.value = f"❌ Failed: {str(ex)[:50]}"
                status_text.current.color = "#FF5252"
            finally:
                download_btn.current.disabled = False
                download_btn.current.text = "🚀 DOWNLOAD NOW 🚀"
                page.update()
        
        threading.Thread(target=thread, daemon=True).start()

    def download_thread():
        url = url_field.current.value.strip()
        if not url:
            status_text.current.value = "⚠️ Enter a YouTube link"
            status_text.current.color = "#FF5252"
            page.update()
            return

        os.makedirs("Videos", exist_ok=True)
        download_btn.current.disabled = True
        download_btn.current.text = "⏳ DOWNLOADING..."
        status_text.current.value = "🔍 Starting..."
        progress_bar.current.value = 0.1
        percent_text.current.value = "5%"
        page.update()

        is_audio = selected_quality == "Audio Only (mp3)"
        opts = {
            "format": get_format(selected_quality),
            "merge_output_format": "mp4" if not is_audio else "mp3",
            "outtmpl": "Videos/%(title)s.%(ext)s",
            "restrictfilenames": True,
            "progress_hooks": [on_progress],
            "noplaylist": True,
        }
        if is_audio:
            opts["postprocessors"] = [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                real_title = info.get('title','Video')
                title_text.current.value = f"🎬 {real_title[:70]}"
                page.update()
                ydl.download([url])

            status_text.current.value = "✅ BOOM! Completed! 🎉"
            status_text.current.color = "#00FF88"
            percent_text.current.value = "100%"
            progress_bar.current.value = 1
            progress_bar.current.color = "#00FF88"
            
            # Add to history
            entry = {
                "title": real_title[:50],
                "quality": selected_quality,
                "time": datetime.now().strftime("%I:%M %p • %d %b"),
                "color": random.choice(NEON)
            }
            history.append(entry)
            save_history(history)
            refresh_history()
            
            # Confetti!
            page.update()
            show_confetti()
            
        except Exception as ex:
            status_text.current.value = f"❌ {str(ex)[:50]}"
            status_text.current.color = "#FF5252"
            progress_bar.current.value = 0
        finally:
            download_btn.current.disabled = False
            download_btn.current.text = "🚀 DOWNLOAD NOW 🚀"
            page.update()

    def start_download(e):
        threading.Thread(target=download_thread, daemon=True).start()

    # Quality buttons list
    qualities = [
        ("🌈 Best", "Best Quality", "#7B00FF"),
        ("💎 1080p", "1080p", "#0066FF"),
        ("🔥 720p", "720p", "#FF6A00"),
        ("⚡ 480p", "480p", "#00FF88"),
        ("🎵 MP3", "Audio Only (mp3)", "#FF00AA"),
    ]
    
    quality_buttons = []
    for label, value, color in qualities:
        btn = ft.ElevatedButton(
            text=label,
            data=value,
            data_color=color,
            bgcolor=color if value == selected_quality else "#1E1E3A",
            color="white",
            style=ft.ButtonStyle(
                side=ft.BorderSide(2.5, ft.Colors.WHITE) if value==selected_quality else ft.BorderSide(0, ft.Colors.TRANSPARENT),
                shape=ft.RoundedRectangleBorder(radius=20),
                padding=ft.padding.symmetric(horizontal=8, vertical=10)
            ),
            on_click=select_quality,
            expand=True
        )
        quality_buttons.append(btn)

    # ===== UI BUILD =====
    page.add(
        ft.Column([
            # Header
            ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Text("●", size=28, color="#FF006A", weight=ft.FontWeight.BOLD),
                        ft.Text("●", size=28, color="#7B00FF", weight=ft.FontWeight.BOLD),
                        ft.Text("●", size=28, color="#00F0FF", weight=ft.FontWeight.BOLD),
                        ft.Column([
                            ft.Text("YT DOWNLOADER", size=18, weight=ft.FontWeight.BOLD, color="white"),
                            ft.Text("ULTIMATE • ANDROID READY", size=10, weight=ft.FontWeight.BOLD, color="#00F0FF")
                        ], spacing=0)
                    ], spacing=8),
                    ft.IconButton(ref=theme_btn, icon=ft.Icons.DARK_MODE, icon_color="#FFD700", bgcolor="#222244",
                                  on_click=toggle_theme, icon_size=20)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor="#111122",
                padding=ft.padding.symmetric(horizontal=16, vertical=14)
            ),
            
            # URL Card
            ft.Container(
                content=ft.Column([
                    ft.Text("🔗 DROP YOUR LINK HERE", size=12, weight=ft.FontWeight.BOLD, color="#00F0FF"),
                    ft.Row([
                        ft.TextField(ref=url_field, hint_text="https://youtu.be/... or shorts/...",
                                     border_radius=12, filled=True, fill_color="#0E0E20",
                                     border_color="#2A2A5A", expand=True, height=50,
                                     text_size=13, color="white", hint_style=ft.TextStyle(color="#555588")),
                        ft.IconButton(icon=ft.Icons.SEARCH, bgcolor="#7B00FF", icon_color="white",
                                      width=50, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                                      on_click=fetch_preview)
                    ], spacing=8)
                ], spacing=8),
                bgcolor="#16162A",
                border=ft.border.all(1.5, "#7B00FF"),
                border_radius=20,
                padding=16,
                margin=ft.margin.all(12)
            ),

            # Preview Card - REAL THUMBNAIL
            ft.Container(
                content=ft.Column([
                    ft.Container(ref=thumb_container,
                        content=ft.Stack([
                            ft.Image(ref=thumb_image, src="", width=400, height=200, fit=ft.ImageFit.COVER, border_radius=16, visible=False),
                            ft.Container(content=ft.Text("🎬\nPaste link & hit 🔍", size=14, weight=ft.FontWeight.BOLD, color="#555588", text_align=ft.TextAlign.CENTER),
                                         alignment=ft.alignment.center, width=400, height=200) if not thumb_image.current or not thumb_image.current.visible else ft.Container()
                        ]),
                        bgcolor="#0E0E20",
                        border_radius=16,
                        height=200,
                        alignment=ft.alignment.center,
                        clip_behavior=ft.ClipBehavior.ANTI_ALIAS
                    ),
                    ft.Container(height=4, bgcolor="#7B00FF", border_radius=2),
                    ft.Text(ref=title_text, value="✨ Video info will appear here ✨", size=12, weight=ft.FontWeight.BOLD, color="#AAAAFF", text_align=ft.TextAlign.CENTER),
                    ft.Text(ref=channel_text, value="", size=10, color="#7777AA", text_align=ft.TextAlign.CENTER)
                ], spacing=6),
                bgcolor="#16162A",
                border=ft.border.all(1.5, "#FF006A"),
                border_radius=20,
                padding=12,
                margin=ft.margin.symmetric(horizontal=12)
            ),

            # Quality
            ft.Container(
                content=ft.Column([
                    ft.Text("🎨 CHOOSE QUALITY", size=12, weight=ft.FontWeight.BOLD, color="#FFD700"),
                    ft.Row(controls=quality_buttons[:3], spacing=6),
                    ft.Row(controls=quality_buttons[3:], spacing=6),
                ], spacing=8),
                bgcolor="#16162A",
                border=ft.border.all(1.5, "#00F0FF"),
                border_radius=20,
                padding=14,
                margin=ft.margin.all(12)
            ),

            # Progress
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(ref=percent_text, value="0%", size=18, weight=ft.FontWeight.BOLD, color="#00F0FF"),
                        ft.Text(ref=status_text, value="⚡ Ready to rock!", size=11, weight=ft.FontWeight.BOLD, color="#AAAAFF")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.ProgressBar(ref=progress_bar, value=0, color="#7B00FF", bgcolor="#0E0E20", height=10, border_radius=10),
                    ft.Row([
                        ft.Text(ref=speed_text, value="🚀 0 MB/s • ⏳ --:--", size=10, color="#666688"),
                        ft.Text("📁 ./Videos/", size=10, color="#666688")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(height=3, bgcolor=random.choice(NEON), border_radius=3)
                ], spacing=6),
                bgcolor="#16162A",
                border_radius=20,
                padding=14,
                margin=ft.margin.symmetric(horizontal=12)
            ),

            # Download Button
            ft.Container(
                content=ft.ElevatedButton(ref=download_btn, text="🚀 DOWNLOAD NOW 🚀",
                                          bgcolor="#FF006A", color="white",
                                          height=60,
                                          style=ft.ButtonStyle(
                                              shape=ft.RoundedRectangleBorder(radius=18),
                                              side=ft.BorderSide(2, "#00F0FF")
                                          ),
                                          on_click=start_download),
                margin=ft.margin.all(12)
            ),

            # History
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("📜 DOWNLOAD HISTORY", size=12, weight=ft.FontWeight.BOLD, color="#FFD700"),
                        ft.TextButton("Clear", style=ft.ButtonStyle(color="#FF006A"),
                                      on_click=lambda e: (history.clear(), save_history(history), refresh_history()))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Column(ref=history_col, spacing=4)
                ], spacing=6),
                bgcolor="#16162A",
                border=ft.border.all(1.2, "#FFD700"),
                border_radius=20,
                padding=14,
                margin=ft.margin.all(12)
            ),

            ft.Text("Made with 💜 • Android Ready • yt-dlp", size=10, weight=ft.FontWeight.BOLD, color="#444466", text_align=ft.TextAlign.CENTER)
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
    )

    refresh_history()

if __name__ == "__main__":
    # Desktop: run with ft.app, Mobile: flet auto-runs main() so we skip
    try:
        ft.app(target=main)
    except AttributeError:
        pass
