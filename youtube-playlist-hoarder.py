import yt_dlp
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
import subprocess
import sys
import time
from colorama import init, Fore, Back, Style
from pathlib import Path
import pystray
from PIL import Image, ImageDraw
import threading
import tkinter as tk
from tkinter import Tk

# Initialize colorama for Windows
init()

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# FFmpeg will be in a folder next to the script
FFMPEG_PATH = os.path.join(SCRIPT_DIR, "ffmpeg-master-latest-win64-gpl", "bin")
FFMPEG_EXE = os.path.join(FFMPEG_PATH, "ffmpeg.exe")
FFPROBE_EXE = os.path.join(FFMPEG_PATH, "ffprobe.exe")

# Define folder structure
DOWNLOADS_DIR = os.path.join(SCRIPT_DIR, "downloads")
PLAYLISTS_DIR = os.path.join(DOWNLOADS_DIR, "playlists")
VIDEOS_DIR = os.path.join(DOWNLOADS_DIR, "videos", "video")
SONGS_DIR = os.path.join(DOWNLOADS_DIR, "songs", "converted_audio")
COMBINED_VIDEOS_DIR = os.path.join(DOWNLOADS_DIR, "combined_videos", "video")
COMBINED_SONGS_DIR = os.path.join(DOWNLOADS_DIR, "combined_songs", "converted_audio")

def print_banner():
    print(Fore.CYAN + """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║                ██████╗ ███████╗██████╗                       ║
║                ██╔══██╗██╔════╝██╔══██╗                      ║
║                ██║  ██║███████╗██████╔╝                      ║
║                ██║  ██║╚════██║██╔═══╝                       ║
║                ██████╔╝███████║██║                           ║
║                ╚═════╝ ╚══════╝╚═╝                           ║
║                                                              ║
║                 Digital Sound Plug                           ║
║           YouTube / Spotify Playlist Hoarder                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""" + Style.RESET_ALL)

def print_instructions():
    print(Fore.WHITE + """
╔══════════════════════════════════════════════════════════════╗
║                     HOW TO USE                               ║
║                                                              ║
║  1. Copy a link from:                                        ║
║     • YouTube Video                                          ║
║     • YouTube Playlist                                       ║
║     • YouTube Music                                          ║
║     • Spotify Track                                          ║
║     • Spotify Playlist                                       ║
║                                                              ║
║  2. Paste the link when prompted                             ║
║                                                              ║
║  3. The tool will automatically:                             ║
║     • Detect the type of content                             ║
║     • Ask any needed questions                               ║
║     • Download in the best quality                           ║
║     • Save to the correct folder                             ║
║                                                              ║
║  Note: Press any key to open folders, Enter to exit          ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
""" + Style.RESET_ALL)

def print_menu():
    print(Fore.YELLOW + "\nSelect download type:")
    print(Fore.WHITE + "╔════════════════════════════╗")
    print(f"║ {Fore.GREEN}1.{Fore.WHITE} Individual Video        ║")
    print(f"║ {Fore.GREEN}2.{Fore.WHITE} Playlist               ║")
    print(f"║ {Fore.GREEN}3.{Fore.WHITE} Music (YouTube Music)  ║")
    print("╚════════════════════════════╝" + Style.RESET_ALL)

def print_progress(message):
    print(Fore.CYAN + f"\n→ {message}" + Style.RESET_ALL)

def print_success(message):
    print(Fore.GREEN + f"\n✓ {message}" + Style.RESET_ALL)

def print_error(message):
    print(Fore.RED + f"\n✗ {message}" + Style.RESET_ALL)

def show_loading_animation(duration):
    animation = "|/-\\"
    for i in range(duration * 10):
        time.sleep(0.1)
        sys.stdout.write(Fore.CYAN + "\r" + animation[i % len(animation)] + Style.RESET_ALL)
        sys.stdout.flush()
    print()

def print_progress_bar(current, total, prefix='Progress:', suffix='Complete', length=50):
    percent = float(current) * 100 / total
    filled_length = int(length * current // total)
    bar = Fore.GREEN + '█' * filled_length + Fore.WHITE + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent:.1f}% {suffix}', end='\r')
    if current == total:
        print()

class DownloadProgress:
    def __init__(self):
        self.current_title = ""
        self.start_time = None
        
    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if self.current_title != d.get('filename', ''):
                self.current_title = d.get('filename', '')
                self.start_time = time.time()
            
            # Calculate download progress
            total = d.get('total_bytes', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                percent = downloaded * 100.0 / total
                speed = downloaded / (time.time() - self.start_time)
                speed_str = f'{speed/1024/1024:.1f} MB/s'
                
                # Print progress bar
                print_progress_bar(
                    downloaded, 
                    total,
                    prefix=f'{Fore.CYAN}Downloading: {os.path.basename(self.current_title)}',
                    suffix=f'{percent:.1f}% ({speed_str}){Style.RESET_ALL}',
                    length=40
                )

def create_folders():
    """Create all necessary folders"""
    folders = [
        DOWNLOADS_DIR,
        PLAYLISTS_DIR,
        VIDEOS_DIR,
        SONGS_DIR,
        COMBINED_VIDEOS_DIR,
        COMBINED_SONGS_DIR
    ]
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

def get_output_dir(is_playlist, as_audio, playlist_name=None):
    """Determine the correct output directory based on download type"""
    if is_playlist:
        # Create a subfolder for this specific playlist
        playlist_folder = os.path.join(PLAYLISTS_DIR, sanitize_filename(playlist_name))
        os.makedirs(playlist_folder, exist_ok=True)
        return playlist_folder
    return SONGS_DIR if as_audio else VIDEOS_DIR

def verify_ffmpeg():
    if not os.path.exists(FFMPEG_EXE) or not os.path.exists(FFPROBE_EXE):
        print_error("FFmpeg files not found!")
        print(f"Looking in: {FFMPEG_PATH}")
        print("Please ensure ffmpeg.exe and ffprobe.exe are in the bin directory")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Add FFmpeg to system PATH
    if FFMPEG_PATH not in os.environ['PATH']:
        os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ['PATH']
    
    return FFMPEG_EXE, FFPROBE_EXE

def sanitize_filename(title):
    # Remove invalid characters from filename
    return re.sub(r'[<>:"/\\|?*]', '', title)

def get_captions(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return '\n'.join(f"{item['start']}: {item['text']}" for item in transcript)
    except:
        return "No captions available"

def combine_audio_files(files, playlist_name):
    try:
        # Use playlist name for the output file
        safe_playlist_name = sanitize_filename(playlist_name)
        output_path = os.path.join(COMBINED_SONGS_DIR, f"{safe_playlist_name}.mp3")
        
        # Create a text file listing all input files
        list_file = "files_to_combine.txt"
        with open(list_file, "w", encoding='utf-8') as f:
            for audio_file in files:
                f.write(f"file '{audio_file}'\n")
        
        print(f"\nCreating combined file: {safe_playlist_name}.mp3")
        
        # Use FFmpeg to concatenate files
        cmd = [
            FFMPEG_EXE,  # Use the full path
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            output_path
        ]
        subprocess.run(cmd, check=True)
        
        # Clean up the temporary file
        os.remove(list_file)
        return True
    except Exception as e:
        print_error(f"Error combining files: {str(e)}")
        return False

def combine_video_files(files, playlist_name):
    try:
        # Use playlist name for the output file
        safe_playlist_name = sanitize_filename(playlist_name)
        output_path = os.path.join(COMBINED_VIDEOS_DIR, f"{safe_playlist_name}.mp4")
        
        # Create a text file listing all input files
        list_file = "files_to_combine.txt"
        with open(list_file, "w", encoding='utf-8') as f:
            for video_file in files:
                f.write(f"file '{video_file}'\n")
        
        print(f"\nCreating combined file: {safe_playlist_name}.mp4")
        
        # Use FFmpeg to concatenate files
        ffmpeg_exe = os.path.join(FFMPEG_PATH, 'ffmpeg.exe')
        cmd = [
            ffmpeg_exe, '-f', 'concat', '-safe', '0',
            '-i', list_file, '-c', 'copy', output_path
        ]
        subprocess.run(cmd, check=True)
        
        # Clean up the temporary file
        os.remove(list_file)
        return True
    except Exception as e:
        print(f"Error combining files: {str(e)}")
        return False

def get_video_formats(url):
    """Get available formats with their sizes"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = []
            
            # Filter and organize formats
            for f in info['formats']:
                # Skip audio-only formats
                if f.get('vcodec') == 'none':
                    continue
                    
                # Get format details
                format_id = f.get('format_id', 'N/A')
                ext = f.get('ext', 'N/A')
                resolution = f.get('resolution', 'N/A')
                filesize = f.get('filesize', 0)
                filesize_mb = filesize / (1024 * 1024) if filesize else 0
                
                # Convert filesize to GB if it's over 1024 MB
                if filesize_mb > 1024:
                    filesize_str = f"{filesize_mb/1024:.1f} GB"
                else:
                    filesize_str = f"{filesize_mb:.1f} MB"
                
                # Only include formats with video
                if resolution != 'N/A':
                    formats.append({
                        'format_id': format_id,
                        'ext': ext,
                        'resolution': resolution,
                        'filesize': filesize_str
                    })
            
            # Sort formats by resolution (highest to lowest)
            formats.sort(key=lambda x: {
                '4320p': 8,  # 8K
                '2160p': 7,  # 4K
                '1440p': 6,  # 2K
                '1080p': 5,  # Full HD
                '720p': 4,   # HD
                '480p': 3,
                '360p': 2,
                '240p': 1,
                '144p': 0
            }.get(x['resolution'], -1), reverse=True)
            
            return formats
    except Exception as e:
        print_error(f"Error getting formats: {str(e)}")
        return []

def select_video_quality(url):
    """Let user select video quality with fallback to next best available"""
    # First ask if user wants best quality
    print(Fore.YELLOW + "\nDo you want the best quality available?" + Style.RESET_ALL)
    print(Fore.WHITE + "╔════════════════════════════════════════════╗")
    print(f"║ {Fore.GREEN}Y{Fore.WHITE} - Best quality (Larger file size)          ║")
    print(f"║ {Fore.GREEN}N{Fore.WHITE} - Select specific quality (See options)     ║")
    print("╚════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    choice = input(Fore.YELLOW + "\nYour choice (Y/N): " + Style.RESET_ALL).lower()
    if choice == 'y':
        return 'bestvideo+bestaudio/best'  # Best quality available
    
    # If user wants to select quality, show available formats
    formats = get_video_formats(url)
    if not formats:
        return 'best'
        
    print(Fore.YELLOW + "\nAvailable video qualities:" + Style.RESET_ALL)
    print(Fore.WHITE + "╔═══════════════════════════════════════════════════════╗")
    print("║  #  Resolution  Format    Size          Codec          ║")
    print("╠═══════════════════════════════════════════════════════╣")
    
    for i, f in enumerate(formats, 1):
        print(f"║ {Fore.GREEN}{i:2d}{Fore.WHITE}  {f['resolution']:10} {f['ext']:8} {f['filesize']:12}  ║")
    
    print("║                                                       ║")
    print(f"║ {Fore.GREEN}0{Fore.WHITE}   Best Quality (Automatic Selection)                  ║")
    print("╚═══════════════════════════════════════════════════════╝" + Style.RESET_ALL)
    
    while True:
        try:
            choice = input(Fore.YELLOW + "\nSelect quality (0-" + str(len(formats)) + "): " + Style.RESET_ALL)
            choice = int(choice)
            if choice == 0:
                return 'bestvideo+bestaudio/best'  # This ensures best available quality
            if 1 <= choice <= len(formats):
                selected_format = formats[choice-1]
                # Create a format string that will fall back to next best available
                format_string = f"bestvideo[height<={selected_format['resolution'][:-1]}]+bestaudio/best[height<={selected_format['resolution'][:-1]}]/best"
                return format_string
            print_error("Invalid choice")
        except ValueError:
            print_error("Please enter a number")

def download_video(url, is_playlist=False, as_audio=True, playlist_name=None, format_id=None):
    try:
        ffmpeg_exe, ffprobe_exe = verify_ffmpeg()
        output_dir = get_output_dir(is_playlist, as_audio, playlist_name)
        
        # Configure yt-dlp options with explicit FFmpeg path
        progress_tracker = DownloadProgress()
        ydl_opts = {
            'format': format_id if format_id else ('bestaudio/best' if as_audio else 'bestvideo+bestaudio/best'),
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': True,
            'ffmpeg_location': FFMPEG_PATH,  # Explicitly set FFmpeg path
            'progress_hooks': [progress_tracker.progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if as_audio else [],
        }
            
        # Add --no-playlist flag for single video downloads
        if '&list=' in url and not url.startswith('https://www.youtube.com/playlist'):
            url = url.split('&list=')[0]

        # Download the video/audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info['title']
            video_id = info['id']
            
            # Get the output path
            if as_audio:
                filename = f"{sanitize_filename(title)}.mp3"
            else:
                filename = f"{sanitize_filename(title)}.mp4"
            output_path = os.path.join(output_dir, filename)
            
            # Download captions
            captions = get_captions(video_id)
            caption_path = os.path.join(output_dir, f"{sanitize_filename(title)}_captions.txt")
            with open(caption_path, 'w', encoding='utf-8') as f:
                f.write(captions)
                
            return output_path
            
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return None

def print_platform_menu():
    print(Fore.YELLOW + "\nSelect platform:")
    print(Fore.WHITE + "╔════════════════════════════╗")
    print(f"║ {Fore.GREEN}1.{Fore.WHITE} YouTube               ║")
    print(f"║ {Fore.GREEN}2.{Fore.WHITE} Spotify               ║")
    print("╚════════════════════════════╝" + Style.RESET_ALL)

def setup_spotify():
    # You'll need to get these from Spotify Developer Dashboard
    client_id = "YOUR_SPOTIFY_CLIENT_ID"
    client_secret = "YOUR_SPOTIFY_CLIENT_SECRET"
    
    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id, 
            client_secret=client_secret
        )
        return spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    except Exception as e:
        print_error(f"Error setting up Spotify: {str(e)}")
        return None

def get_spotify_track_info(sp, track_url):
    try:
        # Extract track ID from URL
        track_id = track_url.split('/')[-1].split('?')[0]
        track = sp.track(track_id)
        return {
            'title': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name']
        }
    except Exception as e:
        print_error(f"Error getting track info: {str(e)}")
        return None

def get_spotify_playlist_tracks(sp, playlist_url):
    try:
        # Extract playlist ID from URL
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        results = sp.playlist_tracks(playlist_id)
        tracks = []
        
        for item in results['items']:
            track = item['track']
            tracks.append({
                'title': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name']
            })
            
        return tracks
    except Exception as e:
        print_error(f"Error getting playlist tracks: {str(e)}")
        return []

def download_spotify_track(track_info, output_dir):
    try:
        # Search YouTube for the track
        search_query = f"{track_info['artist']} - {track_info['title']} audio"
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'default_search': 'ytsearch',
            'quiet': False,
            'no_warnings': True,
            'extract_flat': False,
            'ffmpeg_location': FFMPEG_PATH,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        return True
    except Exception as e:
        print_error(f"Error downloading track: {str(e)}")
        return False

def download_from_spotify_url(url, is_playlist=False):
    try:
        if 'spotify.com/track/' in url:
            # Extract track name and artist from URL
            track_id = url.split('/')[-1].split('?')[0]
            # Use youtube-dl's search feature to find the best match
            search_query = f"ytsearch:{track_id} audio"
            download_audio(search_query, SONGS_DIR)
            
        elif 'spotify.com/playlist/' in url:
            print_error("For playlists, please provide individual track URLs")
            return False
            
        return True
    except Exception as e:
        print_error(f"Error processing Spotify URL: {str(e)}")
        return False

def download_audio(search_query, output_dir):
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'default_search': 'ytsearch',
            'quiet': False,
            'no_warnings': True,
            'extract_flat': False,
            'ffmpeg_location': FFMPEG_PATH,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'progress_hooks': [DownloadProgress().progress_hook],
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            
        return True
    except Exception as e:
        print_error(f"Error downloading audio: {str(e)}")
        return False

def interpret_url(url):
    # Determine URL type
    if 'youtube.com' in url or 'youtu.be' in url:
        if 'playlist' in url:
            print_progress("YouTube Playlist detected")
            return ('youtube', 'playlist', url)
        elif 'music.youtube' in url:
            print_progress("YouTube Music track detected")
            return ('youtube', 'music', url)
        else:
            print_progress("YouTube video detected")
            return ('youtube', 'video', url)
    elif 'spotify.com' in url:
        if 'track' in url:
            print_progress("Spotify track detected")
            return ('spotify', 'track', url)
        elif 'playlist' in url:
            print_progress("Spotify playlist detected")
            return ('spotify', 'playlist', url)
    
    print_error("Unrecognized URL format")
    return None

def process_youtube_playlist(url, combine_files=False, audio_only=False, quality='best'):
    """Process a YouTube playlist"""
    try:
        print(Fore.YELLOW + "\n→ Processing playlist..." + Style.RESET_ALL)
        print(Fore.YELLOW + "\n→ Fetching playlist information..." + Style.RESET_ALL)
        
        # Add timeout and show progress
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just get info
            'timeout': 30,  # Add timeout of 30 seconds
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                print(Fore.YELLOW + "\n→ Extracting playlist details..." + Style.RESET_ALL)
                playlist_info = ydl.extract_info(url, download=False)
                
                if not playlist_info or 'entries' not in playlist_info:
                    print(Fore.RED + "\nError: Could not fetch playlist information" + Style.RESET_ALL)
                    return
                
                total_videos = len(playlist_info['entries'])
                print(Fore.GREEN + f"\nFound {total_videos} videos in playlist" + Style.RESET_ALL)
                
                # Process each video
                for index, entry in enumerate(playlist_info['entries'], 1):
                    if entry is None:  # Skip unavailable videos
                        continue
                    print(Fore.YELLOW + f"\n→ Processing video {index}/{total_videos}" + Style.RESET_ALL)
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    download_video(video_url, combine_files, audio_only, quality)
                    
            except yt_dlp.utils.DownloadError as e:
                print(Fore.RED + f"\nError downloading playlist: {str(e)}" + Style.RESET_ALL)
            except Exception as e:
                print(Fore.RED + f"\nUnexpected error: {str(e)}" + Style.RESET_ALL)
                
    except Exception as e:
        print(Fore.RED + f"\nFailed to process playlist: {str(e)}" + Style.RESET_ALL)
        
    print(Fore.GREEN + "\n→ Playlist processing complete" + Style.RESET_ALL)

def create_hidden_window():
    # Create a hidden root window to handle close events
    root = Tk()
    root.withdraw()  # Hide the window
    
    def on_closing():
        # Properly close the application
        root.quit()
        os._exit(0)  # Ensure complete exit
    
    def minimize_to_tray():
        # Minimize to system tray
        root.withdraw()
        return "break"
    
    # Bind minimize button to minimize_to_tray
    root.protocol("WM_DELETE_WINDOW", minimize_to_tray)
    root.bind('<Alt-F4>', lambda e: minimize_to_tray())
    
    return root

def create_system_tray(root_window):
    # Create a 64x64 image with a music note and download arrow
    icon_size = 64
    icon_image = Image.new('RGB', (icon_size, icon_size), color='black')
    
    # Create a drawing object
    draw = ImageDraw.Draw(icon_image)
    
    # Draw music note (simplified)
    # Note head
    draw.ellipse([24, 30, 34, 40], fill='white')
    # Note stem
    draw.rectangle([32, 12, 34, 30], fill='white')
    # Flag
    draw.arc([34, 12, 44, 22], 0, 180, fill='white', width=2)
    
    # Draw download arrow
    # Arrow shaft
    draw.rectangle([28, 35, 32, 50], fill='white')
    # Arrow head
    draw.polygon([20, 42, 30, 52, 40, 42], fill='white')
    
    def on_exit(icon, item):
        icon.stop()
        os._exit(0)  # Force exit the application
    
    def on_show(icon, item):
        if os.name == 'nt':
            # Windows-specific code to show console
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 1)
    
    # Create the system tray icon with show/exit options
    icon = pystray.Icon("DSP_YT-Playlist-Hoarder",
                       icon_image,
                       "DSP YT Playlist Hoarder",
                       menu=pystray.Menu(
                           pystray.MenuItem("Show", on_show),
                           pystray.MenuItem("Exit", on_exit)
                       ))
    
    return icon

def main():
    try:
        # Create hidden window to handle close events
        root = create_hidden_window()
        
        # Create and start system tray icon in a separate thread
        icon = create_system_tray(root)  # Pass root window reference
        icon_thread = threading.Thread(target=icon.run)
        icon_thread.daemon = True
        icon_thread.start()
        
        print_banner()
        print_instructions()
        
        # Verify FFmpeg at startup
        print_progress("Verifying FFmpeg installation...")
        verify_ffmpeg()
        show_loading_animation(1)
        
        # Create all necessary folders
        print_progress("Creating necessary folders...")
        create_folders()
        
        # Get and interpret URL (only once)
        url = input(Fore.YELLOW + "\nPaste your URL: " + Style.RESET_ALL).strip()
        
        # Add 'https://' if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        url_info = interpret_url(url)  # Pass the URL to interpret_url
        if not url_info:
            print_error("Failed to interpret URL")
            input("Press Enter to exit...")
            return
            
        platform, content_type, url = url_info
        
        # Handle based on URL type
        if platform == 'youtube':
            convert_to_audio = content_type == 'music'
            is_playlist = content_type == 'playlist'
            
            if is_playlist:
                combine_files = input(Fore.YELLOW + "Combine all files into one? (Y/N): " + Style.RESET_ALL).lower() == 'y'
                convert_to_audio = input(Fore.YELLOW + "Convert to audio files? (Y/N): " + Style.RESET_ALL).lower() == 'y'
                
                if not convert_to_audio:
                    # Show quality options with storage estimates
                    print_progress("Getting available video qualities...")
                    format_id = select_video_quality(url)
                    print_progress(f"Selected quality: {format_id}")
                
                print_progress("Processing playlist...")
                process_youtube_playlist(url, combine_files, convert_to_audio, format_id if not convert_to_audio else None)
        
        else:  # Spotify
            download_from_spotify_url(url, content_type == 'playlist')
        
        print_success("\nOperation completed!")
        print(Fore.CYAN + "\nPress any key to open the download folder, or Enter to exit..." + Style.RESET_ALL)
        
        # Wait for keypress
        import msvcrt
        key = msvcrt.getch()
        
        # If any key other than Enter was pressed, open the folder
        if key != b'\r':
            target_dir = DOWNLOADS_DIR  # Default to main downloads directory
            if platform == 'youtube':
                if is_playlist:
                    target_dir = COMBINED_SONGS_DIR if convert_to_audio else COMBINED_VIDEOS_DIR
                else:
                    target_dir = SONGS_DIR if convert_to_audio else VIDEOS_DIR
            else:  # Spotify
                target_dir = SONGS_DIR
                
            os.startfile(target_dir) if os.name == 'nt' else os.system(f'xdg-open "{target_dir}"')
            
        # Start the tkinter event loop
        root.mainloop()
        
    except Exception as e:
        print_error(f"An error occurred: {str(e)}")
        print("Please check your internet connection and try again")
        input("Press Enter to exit...")
    finally:
        if 'icon' in locals():
            icon.stop()

if __name__ == "__main__":
    main()
