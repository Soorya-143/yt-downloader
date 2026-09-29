import flet as ft
import yt_dlp
import os
import json
import threading
import random
from datetime import datetime

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
    try:
        page.title = "YT Downloader - ULTIMATE"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#0A0A14"
        page.padding = 0
        page.scroll = ft.ScrollMode.AUTO

        history = load_history()
        selected_quality = {"value": "Best Quality"}
        is_dark = {"value": True}

        url_field = ft.TextField(
            hint_text="https://youtu.be/... or shorts/...",
            border_radius=12, filled=True, fill_color="#0E0E20",
            border_color="#2A2A5A", expand=True, height=50,
            text_size=13, color="white"
        )
        title_text = ft.Text("✨ Video info will appear here ✨", size=12, weight=ft.FontWeight.BOLD, color="#AAAAFF", text_align=ft.TextAlign.CENTER)
        channel_text = ft.Text("", size=10, color="#7777AA", text_align=ft.TextAlign.CENTER)
        progress_bar = ft.ProgressBar(value=0, color="#7B00FF", bgcolor="#0E0E20", height=10, border_radius=10)
        percent_text = ft.Text("0%", size=18, weight=ft.FontWeight.BOLD, color="#00F0FF")
        status_text = ft.Text("⚡ Ready to rock!", size=11, weight=ft.FontWeight.BOLD, color="#AAAAFF")
        speed_text = ft.Text("🚀 0 MB/s • ⏳ --:--", size=10, color="#666688")
        thumb_image = ft.Image(src="", width=400, height=200, fit=ft.ImageFit.COVER, border_radius=16, visible=False)
        history_col = ft.Column(spacing=4)

        NEON = ["#FF006A", "#7B00FF", "#00F0FF", "#00FF88", "#FFD700"]

        def get_format(q):
            if q == "1080p": return "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best"
            if q == "720p": return "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best"
            if q == "480p": return "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best"
            if q == "Audio Only (mp3)": return "bestaudio/best"
            return "bestvideo+bestaudio/best"

        def select_quality(e):
            selected_quality["value"] = e.control.data
            for btn in quality_buttons:
                if btn.data == selected_quality["value"]:
                    btn.bgcolor = btn.data_color
                    btn.style = ft.ButtonStyle(side=ft.BorderSide(2.5, ft.Colors.WHITE), shape=ft.RoundedRectangleBorder(radius=20))
                else:
                    btn.bgcolor = "#1E1E3A"
                    btn.style = ft.ButtonStyle(side=ft.BorderSide(0, ft.Colors.TRANSPARENT), shape=ft.RoundedRectangleBorder(radius=20))
            page.update()

        def refresh_history():
            history_col.controls.clear()
            if not history:
                history_col.controls.append(ft.Text("No downloads yet 📭", size=11, color="#666688", text_align=ft.TextAlign.CENTER))
            else:
                for entry in reversed(history[-5:]):
                    card = ft.Container(
                        content=ft.Row([
                            ft.Container(content=ft.Column([
                                ft.Text(entry["title"][:45], size=12, weight=ft.FontWeight.BOLD, color="white", max_lines=2),
                                ft.Text(f"{entry['time']} • {entry['quality']}", size=10, color="#8888AA")
                            ], spacing=2), expand=True),
                            ft.Container(width=10, height=10, bgcolor=entry["color"], border_radius=10)
                        ]),
                        bgcolor="#1E1E3A",
                        border=ft.border.all(1, entry["color"]),
                        border_radius=12,
                        padding=10,
                        margin=ft.margin.only(bottom=6)
                    )
                    history_col.controls.append(card)
            try: page.update()
            except: pass

        def on_progress(d):
            try:
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                    downloaded = d.get('downloaded_bytes', 0)
                    percent = downloaded / total if total else 0
                    progress_bar.value = percent
                    percent_text.value = f"{int(percent*100)}%"
                    speed_text.value = f"🚀 {d.get('_speed_str','')} • ⏳ {d.get('_eta_str','')}"
                    status_text.value = f"⚡ Downloading {int(percent*100)}%"
                    progress_bar.color = random.choice(NEON)
                    page.update()
            except: pass

        def fetch_preview(e):
            url = url_field.value.strip()
            if not url:
                status_text.value = "⚠️ Paste link first!"
                page.update()
                return
            status_text.value = "🔍 Fetching info..."
            page.update()
            def run():
                try:
                    with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True}) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title_text.value = f"🎬 {info.get('title','')[:60]}"
                        channel_text.value = f"📺 {info.get('uploader','')} • 👁️ {info.get('view_count','')} views"
                        thumb = info.get('thumbnail','')
                        if thumb:
                            thumb_image.src = thumb
                            thumb_image.visible = True
                        status_text.value = "✅ Info loaded!"
                        page.update()
                except Exception as ex:
                    status_text.value = f"❌ {str(ex)[:50]}"
                    page.update()
            threading.Thread(target=run, daemon=True).start()

        def start_download(e):
            url = url_field.value.strip()
            if not url:
                status_text.value = "⚠️ Enter URL"
                page.update()
                return
            try:
                save_path = "/storage/emulated/0/Download/YTDownloader"
                os.makedirs(save_path, exist_ok=True)
            except:
                save_path = "."
                os.makedirs(save_path, exist_ok=True)
            def run():
                status_text.value = "⏳ Downloading..."
                progress_bar.value = 0.1
                page.update()
                is_audio = selected_quality["value"] == "Audio Only (mp3)"
                opts = {
                    "format": get_format(selected_quality["value"]),
                    "outtmpl": f"{save_path}/%(title)s.%(ext)s",
                    "progress_hooks": [on_progress],
                    "noplaylist": True,
                }
                if is_audio:
                    opts["postprocessors"] = [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'192'}]
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        real_title = info.get('title','Video')
                        title_text.value = f"🎬 {real_title[:60]}"
                        page.update()
                        ydl.download([url])
                    status_text.value = "✅ BOOM! Completed! 🎉"
                    percent_text.value = "100%"
                    progress_bar.value = 1
                    entry = {"title": real_title[:50], "quality": selected_quality["value"], "time": datetime.now().strftime("%I:%M %p • %d %b"), "color": random.choice(NEON)}
                    history.append(entry)
                    save_history(history)
                    refresh_history()
                    page.update()
                except Exception as ex:
                    status_text.value = f"❌ {str(ex)[:60]}"
                    page.update()
            threading.Thread(target=run, daemon=True).start()

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
                text=label, data=value, data_color=color,
                bgcolor=color if value==selected_quality["value"] else "#1E1E3A",
                color="white", height=38,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=20), side=ft.BorderSide(2.5, ft.Colors.WHITE) if value==selected_quality["value"] else ft.BorderSide(0, ft.Colors.TRANSPARENT)),
                on_click=select_quality
            )
            quality_buttons.append(btn)

        def toggle_theme(e):
            is_dark["value"] = not is_dark["value"]
            page.theme_mode = ft.ThemeMode.DARK if is_dark["value"] else ft.ThemeMode.LIGHT
            page.bgcolor = "#0A0A14" if is_dark["value"] else "#F5F5FF"
            page.update()

        page.add(
            ft.Column([
                ft.Container(content=ft.Row([
                    ft.Row([ft.Text("●", color="#FF006A", size=26), ft.Text("●", color="#7B00FF", size=26), ft.Text("●", color="#00F0FF", size=26)], spacing=2),
                    ft.Column([ft.Text("YT DOWNLOADER", size=16, weight=ft.FontWeight.BOLD, color="white"), ft.Text("ULTIMATE v3.0", size=10, weight=ft.FontWeight.BOLD, color="#00F0FF")], spacing=0),
                    ft.IconButton(icon=ft.Icons.DARK_MODE, icon_color="#FFD700", bgcolor="#222244", on_click=toggle_theme)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor="#111122", padding=ft.padding.symmetric(horizontal=16, vertical=14)),

                ft.Container(content=ft.Column([
                    ft.Text("🔗 DROP YOUR LINK HERE", size=12, weight=ft.FontWeight.BOLD, color="#00F0FF"),
                    ft.Row([url_field, ft.IconButton(icon=ft.Icons.SEARCH, bgcolor="#7B00FF", icon_color="white", width=50, height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)), on_click=fetch_preview)], spacing=8)
                ], spacing=8), bgcolor="#16162A", border=ft.border.all(1.5, "#7B00FF"), border_radius=20, padding=16, margin=ft.margin.all(12)),

                ft.Container(content=ft.Column([
                    ft.Container(content=ft.Stack([thumb_image, ft.Container(content=ft.Text("🎬\nPaste link & hit 🔍", size=14, weight=ft.FontWeight.BOLD, color="#555588", text_align=ft.TextAlign.CENTER), alignment=ft.alignment.center, width=400, height=200)]), bgcolor="#0E0E20", border_radius=16, height=200, alignment=ft.alignment.center),
                    ft.Container(height=4, bgcolor="#7B00FF", border_radius=2),
                    title_text, channel_text
                ], spacing=6), bgcolor="#16162A", border=ft.border.all(1.5, "#FF006A"), border_radius=20, padding=12, margin=ft.margin.symmetric(horizontal=12)),

                ft.Container(content=ft.Column([
                    ft.Text("🎨 CHOOSE QUALITY", size=12, weight=ft.FontWeight.BOLD, color="#FFD700"),
                    ft.Row(controls=quality_buttons[:3], spacing=6),
                    ft.Row(controls=quality_buttons[3:], spacing=6),
                ], spacing=8), bgcolor="#16162A", border=ft.border.all(1.5, "#00F0FF"), border_radius=20, padding=14, margin=ft.margin.all(12)),

                ft.Container(content=ft.Column([
                    ft.Row([percent_text, status_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    progress_bar,
                    ft.Row([speed_text, ft.Text("📁 Downloads/YTDownloader", size=10, color="#666688")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=6), bgcolor="#16162A", border_radius=20, padding=14, margin=ft.margin.symmetric(horizontal=12)),

                ft.Container(content=ft.ElevatedButton(text="🚀 DOWNLOAD NOW 🚀", bgcolor="#FF006A", color="white", height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=18), side=ft.BorderSide(2, "#00F0FF")), on_click=start_download), margin=ft.margin.all(12)),

                ft.Container(content=ft.Column([
                    ft.Row([ft.Text("📜 DOWNLOAD HISTORY", size=12, weight=ft.FontWeight.BOLD, color="#FFD700"), ft.TextButton("Clear", style=ft.ButtonStyle(color="#FF006A"), on_click=lambda e: (history.clear(), save_history(history), refresh_history()))], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    history_col
                ], spacing=6), bgcolor="#16162A", border=ft.border.all(1.2, "#FFD700"), border_radius=20, padding=14, margin=ft.margin.all(12)),

                ft.Text("Made with 💜 • Android Ready • yt-dlp", size=10, weight=ft.FontWeight.BOLD, color="#444466", text_align=ft.TextAlign.CENTER)
            ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        )

        refresh_history()

    except Exception as ex:
        page.clean()
        page.add(ft.Column([ft.Text(f"⚠️ Error: {ex}", size=14, color="red"), ft.Text(str(ex.__class__), size=10)]))
        try: page.update()
        except: pass

if __name__ == "__main__":
    try:
        ft.app(target=main)
    except:
        pass