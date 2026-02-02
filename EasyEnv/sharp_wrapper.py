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
) -> tuple:
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
        Tuple of (Path to generated PLY file, camera_metadata dict or None)
        Camera metadata contains: focal_length_px, width, height, cx, cy

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
from sharp.cli import main_cli
sys.exit(main_cli())
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

            # Read camera metadata BEFORE standardization (standardize removes it)
            print("Reading camera metadata from PLY...")
            camera_metadata = read_camera_metadata_from_ply(output_ply, verbose=verbose)
            if camera_metadata:
                print(f"Camera metadata extracted: {camera_metadata['width']}x{camera_metadata['height']}, "
                      f"focal={camera_metadata['focal_length_px']:.2f}px")
            else:
                print("No camera metadata found in PLY file")

            # Convert to industry-standard PLY format for compatibility
            # with Houdini, SuperSplat, and other 3DGS software
            print("Converting to industry-standard PLY format...")
            standardize_ply_format(output_ply, verbose=verbose)
            print(f"PLY format standardized: {output_ply.name}")

            return (output_ply, camera_metadata)
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


def read_camera_metadata_from_ply(ply_path: Path, verbose: bool = False) -> dict:
    """
    Read camera metadata from ML-Sharp PLY file before standardization.

    The ML-Sharp output PLY contains camera information:
    - 'intrinsic': 9 floats (3x3 matrix) = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
    - 'image_size': 2 uint32 = [width, height]

    Args:
        ply_path: Path to PLY file
        verbose: Enable verbose logging

    Returns:
        dict with keys: 'focal_length_px', 'width', 'height', 'cx', 'cy'
        Returns None if camera data not found or on error
    """
    if not MLSHARP_PYTHON.exists():
        if verbose:
            print(f"ML-Sharp Python not found: {MLSHARP_PYTHON}")
        return None

    if not ply_path.exists():
        if verbose:
            print(f"PLY file not found: {ply_path}")
        return None

    # Python code to run in ml-sharp environment (has plyfile and numpy)
    # ML-Sharp PLY structure (from gaussians.py save_ply):
    # - intrinsic element: 9 rows, each with property 'intrinsic' (f4)
    # - image_size element: 2 rows, each with property 'image_size' (u4)
    python_code = '''
import sys
import json
import numpy as np
from plyfile import PlyData

def read_camera_metadata(input_path):
    """Extract camera metadata from ML-Sharp PLY file."""

    # Read original PLY
    plydata = PlyData.read(input_path)

    # Check for intrinsic element
    if 'intrinsic' not in plydata:
        return None

    # Check for image_size element
    if 'image_size' not in plydata:
        return None

    # Access intrinsic data - each row has a single 'intrinsic' property
    # The element contains 9 rows: [fx, 0, cx, 0, fy, cy, 0, 0, 1]
    intrinsic_element = plydata['intrinsic']
    intrinsic_data = np.asarray(intrinsic_element['intrinsic'])

    if len(intrinsic_data) < 9:
        return None

    # Extract values from the 3x3 matrix stored as flat array
    fx = float(intrinsic_data[0])  # [0,0] = fx
    cx = float(intrinsic_data[2])  # [0,2] = cx
    fy = float(intrinsic_data[4])  # [1,1] = fy
    cy = float(intrinsic_data[5])  # [1,2] = cy

    # Access image_size data - each row has a single 'image_size' property
    # The element contains 2 rows: [width, height]
    image_size_element = plydata['image_size']
    image_size_data = np.asarray(image_size_element['image_size'])

    if len(image_size_data) < 2:
        return None

    width = int(image_size_data[0])
    height = int(image_size_data[1])

    # Use average of fx and fy as focal length
    focal_length_px = (fx + fy) / 2.0

    return {
        'focal_length_px': focal_length_px,
        'width': width,
        'height': height,
        'cx': cx,
        'cy': cy
    }

if __name__ == "__main__":
    input_path = sys.argv[1]

    try:
        result = read_camera_metadata(input_path)
        if result:
            print(json.dumps(result))
            sys.exit(0)
        else:
            print("null")
            sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
'''

    cmd = [
        str(MLSHARP_PYTHON),
        "-c", python_code,
        str(ply_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        output = result.stdout.strip()
        if output and output != "null":
            import json
            metadata = json.loads(output)
            if verbose:
                print(f"Camera metadata: focal_length={metadata['focal_length_px']:.2f}px, "
                      f"size={metadata['width']}x{metadata['height']}")
            return metadata
        else:
            if verbose:
                print("No camera metadata found in PLY file")
            return None

    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"Failed to read camera metadata: {e.stderr}")
        return None
    except Exception as e:
        if verbose:
            print(f"Error reading camera metadata: {e}")
        return None


def standardize_ply_format(ply_path: Path, verbose: bool = False) -> bool:
    """
    Convert ML-Sharp PLY format to industry-standard 3DGS PLY format.

    This function:
    1. Removes non-standard elements (extrinsic, intrinsic, etc.)
    2. Reorders properties to standard order
    3. Converts quaternions from WXYZ (ML-Sharp) to XYZW (industry standard)
    4. Filters out any NaN/Infinity values

    Args:
        ply_path: Path to PLY file to standardize (modified in-place)
        verbose: Enable verbose logging

    Returns:
        bool: True if successful

    Raises:
        RuntimeError: If standardization fails
    """
    if not MLSHARP_PYTHON.exists():
        raise FileNotFoundError(f"ML-Sharp Python not found: {MLSHARP_PYTHON}")

    if not ply_path.exists():
        raise FileNotFoundError(f"PLY file not found: {ply_path}")

    # Python code to run in ml-sharp environment (has plyfile and numpy)
    python_code = '''
import sys
import numpy as np
from plyfile import PlyData, PlyElement

def standardize_ply(input_path, output_path):
    """Convert ML-Sharp PLY to industry-standard format."""

    # Read original PLY
    plydata = PlyData.read(input_path)

    # Get vertex data
    if 'vertex' not in plydata:
        raise ValueError("PLY file has no vertex element")

    vertex = plydata['vertex']
    data = vertex.data
    num_points = len(data)

    if num_points == 0:
        raise ValueError("PLY file has no vertices")

    # Check required properties exist
    required = ['x', 'y', 'z', 'f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity',
                'scale_0', 'scale_1', 'scale_2', 'rot_0', 'rot_1', 'rot_2', 'rot_3']

    available_props = list(data.dtype.names)
    missing = [p for p in required if p not in available_props]
    if missing:
        raise ValueError(f"Missing required properties: {missing}")

    # Filter out NaN/Infinity values
    valid_mask = np.ones(num_points, dtype=bool)
    for prop in required:
        valid_mask &= np.isfinite(data[prop])

    filtered_data = data[valid_mask]
    num_valid = len(filtered_data)
    num_removed = num_points - num_valid

    if num_valid == 0:
        raise ValueError("All vertices contain NaN/Infinity values")

    # Define industry-standard property order
    dtype_standard = [
        ('x', '<f4'), ('y', '<f4'), ('z', '<f4'),
        ('scale_0', '<f4'), ('scale_1', '<f4'), ('scale_2', '<f4'),
        ('rot_0', '<f4'), ('rot_1', '<f4'), ('rot_2', '<f4'), ('rot_3', '<f4'),
        ('f_dc_0', '<f4'), ('f_dc_1', '<f4'), ('f_dc_2', '<f4'),
        ('opacity', '<f4'),
    ]

    # Create new structured array with standard order
    new_data = np.empty(num_valid, dtype=dtype_standard)

    # Copy position, scale, color, opacity as-is
    for prop in ['x', 'y', 'z', 'scale_0', 'scale_1', 'scale_2',
                 'f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity']:
        new_data[prop] = filtered_data[prop]

    # Convert quaternion from WXYZ (ML-Sharp) to XYZW (industry standard)
    # ML-Sharp: rot_0=w, rot_1=x, rot_2=y, rot_3=z
    # Standard: rot_0=x, rot_1=y, rot_2=z, rot_3=w
    new_data['rot_0'] = filtered_data['rot_1']  # x
    new_data['rot_1'] = filtered_data['rot_2']  # y
    new_data['rot_2'] = filtered_data['rot_3']  # z
    new_data['rot_3'] = filtered_data['rot_0']  # w

    # Create clean PLY with only vertex element
    vertex_element = PlyElement.describe(new_data, 'vertex')
    clean_ply = PlyData([vertex_element], text=False)
    clean_ply.write(output_path)

    return num_valid, num_removed

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    verbose = len(sys.argv) > 3 and sys.argv[3] == "-v"

    try:
        num_valid, num_removed = standardize_ply(input_path, output_path)
        if verbose:
            print(f"Standardized PLY: {num_valid} vertices")
            if num_removed > 0:
                print(f"Removed {num_removed} invalid vertices (NaN/Infinity)")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
'''

    # Create a temporary file for the standardized output
    temp_output = ply_path.with_suffix('.ply.tmp')

    cmd = [
        str(MLSHARP_PYTHON),
        "-c", python_code,
        str(ply_path),
        str(temp_output)
    ]

    if verbose:
        cmd.append("-v")
        print(f"Standardizing PLY format: {ply_path.name}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )

        if verbose and result.stdout:
            print(result.stdout.strip())

        # Replace original file with standardized version
        if temp_output.exists():
            import shutil
            shutil.move(str(temp_output), str(ply_path))
            return True
        else:
            raise RuntimeError("Standardized PLY file was not created")

    except subprocess.CalledProcessError as e:
        # Clean up temp file if it exists
        if temp_output.exists():
            temp_output.unlink()

        error_msg = f"PLY standardization failed with exit code {e.returncode}\n"
        if e.stdout:
            error_msg += f"Output: {e.stdout}\n"
        if e.stderr:
            error_msg += f"Error: {e.stderr}"
        raise RuntimeError(error_msg)

    except Exception as e:
        # Clean up temp file if it exists
        if temp_output.exists():
            temp_output.unlink()
        raise RuntimeError(f"Unexpected error during PLY standardization: {e}")
