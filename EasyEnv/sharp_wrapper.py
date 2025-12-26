"""
ML-Sharp wrapper for Blender integration.
This module uses ml-sharp's embedded Python environment via subprocess.
This avoids modifying Blender's Python installation.
"""

import os
import sys
import subprocess
from pathlib import Path

ADDON_DIR = Path(__file__).parent
MLSHARP_DIR = ADDON_DIR / "ml-sharp"
MLSHARP_ENV_DIR = MLSHARP_DIR / "Env"

# Detect ml-sharp's embedded Python executable
if os.name == 'nt':  # Windows
    MLSHARP_PYTHON = MLSHARP_ENV_DIR / "python.exe"
else:  # macOS/Linux
    MLSHARP_PYTHON = MLSHARP_ENV_DIR / "bin" / "python"


def predict_gaussians_from_image(
    image_path: Path,
    output_path: Path,
    checkpoint_path: Path = None,
    device: str = "default",
    verbose: bool = False
) -> Path:
    """
    Generate Gaussian Splatting PLY file from a single image.
    Uses ml-sharp's embedded Python environment via subprocess.
    
    Args:
        image_path: Path to input image
        output_path: Directory to save output PLY file
        checkpoint_path: Path to model checkpoint (optional, will download if not provided)
        device: Device to use ('cpu', 'cuda', 'mps', or 'default')
        verbose: Enable verbose logging
    
    Returns:
        Path to generated PLY file
    
    Raises:
        FileNotFoundError: If input image or ml-sharp Python not found
        RuntimeError: If prediction fails
    """
    
    # Validate ml-sharp Python exists
    if not MLSHARP_PYTHON.exists():
        raise FileNotFoundError(
            f"ML-Sharp embedded Python not found at: {MLSHARP_PYTHON}\n"
            f"Expected location: {MLSHARP_ENV_DIR}\n"
            "Please ensure ml-sharp's Env folder is present."
        )
    
    # Validate input
    if not image_path.exists():
        raise FileNotFoundError(f"Input image not found: {image_path}")
    
    # Create output directory
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Check for checkpoint
    if checkpoint_path is None:
        bundled_checkpoint = MLSHARP_DIR / "sharp_2572gikvuh.pt"
        if bundled_checkpoint.exists():
            checkpoint_path = bundled_checkpoint
    
    # Build command
    # Note: Windows embeddable Python often ignores PYTHONPATH, so we need to
    # modify sys.path at runtime using a wrapper script approach
    mlsharp_src = str(MLSHARP_DIR / "src")

    # Create inline Python code that adds src to path and runs sharp.cli
    python_code = f"""
import sys
sys.path.insert(0, {repr(mlsharp_src)})
from sharp.cli import main
sys.exit(main())
"""

    # Build command with arguments for sharp CLI
    cmd = [
        str(MLSHARP_PYTHON),
        "-c", python_code,
        "predict",
        "-i", str(image_path),
        "-o", str(output_path),
        "--device", device
    ]

    if checkpoint_path:
        cmd.extend(["-c", str(checkpoint_path)])

    if verbose:
        cmd.append("-v")

    # Still set PYTHONPATH as backup (works on some systems)
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = mlsharp_src + os.pathsep + env['PYTHONPATH']
    else:
        env['PYTHONPATH'] = mlsharp_src
    
    # Run ml-sharp prediction
    print(f"Running ML-Sharp with embedded Python: {MLSHARP_PYTHON.name}")
    print(f"Processing: {image_path.name}")
    print(f"Output directory: {output_path}")
    if verbose:
        print(f"Command: {' '.join(cmd)}")
        print(f"PYTHONPATH: {env['PYTHONPATH']}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=str(MLSHARP_DIR),
            env=env  # Pass the modified environment
        )
        
        if verbose:
            print("=== ML-Sharp Output ===")
            print(result.stdout)
        
        # Find generated PLY file
        output_ply = output_path / f"{image_path.stem}.ply"
        
        if output_ply.exists():
            print(f"Successfully generated: {output_ply.name}")
            return output_ply
        else:
            raise RuntimeError(f"Expected output PLY not found: {output_ply}")
            
    except subprocess.CalledProcessError as e:
        error_msg = f"ML-Sharp prediction failed with exit code {e.returncode}\n"
        error_msg += f"Command: {' '.join(cmd)}\n"
        if e.stdout:
            error_msg += f"Output: {e.stdout}\n"
        if e.stderr:
            error_msg += f"Error: {e.stderr}"
        raise RuntimeError(error_msg)
    except Exception as e:
        raise RuntimeError(f"Unexpected error during prediction: {e}")


def check_mlsharp_environment():
    """
    Check if ml-sharp embedded Python environment is properly set up.
    
    Returns:
        dict: Status information with keys 'available', 'python_path', 'message'
    """
    status = {
        'available': False,
        'python_path': str(MLSHARP_PYTHON),
        'message': ''
    }
    
    if not MLSHARP_PYTHON.exists():
        status['message'] = f"ML-Sharp Python not found at: {MLSHARP_PYTHON}"
        return status
    
    # Try to run a simple command to verify it works
    try:
        result = subprocess.run(
            [str(MLSHARP_PYTHON), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            status['available'] = True
            status['message'] = f"ML-Sharp environment ready: {result.stdout.strip()}"
        else:
            status['message'] = "ML-Sharp Python found but not responding correctly"
            
    except Exception as e:
        status['message'] = f"Error checking ML-Sharp environment: {e}"
    
    return status


def verify_sharp_package():
    """
    Verify that sharp package is available in ml-sharp environment.
    
    Returns:
        bool: True if sharp package is available
    """
    if not MLSHARP_PYTHON.exists():
        return False
    
    try:
        result = subprocess.run(
            [str(MLSHARP_PYTHON), "-c", "import sharp; print(sharp.__file__)"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except:
        return False
