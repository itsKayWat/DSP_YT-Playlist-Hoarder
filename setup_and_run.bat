@echo off
setlocal EnableDelayedExpansion

:: Check if running with administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] Running with administrator privileges
) else (
    echo [WARNING] Not running with administrator privileges
    echo Some features might not work correctly
    echo Consider running as administrator for full functionality
    timeout /t 5
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                                                              ║
echo ║                ██████╗ ███████╗██████╗                       ║
echo ║                ██╔══██╗██╔════╝██╔══██╗                      ║
echo ║                ██║  ██║███████╗██████╔╝                      ║
echo ║                ██║  ██║╚════██║██╔═══╝                       ║
echo ║                ██████╔╝███████║██║                           ║
echo ║                ╚═════╝ ╚══════╝╚═╝                           ║
echo ║                                                              ║
echo ║                 Digital Sound Plug                           ║
echo ║           YouTube / Spotify Playlist Hoarder                 ║
echo ║                                                              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Setting up DSP YT Playlist Hoarder...
echo.

:: Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed!
    echo Please install Python 3.x from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b
)

:: Check Python version
python -c "import sys; exit(0) if sys.version_info >= (3,7) else exit(1)" > nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3.7 or higher is required!
    echo Current Python version:
    python --version
    pause
    exit /b
)

echo [✓] Python check passed
echo.

:: Check if FFmpeg is installed
ffmpeg -version > nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found! Installing FFmpeg...
    python -m pip install ffmpeg-python
)

echo [✓] FFmpeg check passed
echo.

:: Check internet connection
ping 8.8.8.8 -n 1 -w 1000 >nul
if errorlevel 1 (
    echo [ERROR] No internet connection detected!
    echo Please check your internet connection and try again.
    pause
    exit /b
)

echo [✓] Internet connection verified
echo.

echo Installing/Updating required packages...
echo.

:: Upgrade pip
python -m pip install --upgrade pip

:: Remove existing packages to avoid conflicts
echo Cleaning existing packages...
python -m pip uninstall -y yt-dlp colorama requests spotipy tqdm mutagen moviepy imageio imageio-ffmpeg decorator pytube youtube_transcript_api pystray pillow
python -m pip cache purge

:: Install all required packages
echo Installing required packages...
python -m pip install yt-dlp
python -m pip install colorama
python -m pip install requests
python -m pip install spotipy
python -m pip install tqdm
python -m pip install mutagen
python -m pip install decorator==4.4.2
python -m pip install imageio==2.9.0
python -m pip install imageio-ffmpeg==0.4.5
python -m pip install moviepy==1.0.3
python -m pip install pytube
python -m pip install youtube_transcript_api
python -m pip install pystray
python -m pip install pillow
python -m pip install tkinter

echo.
echo [✓] All packages installed successfully!
echo.

:: Create necessary folders
if not exist "Downloads" mkdir "Downloads"
if not exist "Downloads\Video" mkdir "Downloads\Video"
if not exist "Downloads\Audio" mkdir "Downloads\Audio"
if not exist "Downloads\Playlists" mkdir "Downloads\Playlists"

echo [✓] Folder structure created
echo.

:: Verify python script exists
if not exist "youtube-playlist-hoarder.py" (
    echo [ERROR] youtube-playlist-hoarder.py not found!
    echo Please ensure the script is in the same directory.
    pause
    exit /b
)

echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Setup Complete!                           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Starting DSP YT Playlist Hoarder...
echo.

:: Run the Python script
python youtube-playlist-hoarder.py

if errorlevel 1 (
    echo [ERROR] An error occurred while running the script.
    echo Please check the error message above.
    pause
    exit /b
)

pause
endlocal 