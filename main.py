import flet as ft
import yt_dlp
import os
import threading

def main(page: ft.Page):
    try:
        page.title = "YT Downloader - ULTIMATE"
        page.theme_mode = ft.ThemeMode.DARK
        page.bgcolor = "#0A0A14"
        page.padding = 10
        page.scroll = ft.ScrollMode.AUTO

        url_field = ft.TextField(
            hint_text="https://youtube.com/watch?v=...",
            border_radius=12, filled=True, fill_color="#1E1E3A", expand=True
        )
        title_text = ft.Text("✨ Paste link above ✨", size=13, color="#AAAAFF", text_align=ft.TextAlign.CENTER)
        status_text = ft.Text("⚡ Ready", size=12, color="#00FF88")
        percent_text = ft.Text("0%", size=18, weight=ft.FontWeight.BOLD, color="#00F0FF")
        progress_bar = ft.ProgressBar(value=0, color="#7B00FF", bgcolor="#1E1E3A", height=10)

        selected_quality = {"value": "bestvideo+bestaudio/best"}

        def select_quality(e):
            selected_quality["value"] = e.control.data
            status_text.value = f"Quality: {e.control.text}"
            page.update()

        quality_buttons = [
            ft.ElevatedButton("Best", data="bestvideo+bestaudio/best", bgcolor="#FF006A", color="white", on_click=select_quality),
            ft.ElevatedButton("1080p", data="bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best", bgcolor="#1E1E3A", color="white", on_click=select_quality),
            ft.ElevatedButton("720p", data="bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best", bgcolor="#1E1E3A", color="white", on_click=select_quality),
            ft.ElevatedButton("Audio", data="bestaudio/best", bgcolor="#1E1E3A", color="white", on_click=select_quality),
        ]

        def on_progress(d):
            try:
                if d['status'] == 'downloading':
                    total = d.get('total_bytes') or d.get('total_bytes_estimate') or 1
                    downloaded = d.get('downloaded_bytes', 0)
                    p = downloaded / total if total else 0
                    progress_bar.value = p
                    percent_text.value = f"{int(p*100)}%"
                    status_text.value = f"Downloading {int(p*100)}% - {d.get('_speed_str','')}"
                    page.update()
            except: pass

        def start_download(e):
            url = url_field.value.strip()
            if not url:
                status_text.value = "⚠️ Enter URL first"
                page.update()
                return
            status_text.value = "Fetching..."
            page.update()
            def run():
                try:
                    save_path = "/storage/emulated/0/Download/YTDownloader"
                    os.makedirs(save_path, exist_ok=True)
                except:
                    save_path = "."
                opts = {"format": selected_quality["value"], "outtmpl": f"{save_path}/%(title)s.%(ext)s", "progress_hooks": [on_progress], "noplaylist": True}
                try:
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        info = ydl.extract_info(url, download=False)
                        title_text.value = info.get('title','')[:60]
                        page.update()
                        ydl.download([url])
                    status_text.value = "✅ Done! Check Downloads/YTDownloader"
                    progress_bar.value = 1
                    page.update()
                except Exception as ex:
                    status_text.value = f"❌ {str(ex)[:80]}"
                    page.update()
            threading.Thread(target=run, daemon=True).start()

        page.add(
            ft.Column([
                ft.Container(content=ft.Row([ft.Text("▶ YT Downloader ULTIMATE", size=18, weight=ft.FontWeight.BOLD, color="white"), ft.Icon(ft.Icons.VIDEO_LIBRARY, color="#FF006A")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), bgcolor="#111122", padding=16, border_radius=12),
                ft.Container(content=ft.Column([ft.Text("🔗 PASTE LINK", size=12, weight=ft.FontWeight.BOLD, color="#00F0FF"), url_field, title_text], spacing=10), bgcolor="#16162A", border=ft.border.all(1, "#7B00FF"), border_radius=16, padding=14),
                ft.Container(content=ft.Column([ft.Text("🎨 QUALITY", size=12, weight=ft.FontWeight.BOLD, color="#FFD700"), ft.Row(controls=quality_buttons, wrap=True, spacing=6)], spacing=8), bgcolor="#16162A", border=ft.border.all(1, "#00F0FF"), border_radius=16, padding=12),
                ft.Container(content=ft.Column([ft.Row([percent_text, status_text], alignment=ft.MainAxisAlignment.SPACE_BETWEEN), progress_bar, ft.ElevatedButton("🚀 DOWNLOAD NOW 🚀", bgcolor="#FF006A", color="white", height=55, width=400, on_click=start_download)], spacing=8), bgcolor="#16162A", border_radius=16, padding=12),
            ], spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)
        )
    except Exception as ex:
        page.clean()
        page.add(ft.Column([ft.Text("⚠️ Error", size=20, color="red"), ft.Text(str(ex), size=12)]))
        page.update()

if __name__ == "__main__":
    try: ft.app(target=main)
    except: pass
