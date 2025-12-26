"""
Environment installer for EasyEnv add-on.
Downloads and sets up the ML-Sharp Python environment and checkpoint.
"""

import os
import sys
import subprocess
import urllib.request
import zipfile
import shutil
import ssl
from pathlib import Path
from typing import Optional, Callable


ADDON_DIR = Path(__file__).parent
MLSHARP_DIR = ADDON_DIR / "ml-sharp"
MLSHARP_ENV_DIR = MLSHARP_DIR / "Env"

# Python download URLs (embeddable packages)
PYTHON_DOWNLOADS = {
    'win32': 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip',
    'darwin': None,  # macOS uses full installer
    'linux': None,   # Linux uses system Python or manual setup
}

# Checkpoint URL
CHECKPOINT_URL = "https://huggingface.co/TimChen/ml-sharp/resolve/main/sharp_2572gikvuh.pt?download=true"
CHECKPOINT_FILENAME = "sharp_2572gikvuh.pt"


def download_file(url: str, destination: Path, progress_callback: Optional[Callable[[int, int], None]] = None):
    """
    Download a file with progress tracking.

    Args:
        url: URL to download from
        destination: Path to save file to
        progress_callback: Optional callback(downloaded_bytes, total_bytes)
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {url}")
    print(f"Destination: {destination}")

    # Create SSL context with certificate verification
    ssl_context = None
    try:
        # Try to use certifi for certificate verification (Blender includes this)
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            print("Using certifi for SSL verification")
        except ImportError:
            # Fall back to default SSL context
            ssl_context = ssl.create_default_context()
            print("Using default SSL context")
    except Exception as e:
        print(f"Warning: Could not create SSL context: {e}")
        # Create unverified context as last resort (not recommended but functional)
        ssl_context = ssl._create_unverified_context()
        print("Warning: Using unverified SSL context")

    def report_progress(block_count, block_size, total_size):
        downloaded = block_count * block_size
        if progress_callback:
            progress_callback(downloaded, total_size)

        if total_size > 0:
            percent = min(100, (downloaded / total_size) * 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\rDownloading: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

    try:
        # Install custom opener with SSL context
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ssl_context))
        urllib.request.install_opener(opener)

        urllib.request.urlretrieve(url, destination, reporthook=report_progress)
        print("\nDownload complete!")
        return True
    except Exception as e:
        print(f"\nDownload failed: {e}")
        if destination.exists():
            destination.unlink()
        raise


def install_python_windows(progress_callback: Optional[Callable[[str], None]] = None):
    """
    Download and extract embeddable Python for Windows.

    Args:
        progress_callback: Optional callback for status updates
    """
    if progress_callback:
        progress_callback("Downloading Python 3.13 for Windows...")

    # Download embeddable Python
    python_zip = MLSHARP_DIR / "python_embed.zip"
    download_file(PYTHON_DOWNLOADS['win32'], python_zip)

    if progress_callback:
        progress_callback("Extracting Python...")

    # Extract to Env directory
    MLSHARP_ENV_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(python_zip, 'r') as zip_ref:
        zip_ref.extractall(MLSHARP_ENV_DIR)

    # Clean up zip
    python_zip.unlink()

    # Modify python313._pth to enable pip and site-packages
    pth_file = MLSHARP_ENV_DIR / "python313._pth"
    if pth_file.exists():
        content = pth_file.read_text()
        # Uncomment 'import site' line if it exists
        content = content.replace('#import site', 'import site')
        # Add Lib/site-packages if not present
        if 'Lib/site-packages' not in content:
            content += '\nLib/site-packages\n'
        pth_file.write_text(content)

    if progress_callback:
        progress_callback("Python installation complete")

    return True


def install_pip(python_exe: Path, progress_callback: Optional[Callable[[str], None]] = None):
    """
    Install pip into the embedded Python environment.

    Args:
        python_exe: Path to Python executable
        progress_callback: Optional callback for status updates
    """
    if progress_callback:
        progress_callback("Installing pip...")

    # Download get-pip.py
    get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
    get_pip_path = MLSHARP_ENV_DIR / "get-pip.py"

    print("Downloading get-pip.py...")
    download_file(get_pip_url, get_pip_path)

    # Run get-pip.py
    print("Installing pip...")
    result = subprocess.run(
        [str(python_exe), str(get_pip_path)],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"pip installation output: {result.stdout}")
        print(f"pip installation errors: {result.stderr}")
        raise RuntimeError(f"Failed to install pip: {result.stderr}")

    # Clean up
    get_pip_path.unlink()

    if progress_callback:
        progress_callback("pip installed successfully")

    return True


def install_requirements(python_exe: Path, requirements_file: Path, progress_callback: Optional[Callable[[str], None]] = None):
    """
    Install Python packages from requirements.txt using pip.

    Args:
        python_exe: Path to Python executable
        requirements_file: Path to requirements.txt
        progress_callback: Optional callback for status updates
    """
    if not requirements_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

    if progress_callback:
        progress_callback("Installing Python packages (this may take several minutes)...")

    print(f"Installing packages from: {requirements_file}")

    # Read requirements and filter out problematic lines
    # The sharp package is already available via PYTHONPATH (ml-sharp/src)
    # so we don't need to install it via pip
    with open(requirements_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Filter out editable install lines and comments-only lines
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip editable installs (-e), empty lines, and comment-only lines
        if stripped and not stripped.startswith('-e') and not stripped.startswith('#'):
            # Keep lines that have actual package specifications
            if not stripped.startswith('via'):  # Skip uv metadata comments
                filtered_lines.append(line)

    # Create temporary filtered requirements file
    temp_requirements = MLSHARP_ENV_DIR / "requirements_filtered.txt"
    with open(temp_requirements, 'w', encoding='utf-8') as f:
        f.writelines(filtered_lines)

    print(f"Filtered requirements (removed editable installs):")
    print(f"Original lines: {len(lines)}, Filtered lines: {len(filtered_lines)}")

    # Install packages using pip
    cmd = [
        str(python_exe),
        "-m", "pip",
        "install",
        "-r", str(temp_requirements),
        "--no-warn-script-location"
    ]

    print(f"Running: {' '.join(cmd)}")

    # Run with real-time output
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # Print output in real-time
    for line in process.stdout:
        print(line.rstrip())

    process.wait()

    # Clean up temporary file
    if temp_requirements.exists():
        temp_requirements.unlink()

    if process.returncode != 0:
        raise RuntimeError(f"Failed to install requirements. Exit code: {process.returncode}")

    if progress_callback:
        progress_callback("All packages installed successfully")

    return True


def download_checkpoint(progress_callback: Optional[Callable[[str], None]] = None):
    """
    Download ML-Sharp checkpoint file.

    Args:
        progress_callback: Optional callback for status updates
    """
    checkpoint_path = MLSHARP_DIR / CHECKPOINT_FILENAME

    if checkpoint_path.exists():
        if progress_callback:
            progress_callback(f"Checkpoint already exists: {CHECKPOINT_FILENAME}")
        return checkpoint_path

    if progress_callback:
        progress_callback("Downloading ML-Sharp checkpoint (~1.5GB)...")

    download_file(CHECKPOINT_URL, checkpoint_path)

    if progress_callback:
        progress_callback("Checkpoint downloaded successfully")

    return checkpoint_path


def get_python_executable() -> Optional[Path]:
    """Get the expected Python executable path for current platform."""
    if os.name == 'nt':  # Windows
        return MLSHARP_ENV_DIR / "python.exe"
    else:  # macOS/Linux
        return MLSHARP_ENV_DIR / "bin" / "python"


def check_environment_status():
    """
    Check the status of the ML-Sharp environment.

    Returns:
        dict: Status with keys 'python_installed', 'packages_installed', 'checkpoint_exists'
    """
    python_exe = get_python_executable()
    checkpoint_path = MLSHARP_DIR / CHECKPOINT_FILENAME

    status = {
        'python_installed': python_exe.exists() if python_exe else False,
        'packages_installed': False,
        'checkpoint_exists': checkpoint_path.exists(),
        'python_path': str(python_exe) if python_exe else "Unknown",
    }

    # Check if packages are installed by trying to import sharp
    if status['python_installed']:
        try:
            # Set up environment with ml-sharp/src in PYTHONPATH
            env = os.environ.copy()
            mlsharp_src = str(MLSHARP_DIR / "src")
            env['PYTHONPATH'] = mlsharp_src

            result = subprocess.run(
                [str(python_exe), "-c", "import sharp; import torch; import gsplat"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env
            )
            status['packages_installed'] = (result.returncode == 0)
        except:
            status['packages_installed'] = False

    return status


def install_environment_windows(progress_callback: Optional[Callable[[str], None]] = None):
    """
    Complete installation workflow for Windows.

    Args:
        progress_callback: Optional callback for status updates

    Returns:
        bool: True if successful
    """
    try:
        # Check current status
        status = check_environment_status()

        # Step 1: Install Python if needed
        if not status['python_installed']:
            if progress_callback:
                progress_callback("Step 1/3: Installing Python...")
            install_python_windows(progress_callback)
        else:
            if progress_callback:
                progress_callback("Step 1/3: Python already installed")

        python_exe = get_python_executable()

        # Step 2: Install pip and packages
        if not status['packages_installed']:
            if progress_callback:
                progress_callback("Step 2/3: Installing pip...")
            install_pip(python_exe, progress_callback)

            if progress_callback:
                progress_callback("Step 2/3: Installing Python packages...")
            requirements_file = MLSHARP_DIR / "requirements.txt"
            install_requirements(python_exe, requirements_file, progress_callback)
        else:
            if progress_callback:
                progress_callback("Step 2/3: Packages already installed")

        # Step 3: Download checkpoint
        if not status['checkpoint_exists']:
            if progress_callback:
                progress_callback("Step 3/3: Downloading checkpoint...")
            download_checkpoint(progress_callback)
        else:
            if progress_callback:
                progress_callback("Step 3/3: Checkpoint already exists")

        if progress_callback:
            progress_callback("Installation complete!")

        return True

    except Exception as e:
        if progress_callback:
            progress_callback(f"Installation failed: {str(e)}")
        raise


def install_environment(progress_callback: Optional[Callable[[str], None]] = None):
    """
    Platform-independent environment installation.

    Args:
        progress_callback: Optional callback for status updates

    Returns:
        bool: True if successful
    """
    if sys.platform == 'win32':
        return install_environment_windows(progress_callback)
    elif sys.platform == 'darwin':
        raise NotImplementedError(
            "Automatic installation not yet supported on macOS.\n"
            "Please install Python 3.13 manually and run:\n"
            f"  python -m pip install -r {MLSHARP_DIR / 'requirements.txt'}"
        )
    elif sys.platform.startswith('linux'):
        raise NotImplementedError(
            "Automatic installation not yet supported on Linux.\n"
            "Please install Python 3.13 manually and run:\n"
            f"  python -m pip install -r {MLSHARP_DIR / 'requirements.txt'}"
        )
    else:
        raise NotImplementedError(f"Unsupported platform: {sys.platform}")
