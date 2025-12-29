"""
Environment installer for EasyEnv add-on.
Downloads and sets up the ML-Sharp Python environment and checkpoint.
"""

import os
import sys
import subprocess
import zipfile
import shutil
from pathlib import Path
from typing import Optional, Callable


ADDON_DIR = Path(__file__).parent
MLSHARP_DIR = ADDON_DIR / "ml-sharp"
MLSHARP_ENV_DIR = MLSHARP_DIR / "Env"
BUNDLED_PYTHON_DIR = MLSHARP_DIR / "python_embedded"  # Bundled Python in GitHub

# Python download URLs (embeddable packages) - fallback if not bundled
PYTHON_DOWNLOADS = {
    'win32': 'https://www.python.org/ftp/python/3.13.0/python-3.13.0-embed-amd64.zip',
    'darwin': None,  # macOS uses full installer
    'linux': None,   # Linux uses system Python or manual setup
}

# Bundled files (included in GitHub repo to avoid download issues)
BUNDLED_PYTHON_ZIP = BUNDLED_PYTHON_DIR / "python-3.13.0-embed-amd64.zip"
BUNDLED_GET_PIP = BUNDLED_PYTHON_DIR / "get-pip.py"

# Checkpoint URL (too large to bundle, must download)
CHECKPOINT_URL = "https://huggingface.co/TimChen/ml-sharp/resolve/main/sharp_2572gikvuh.pt?download=true"
CHECKPOINT_FILENAME = "sharp_2572gikvuh.pt"
CHECKPOINT_EXPECTED_SIZE = 2809738232  # 2.6168 GB - exact file size for validation


def download_file(url: str, destination: Path, progress_callback: Optional[Callable[[int, int], None]] = None):
    """
    Download a file with progress tracking using requests library.
    Uses requests instead of urllib to avoid SSL/firewall issues.

    Args:
        url: URL to download from
        destination: Path to save file to
        progress_callback: Optional callback(downloaded_bytes, total_bytes)
    """
    destination.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading: {url}")
    print(f"Destination: {destination}")

    try:
        # Import requests (bundled with Blender)
        import requests
        print("Using requests library for download")

        # Try to import certifi for better SSL verification
        try:
            import certifi
            verify_ssl = certifi.where()
            print("Using certifi for SSL verification")
        except ImportError:
            verify_ssl = True  # Use default verification
            print("Using default SSL verification")

        # Stream download to handle large files
        with requests.get(url, stream=True, verify=verify_ssl, timeout=30) as response:
            response.raise_for_status()

            # Get total file size
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            block_size = 8192  # 8KB chunks

            # Download in chunks and write to file
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Report progress
                        if progress_callback:
                            progress_callback(downloaded, total_size)

                        if total_size > 0:
                            percent = min(100, (downloaded / total_size) * 100)
                            mb_downloaded = downloaded / (1024 * 1024)
                            mb_total = total_size / (1024 * 1024)
                            print(f"\rDownloading: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')

        print("\nDownload complete!")
        return True

    except ImportError:
        print("Error: requests library not found in Blender")
        print("Falling back to basic download without progress...")
        # Fallback: simple download without progress tracking
        import urllib.request
        try:
            urllib.request.urlretrieve(url, destination)
            print("Download complete!")
            return True
        except Exception as e:
            print(f"Download failed: {e}")
            if destination.exists():
                destination.unlink()
            raise

    except Exception as e:
        print(f"\nDownload failed: {e}")
        if destination.exists():
            destination.unlink()
        raise


def install_python_windows(progress_callback: Optional[Callable[[str], None]] = None):
    """
    Install embeddable Python for Windows.
    First tries to use bundled Python (from GitHub repo), then downloads if needed.

    Args:
        progress_callback: Optional callback for status updates
    """
    # Check if Python is bundled in the repo
    if BUNDLED_PYTHON_ZIP.exists():
        if progress_callback:
            progress_callback("Using bundled Python 3.13 (no download needed)...")
        print(f"Found bundled Python at: {BUNDLED_PYTHON_ZIP}")
        python_zip = BUNDLED_PYTHON_ZIP
        cleanup_zip = False  # Don't delete bundled file
    else:
        if progress_callback:
            progress_callback("Downloading Python 3.13 for Windows...")
        print("Bundled Python not found, downloading...")

        # Download embeddable Python
        python_zip = MLSHARP_DIR / "python_embed.zip"
        download_file(PYTHON_DOWNLOADS['win32'], python_zip)
        cleanup_zip = True  # Delete downloaded file after extraction

    if progress_callback:
        progress_callback("Extracting Python...")

    # Extract to Env directory
    MLSHARP_ENV_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(python_zip, 'r') as zip_ref:
        zip_ref.extractall(MLSHARP_ENV_DIR)

    # Clean up zip only if we downloaded it
    if cleanup_zip:
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
    First tries to use bundled get-pip.py, then downloads if needed.

    Args:
        python_exe: Path to Python executable
        progress_callback: Optional callback for status updates
    """
    if progress_callback:
        progress_callback("Installing pip...")

    # Check if get-pip.py is bundled in the repo
    if BUNDLED_GET_PIP.exists():
        print(f"Found bundled get-pip.py at: {BUNDLED_GET_PIP}")
        # Copy bundled file to Env directory
        get_pip_path = MLSHARP_ENV_DIR / "get-pip.py"
        shutil.copy(BUNDLED_GET_PIP, get_pip_path)
        cleanup_pip = True  # Delete copy after use
    else:
        # Download get-pip.py
        get_pip_url = "https://bootstrap.pypa.io/get-pip.py"
        get_pip_path = MLSHARP_ENV_DIR / "get-pip.py"

        print("Downloading get-pip.py...")
        download_file(get_pip_url, get_pip_path)
        cleanup_pip = True

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

    # Clean up copy
    if cleanup_pip and get_pip_path.exists():
        get_pip_path.unlink()

    if progress_callback:
        progress_callback("pip installed successfully")

    return True


def install_setuptools(python_exe: Path, progress_callback: Optional[Callable[[str], None]] = None):
    """
    Install setuptools and wheel before installing other packages.
    These are required to build packages from source (e.g., MarkupSafe).

    Args:
        python_exe: Path to Python executable
        progress_callback: Optional callback for status updates
    """
    if progress_callback:
        progress_callback("Installing build tools (setuptools, wheel)...")

    print("Installing setuptools and wheel (required for building packages from source)...")

    cmd = [
        str(python_exe),
        "-m", "pip",
        "install",
        "setuptools",
        "wheel",
        "--no-warn-script-location"
    ]

    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"Build tools installation output: {result.stdout}")
        print(f"Build tools installation errors: {result.stderr}")
        raise RuntimeError(f"Failed to install setuptools and wheel: {result.stderr}")

    if progress_callback:
        progress_callback("Build tools installed successfully")

    return True


def install_pytorch_cuda_windows(python_exe: Path, progress_callback: Optional[Callable[[str], None]] = None):
    """
    Install PyTorch with CUDA support on Windows.
    The standard requirements.txt has Linux-only CUDA markers, so we need to
    install PyTorch separately using the official PyTorch index.

    Args:
        python_exe: Path to Python executable
        progress_callback: Optional callback for status updates
    """
    if progress_callback:
        progress_callback("Installing PyTorch with CUDA support for Windows...")

    print("Installing PyTorch 2.8.0 with CUDA 12.8 support...")

    # Install PyTorch with CUDA from official PyTorch index
    # This installs torch, torchvision, and all CUDA dependencies
    cmd = [
        str(python_exe),
        "-m", "pip",
        "install",
        "torch==2.8.0",
        "torchvision==0.23.0",
        "--index-url", "https://download.pytorch.org/whl/cu128",
        "--no-warn-script-location"
    ]

    print(f"Running: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding='utf-8',
        errors='replace',  # Replace invalid UTF-8 bytes instead of crashing
        bufsize=1,
        universal_newlines=True
    )

    for line in process.stdout:
        print(line.rstrip())

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(f"Failed to install PyTorch with CUDA. Exit code: {process.returncode}")

    if progress_callback:
        progress_callback("PyTorch with CUDA installed successfully")

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

    # Filter out editable install lines, comments-only lines, and packages we handle separately
    filtered_lines = []
    packages_to_skip = ['torch', 'torchvision']  # Installed separately with CUDA on Windows

    for line in lines:
        stripped = line.strip()
        # Skip editable installs (-e), empty lines, and comment-only lines
        if stripped and not stripped.startswith('-e') and not stripped.startswith('#'):
            # Skip torch/torchvision (handled separately) and uv metadata
            if not stripped.startswith('via'):
                # Check if line starts with a package we want to skip
                package_name = stripped.split('==')[0].split(';')[0].strip()
                if package_name not in packages_to_skip:
                    filtered_lines.append(line)
                else:
                    print(f"Skipping {package_name} (installed separately with CUDA)")

    # Create temporary filtered requirements file
    temp_requirements = MLSHARP_ENV_DIR / "requirements_filtered.txt"
    with open(temp_requirements, 'w', encoding='utf-8') as f:
        f.writelines(filtered_lines)

    print(f"Filtered requirements (removed editable installs and torch packages):")
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
        encoding='utf-8',
        errors='replace',  # Replace invalid UTF-8 bytes instead of crashing
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


def is_checkpoint_complete() -> bool:
    """
    Check if the checkpoint file is fully downloaded by validating both existence and file size.

    Returns:
        bool: True if checkpoint exists and has the expected file size, False otherwise
    """
    checkpoint_path = MLSHARP_DIR / CHECKPOINT_FILENAME

    # First check if file exists
    if not checkpoint_path.exists():
        return False

    # Check if file size matches expected size (prevents false positive during download)
    try:
        actual_size = checkpoint_path.stat().st_size
        return actual_size == CHECKPOINT_EXPECTED_SIZE
    except OSError:
        # File might be locked or inaccessible during download
        return False


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

    status = {
        'python_installed': python_exe.exists() if python_exe else False,
        'packages_installed': False,
        'checkpoint_exists': is_checkpoint_complete(),
        'python_path': str(python_exe) if python_exe else "Unknown",
    }

    # Check if packages are installed by trying to import core dependencies
    # Note: We don't check for 'sharp' here because it's not installed via pip,
    # it's loaded from ml-sharp/src/ via PYTHONPATH at runtime
    if status['python_installed']:
        try:
            # Check for core dependencies (torch and gsplat are the main ones)
            # Note: torch can take 20+ seconds to import the first time, especially with CUDA
            result = subprocess.run(
                [str(python_exe), "-c", "import torch; import gsplat; print('OK')"],
                capture_output=True,
                text=True,
                timeout=30  # Increased from 10 to 30 seconds for first-time import
            )
            status['packages_installed'] = (result.returncode == 0 and 'OK' in result.stdout)

            # Check CUDA availability (optional - just for info)
            if status['packages_installed']:
                try:
                    cuda_check = subprocess.run(
                        [str(python_exe), "-c", "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')"],
                        capture_output=True,
                        text=True,
                        timeout=30  # Increased from 10 to 30 seconds for first-time import
                    )
                    if cuda_check.returncode == 0:
                        status['cuda_available'] = 'CUDA' in cuda_check.stdout
                    else:
                        status['cuda_available'] = False
                except Exception:
                    status['cuda_available'] = False
        except Exception as e:
            print(f"Package check failed: {e}")
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

            # Install build tools first (required for building packages from source)
            if progress_callback:
                progress_callback("Step 2/3: Installing build tools...")
            install_setuptools(python_exe, progress_callback)

            # Install PyTorch with CUDA support (Windows-specific)
            if progress_callback:
                progress_callback("Step 2/3: Installing PyTorch with CUDA...")
            install_pytorch_cuda_windows(python_exe, progress_callback)

            # Then install remaining packages from requirements.txt
            if progress_callback:
                progress_callback("Step 2/3: Installing remaining packages...")
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
