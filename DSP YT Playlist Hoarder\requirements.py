import subprocess
import sys

def install_requirements():
    requirements = [
        'yt-dlp',
        'colorama',
        'requests',
        'spotipy',
        'tqdm',
        'mutagen'
    ]
    
    print("Installing required packages for DSP_YT-Playlist-Hoarder...")
    for package in requirements:
        print(f"\nInstalling {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print("\nInstalling FFmpeg...")
    if sys.platform == "win32":
        subprocess.check_call([sys.executable, "-m", "pip", "install", "ffmpeg-python"])
    else:
        print("Please install FFmpeg manually for your system")
    
    print("\nAll requirements installed successfully!")

if __name__ == "__main__":
    install_requirements()