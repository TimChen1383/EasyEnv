# 3DGS Render by KIRI Engine - Minimal Version

## Overview
This is a simplified version of the Kiri Engine Blender add-on that focuses on the essential features for displaying Gaussian Splats inside Blender.

## What Was Kept

### Essential Features
1. **Import PLY** - Import Gaussian Splatting PLY files
2. **Enable Camera Updates** - Use planes to represent Gaussian Splats that face the viewport
3. **Update Active To View** - Manually update Gaussian Splat planes to face current viewport
4. **Geometry Node System** - All functions that process point attributes and append Geometry Nodes from the library file

### Core Components
- Import PLY operator (`SNA_OT_Dgs_Render_Import_Ply_E0A3A`)
- Update Active To View operator (`SNA_OT_Dgs_Render_Align_Active_To_View_30B13`)
- Geometry node appending function (`sna_append_and_add_geo_nodes_function_execute_6BCD7`)
- Camera update system (`sna_update_camera_single_time_9EF18`)
- Object properties for camera update modes
- Simplified UI panel with only essential controls

## What Was Removed

### Removed Features
- Export functionality
- Mesh to 3DGS conversion
- HQ/LQ mode switching
- Animation modifiers
- Vertex painting
- Image overlay
- Selective color adjustments (1, 2, 3)
- Alignment to X/Y/Z axes
- Documentation and tutorial links
- Render mode
- Advanced render features
- Proxy object creation
- All modifier management UI (Crop Box, Decimate, Remove By Size, etc.)
- Camera culling
- Color editing modifiers
- Convert to rough mesh
- Higher SH attributes management
- Wire sphere/cube appending

### Removed UI Elements
- Active Mode switcher (Edit/Render/Mesh 2 3DGS)
- Edit mode sub-menus (Modifiers, Colour, Animate, HQ/LQ, Export)
- About/Links/Documentation section
- All complex modifier panels

### Removed Properties
- Scene properties (`sna_dgs_scene_properties`)
- Material properties (`sna_lq__hq`)
- Most global dictionaries
- Complex update handlers

## File Size Comparison
- **Original**: 11,385 lines
- **Minimal**: ~650 lines
- **Reduction**: ~94% smaller

## Installation

1. Copy `__init___MINIMAL.py` to replace or backup your original `__init__.py`
2. Rename `__init___MINIMAL.py` to `__init__.py`
3. Make sure the `assets` folder with geometry nodes and materials is still present
4. Restart Blender or reload the add-on

## Usage

### Import a Gaussian Splat PLY File
1. Open the side panel (press N) in 3D View
2. Go to "3DGS Render" tab
3. Click "Import PLY"
4. Select your .ply file

### Control Camera Updates
Once you have a Gaussian Splat object loaded:

1. Select the object
2. In the panel, choose one of three modes:
   - **Disable Camera Updates**: Hide the Gaussian Splat display
   - **Enable Camera Updates**: Show planes representing Gaussian Splats, facing viewport
   - **Show As Point Cloud**: Display as simple point cloud

3. When "Enable Camera Updates" is selected:
   - Click "Update Active To View" to manually update the view
   - Enable "Enable Active Camera Updates" for automatic updates

## Technical Details

### Dependencies
The minimal version still requires:
- Blender 4.3.0 or later
- NumPy (for color attribute processing)
- The `assets/3DGS Render APPEND V4.blend` file with geometry nodes and materials

### Geometry Nodes Applied
When importing a PLY file, the following geometry node groups are automatically added:
1. `KIRI_3DGS_Render_GN` - Main rendering geometry nodes
2. `KIRI_3DGS_Sorter_GN` - Sorting for proper alpha blending
3. `KIRI_3DGS_Adjust_Colour_And_Material` - Color adjustment system
4. `KIRI_3DGS_Write F_DC_And_Merge` - Writes back color data

### Material System
The material `KIRI_3DGS_Render_Material` is automatically appended and assigned to imported objects.

## Notes

- The minimal version maintains full compatibility with PLY files created by the original add-on
- All the core Gaussian Splatting display functionality is preserved
- The geometry node system remains intact
- Point attribute processing is fully functional

## Credits

Original add-on by KIRI ENGINE
Minimal version created for simplified Gaussian Splat display workflow
