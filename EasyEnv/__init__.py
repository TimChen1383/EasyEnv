# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
    "name" : "EasyEnv",
    "author" : "Tim Chen", 
    "description" : "Generate environment using single image.",
    "blender" : (4, 3, 0),
    "version" : (4, 1, 4),
    "location" : "",
    "warning" : "",
    "doc_url": "", 
    "tracker_url": "", 
    "category" : "3D View" 
}


import bpy
import bpy.utils.previews
import os
import numpy as np
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix


addon_keymaps = {}
_icons = None
_env_status_cache = None
_env_status_cache_time = 0
_env_fully_installed = False  # Once True, stop checking


def property_exists(prop_path, glob, loc):
    try:
        eval(prop_path, glob, loc)
        return True
    except:
        return False


def invalidate_env_cache():
    """Force environment status to be rechecked (call after installation)"""
    global _env_status_cache, _env_status_cache_time, _env_fully_installed
    _env_status_cache = None
    _env_status_cache_time = 0
    _env_fully_installed = False


def get_cached_environment_status():
    """
    Get environment status with smart caching:
    - If fully installed: cache permanently (never check again)
    - If installing: cache for 5 seconds
    - On first load: check once
    """
    import time
    global _env_status_cache, _env_status_cache_time, _env_fully_installed

    # If we already confirmed full installation, return cached result immediately
    if _env_fully_installed and _env_status_cache is not None:
        return _env_status_cache

    current_time = time.time()

    # If not fully installed, cache for 5 seconds (for installation progress)
    if _env_status_cache is not None and (current_time - _env_status_cache_time) < 5.0:
        return _env_status_cache

    # Update cache by checking environment
    try:
        from . import env_installer
        status = env_installer.check_environment_status()
        _env_status_cache = status
        _env_status_cache_time = current_time

        # If fully installed, mark as complete and stop checking
        if status['python_installed'] and status['packages_installed'] and status['checkpoint_exists']:
            _env_fully_installed = True
            print("EasyEnv: Environment fully installed - status checking disabled")

        return status
    except Exception as e:
        print(f"EasyEnv: Error checking environment status: {e}")
        return {'python_installed': False, 'packages_installed': False, 'checkpoint_exists': False}


def load_preview_icon(path):
    global _icons
    if not path in _icons:
        if os.path.exists(path):
            _icons.load(path, path, "IMAGE")
        else:
            return 0
    return _icons[path].icon_id


def sna_update_active_object_update_mode_868D4(self, context):
    """Update handler for Active Object Update Mode property"""
    sna_updated_prop = self.active_object_update_mode
    bpy.context.view_layer.objects.active['update_rot_to_cam'] = (sna_updated_prop == 'Enable Camera Updates')
    bpy.context.view_layer.objects.active.modifiers['KIRI_3DGS_Render_GN']['Socket_50'] = (2 if (sna_updated_prop == 'Show As Point Cloud') else (1 if (sna_updated_prop != 'Enable Camera Updates') else 0))
    bpy.context.view_layer.objects.active.modifiers['KIRI_3DGS_Render_GN'].show_viewport = (True if (sna_updated_prop != 'Disable Camera Updates') else False)
    bpy.context.view_layer.objects.active.update_tag(refresh={'OBJECT'}, )
    if bpy.context and bpy.context.screen:
        for a in bpy.context.screen.areas:
            a.tag_redraw()


def sna_update_enable_active_camera_updates_DE26E(self, context):
    """Update handler for Enable Active Camera Updates property"""
    sna_updated_prop = self.enable_active_camera_updates
    if sna_updated_prop:
        bpy.context.area.spaces.active.region_3d.view_perspective = 'CAMERA'
        bpy.context.view_layer.objects.active.modifiers['KIRI_3DGS_Render_GN']['Socket_54'] = sna_updated_prop

        def delayed_214CF():
            sna_update_camera_single_time_9EF18()
        bpy.app.timers.register(delayed_214CF, first_interval=0.10000000149011612)
    else:
        bpy.context.view_layer.objects.active.modifiers['KIRI_3DGS_Render_GN']['Socket_54'] = sna_updated_prop


def sna_update_camera_single_time_9EF18():
    """Update all 3DGS objects to current camera view"""
    from mathutils import Matrix
    
    # Define helper function for updating the geometry node sockets
    def update_gaussian_splat_camera(obj, view_matrix, proj_matrix, window_width, window_height):
        geometryNodes_modifier = obj.modifiers.get('KIRI_3DGS_Render_GN')
        if not geometryNodes_modifier:
            print(f"Error: GeometryNodes modifier not found on object '{obj.name}'.")
            return False
        
        # Update view matrix
        geometryNodes_modifier['Socket_2'] = view_matrix[0][0]
        geometryNodes_modifier['Socket_3'] = view_matrix[1][0]
        geometryNodes_modifier['Socket_4'] = view_matrix[2][0]
        geometryNodes_modifier['Socket_5'] = view_matrix[3][0]
        geometryNodes_modifier['Socket_6'] = view_matrix[0][1]
        geometryNodes_modifier['Socket_7'] = view_matrix[1][1]
        geometryNodes_modifier['Socket_8'] = view_matrix[2][1]
        geometryNodes_modifier['Socket_9'] = view_matrix[3][1]
        geometryNodes_modifier['Socket_10'] = view_matrix[0][2]
        geometryNodes_modifier['Socket_11'] = view_matrix[1][2]
        geometryNodes_modifier['Socket_12'] = view_matrix[2][2]
        geometryNodes_modifier['Socket_13'] = view_matrix[3][2]
        geometryNodes_modifier['Socket_14'] = view_matrix[0][3]
        geometryNodes_modifier['Socket_15'] = view_matrix[1][3]
        geometryNodes_modifier['Socket_16'] = view_matrix[2][3]
        geometryNodes_modifier['Socket_17'] = view_matrix[3][3]
        
        # Update projection matrix
        geometryNodes_modifier['Socket_18'] = proj_matrix[0][0]
        geometryNodes_modifier['Socket_19'] = proj_matrix[1][0]
        geometryNodes_modifier['Socket_20'] = proj_matrix[2][0]
        geometryNodes_modifier['Socket_21'] = proj_matrix[3][0]
        geometryNodes_modifier['Socket_22'] = proj_matrix[0][1]
        geometryNodes_modifier['Socket_23'] = proj_matrix[1][1]
        geometryNodes_modifier['Socket_24'] = proj_matrix[2][1]
        geometryNodes_modifier['Socket_25'] = proj_matrix[3][1]
        geometryNodes_modifier['Socket_26'] = proj_matrix[0][2]
        geometryNodes_modifier['Socket_27'] = proj_matrix[1][2]
        geometryNodes_modifier['Socket_28'] = proj_matrix[2][2]
        geometryNodes_modifier['Socket_29'] = proj_matrix[3][2]
        geometryNodes_modifier['Socket_30'] = proj_matrix[0][3]
        geometryNodes_modifier['Socket_31'] = proj_matrix[1][3]
        geometryNodes_modifier['Socket_32'] = proj_matrix[2][3]
        geometryNodes_modifier['Socket_33'] = proj_matrix[3][3]
        
        # Update window dimensions
        geometryNodes_modifier['Socket_34'] = window_width
        geometryNodes_modifier['Socket_35'] = window_height
        
        return True
    
    # Find view and projection matrices from the 3D view area
    found_3d_view = False
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            view_matrix = area.spaces.active.region_3d.view_matrix
            proj_matrix = area.spaces.active.region_3d.window_matrix
            window_width = area.width
            window_height = area.height
            found_3d_view = True
            break
    
    if not found_3d_view:
        print("Error: No 3D View found in the current screen.")
        return
    
    # Update all enabled 3DGS objects
    updated_objects = []
    for obj in bpy.context.scene.objects:
        if 'update_rot_to_cam' in obj and obj['update_rot_to_cam']:
            if update_gaussian_splat_camera(obj, view_matrix, proj_matrix, window_width, window_height):
                updated_objects.append(obj.name)
    
    if updated_objects:
        print(f"Updated {len(updated_objects)} object(s): {', '.join(updated_objects)}")
    else:
        print("No enabled 3DGS objects found to update.")
    
    # Force viewport refresh
    if bpy.context and bpy.context.screen:
        for a in bpy.context.screen.areas:
            a.tag_redraw()


def sna_append_and_add_geo_nodes_function_execute_6BCD7(Node_Group_Name, Modifier_Name, Object):
    """Append geometry node group from library file and add as modifier"""
    if not property_exists(f"bpy.data.node_groups['{Node_Group_Name}']", globals(), locals()):
        before_data = list(bpy.data.node_groups)
        bpy.ops.wm.append(
            directory=os.path.join(os.path.dirname(__file__), 'assets', '3DGS Render APPEND V4.blend') + r'\NodeTree', 
            filename=Node_Group_Name, 
            link=False
        )
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.node_groups)))
        appended_65345 = None if not new_data else new_data[0]
    
    modifier = Object.modifiers.new(name=Modifier_Name, type='NODES')
    modifier.node_group = bpy.data.node_groups[Node_Group_Name]
    return modifier


class SNA_OT_Dgs_Render_Align_Active_To_View_30B13(bpy.types.Operator):
    """Update Active To View - Updates the 3DGS planes to face current viewport"""
    bl_idname = "sna.dgs_render_align_active_to_view_30b13"
    bl_label = "Update Active To View"
    bl_description = "Updates the 3DGS_Render modifier once to the current view for the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        from mathutils import Matrix
        
        # Define helper function for updating the geometry node sockets
        def update_gaussian_splat_camera(obj, view_matrix, proj_matrix, window_width, window_height):
            geometryNodes_modifier = obj.modifiers.get('KIRI_3DGS_Render_GN')
            if not geometryNodes_modifier:
                print(f"Error: GeometryNodes modifier not found on object '{obj.name}'.")
                return False
            
            # Update view matrix
            geometryNodes_modifier['Socket_2'] = view_matrix[0][0]
            geometryNodes_modifier['Socket_3'] = view_matrix[1][0]
            geometryNodes_modifier['Socket_4'] = view_matrix[2][0]
            geometryNodes_modifier['Socket_5'] = view_matrix[3][0]
            geometryNodes_modifier['Socket_6'] = view_matrix[0][1]
            geometryNodes_modifier['Socket_7'] = view_matrix[1][1]
            geometryNodes_modifier['Socket_8'] = view_matrix[2][1]
            geometryNodes_modifier['Socket_9'] = view_matrix[3][1]
            geometryNodes_modifier['Socket_10'] = view_matrix[0][2]
            geometryNodes_modifier['Socket_11'] = view_matrix[1][2]
            geometryNodes_modifier['Socket_12'] = view_matrix[2][2]
            geometryNodes_modifier['Socket_13'] = view_matrix[3][2]
            geometryNodes_modifier['Socket_14'] = view_matrix[0][3]
            geometryNodes_modifier['Socket_15'] = view_matrix[1][3]
            geometryNodes_modifier['Socket_16'] = view_matrix[2][3]
            geometryNodes_modifier['Socket_17'] = view_matrix[3][3]
            
            # Update projection matrix
            geometryNodes_modifier['Socket_18'] = proj_matrix[0][0]
            geometryNodes_modifier['Socket_19'] = proj_matrix[1][0]
            geometryNodes_modifier['Socket_20'] = proj_matrix[2][0]
            geometryNodes_modifier['Socket_21'] = proj_matrix[3][0]
            geometryNodes_modifier['Socket_22'] = proj_matrix[0][1]
            geometryNodes_modifier['Socket_23'] = proj_matrix[1][1]
            geometryNodes_modifier['Socket_24'] = proj_matrix[2][1]
            geometryNodes_modifier['Socket_25'] = proj_matrix[3][1]
            geometryNodes_modifier['Socket_26'] = proj_matrix[0][2]
            geometryNodes_modifier['Socket_27'] = proj_matrix[1][2]
            geometryNodes_modifier['Socket_28'] = proj_matrix[2][2]
            geometryNodes_modifier['Socket_29'] = proj_matrix[3][2]
            geometryNodes_modifier['Socket_30'] = proj_matrix[0][3]
            geometryNodes_modifier['Socket_31'] = proj_matrix[1][3]
            geometryNodes_modifier['Socket_32'] = proj_matrix[2][3]
            geometryNodes_modifier['Socket_33'] = proj_matrix[3][3]
            
            # Update window dimensions
            geometryNodes_modifier['Socket_34'] = window_width
            geometryNodes_modifier['Socket_35'] = window_height
            
            return True
        
        # Find view and projection matrices from the 3D view area
        found_3d_view = False
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                view_matrix = area.spaces.active.region_3d.view_matrix
                proj_matrix = area.spaces.active.region_3d.window_matrix
                window_width = area.width
                window_height = area.height
                found_3d_view = True
                break
        
        if not found_3d_view:
            self.report({'ERROR'}, "No 3D View found in the current screen.")
            return {'CANCELLED'}
        
        # Update the active object
        obj = bpy.context.view_layer.objects.active
        if obj and update_gaussian_splat_camera(obj, view_matrix, proj_matrix, window_width, window_height):
            obj.update_tag(refresh={'OBJECT'})
            if bpy.context and bpy.context.screen:
                for a in bpy.context.screen.areas:
                    a.tag_redraw()
            self.report({'INFO'}, f"Updated {obj.name} to current view")
            return {"FINISHED"}
        else:
            self.report({'ERROR'}, "Failed to update object")
            return {'CANCELLED'}

    def invoke(self, context, event):
        return self.execute(context)


class SNA_OT_Install_Environment(bpy.types.Operator):
    """Install ML-Sharp Environment - Downloads and installs Python environment and checkpoint"""
    bl_idname = "sna.install_environment"
    bl_label = "Install Environment"
    bl_description = "Download and install ML-Sharp Python environment and checkpoint file"
    bl_options = {"REGISTER"}

    _timer = None
    _thread = None
    _status_message = "Starting installation..."
    _is_running = False
    _error_message = None
    _success = False

    def modal(self, context, event):
        if event.type == 'TIMER':
            # Update UI with current status
            context.area.tag_redraw()

            # Check if installation thread is still running
            if not self._is_running:
                # Installation finished
                self.cancel(context)

                if self._success:
                    # Invalidate cache to force recheck of environment status
                    invalidate_env_cache()
                    self.report({'INFO'}, "Environment installation complete!")
                    return {'FINISHED'}
                else:
                    error_msg = self._error_message or "Unknown error"
                    self.report({'ERROR'}, f"Installation failed: {error_msg}")
                    return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def execute(self, context):
        import threading
        import sys

        # Check platform support
        if sys.platform != 'win32':
            self.report({'ERROR'}, "Automatic installation is currently only supported on Windows")
            self.report({'INFO'}, "Please install manually: see documentation")
            return {'CANCELLED'}

        # Import installer module
        try:
            from . import env_installer
        except ImportError as e:
            self.report({'ERROR'}, f"Failed to import installer: {e}")
            return {'CANCELLED'}

        # Check current status
        status = env_installer.check_environment_status()

        if status['python_installed'] and status['packages_installed'] and status['checkpoint_exists']:
            self.report({'INFO'}, "Environment is already fully installed!")
            return {'FINISHED'}

        # Define installation function to run in thread
        def install_thread():
            try:
                def progress_callback(message):
                    self._status_message = message
                    print(f"[Install] {message}")

                self._is_running = True
                env_installer.install_environment_windows(progress_callback)
                self._success = True

            except Exception as e:
                self._error_message = str(e)
                self._success = False
                import traceback
                traceback.print_exc()
            finally:
                self._is_running = False

        # Start installation in background thread
        self._thread = threading.Thread(target=install_thread, daemon=True)
        self._thread.start()

        # Set up modal timer
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.5, window=context.window)
        wm.modal_handler_add(self)

        self.report({'INFO'}, "Installing environment... This may take 10-15 minutes")
        self.report({'INFO'}, "Check the system console for progress")

        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        if self._timer:
            wm.event_timer_remove(self._timer)


class SNA_OT_Generate_Gaussians_From_Image(bpy.types.Operator, ImportHelper):
    """Generate 3DGS from Image - Uses ML-Sharp to generate Gaussian Splatting from a single image"""
    bl_idname = "sna.generate_gaussians_from_image"
    bl_label = "Generate from Image"
    bl_description = "Generate Gaussian Splatting scene from a single image using ML-Sharp"
    bl_options = {"REGISTER", "UNDO"}

    filter_glob: bpy.props.StringProperty(
        default='*.png;*.jpg;*.jpeg;*.bmp;*.tif;*.tiff',
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        from pathlib import Path
        import tempfile
        
        image_path = Path(self.filepath)
        
        # Validate input
        if not image_path.exists():
            self.report({'ERROR'}, f"Image file not found: {image_path}")
            return {'CANCELLED'}

        # Setup output directory
        addon_dir = Path(__file__).parent
        custom_export_path = context.scene.sna_generation_settings.export_path.strip()

        if custom_export_path and custom_export_path != "":
            # User specified a custom export path
            output_dir = Path(custom_export_path)
            if not output_dir.exists():
                try:
                    output_dir.mkdir(parents=True, exist_ok=True)
                    self.report({'INFO'}, f"Created export directory: {output_dir}")
                except Exception as e:
                    self.report({'ERROR'}, f"Failed to create export directory: {str(e)}")
                    return {'CANCELLED'}
        else:
            # Use default add-on output folder
            output_dir = addon_dir / "ml-sharp" / "Output"
        
        try:
            # Import the wrapper module
            from . import sharp_wrapper
            
            # Check ml-sharp environment
            env_status = sharp_wrapper.check_mlsharp_environment()
            if not env_status['available']:
                self.report({'ERROR'}, "ML-Sharp environment not available")
                self.report({'ERROR'}, env_status['message'])
                self.report({'ERROR'}, "Please ensure ml-sharp's Env folder exists")
                return {'CANCELLED'}
            
        except ImportError as e:
            self.report({'ERROR'}, f"ML-Sharp import error: {str(e)}")
            self.report({'ERROR'}, "Please ensure ml-sharp directory exists")
            return {'CANCELLED'}
        
        # Check if checkpoint exists
        checkpoint_path = addon_dir / "ml-sharp" / "sharp_2572gikvuh.pt"
        if checkpoint_path.exists():
            self.report({'INFO'}, f"Using checkpoint: {checkpoint_path.name}")
        else:
            self.report({'INFO'}, "Checkpoint not found, will download default model")
            checkpoint_path = None
        
        try:
            
            # Get device setting from scene
            device = context.scene.sna_generation_settings.device

            self.report({'INFO'}, f"Processing image: {image_path.name}")
            self.report({'INFO'}, f"Using device: {device}")
            self.report({'INFO'}, f"Output directory: {output_dir}")
            self.report({'INFO'}, f"This may take a few minutes depending on your hardware...")

            # Generate Gaussian Splatting
            output_ply = sharp_wrapper.predict_gaussians_from_image(
                image_path=image_path,
                output_path=output_dir,
                checkpoint_path=checkpoint_path,
                device=device,
                verbose=False
            )
            
            self.report({'INFO'}, f"Generated PLY file: {output_ply.name}")
            
            # Now import the generated PLY file
            if output_ply.exists():
                # Store the current filepath for the import operator
                ply_filepath = str(output_ply)
                
                # Import PLY using existing operator logic
                try:
                    bpy.ops.wm.ply_import(filepath=ply_filepath)
                except AttributeError:
                    self.report({'ERROR'}, "PLY importer not found. Ensure Blender 4.0 or later is used.")
                    return {'CANCELLED'}
                
                # Get the imported object
                imported_objects = [obj for obj in context.scene.objects if obj.select_get()]
                if not imported_objects:
                    self.report({'ERROR'}, "No objects were imported from the PLY file.")
                    return {'CANCELLED'}
                
                obj = imported_objects[0]

                # Auto-rotate imported PLY 90 degrees about X to match Blender coordinates
                import math
                try:
                    obj.rotation_mode = 'XYZ'
                    obj.rotation_euler.x += math.radians(-90)
                except Exception:
                    pass

                if obj.type != 'MESH':
                    self.report({'ERROR'}, "Imported object is not a mesh.")
                    return {'CANCELLED'}
                
                # Apply 3DGS setup (same as Import PLY operator)
                mesh = obj.data
                required_attributes = ['f_dc_0', 'f_dc_1', 'f_dc_2', 'opacity', 
                                     'scale_0', 'scale_1', 'scale_2', 
                                     'rot_0', 'rot_1', 'rot_2', 'rot_3']
                
                missing_attrs = []
                for attr_name in required_attributes:
                    if attr_name not in mesh.attributes:
                        missing_attrs.append(attr_name)
                
                if missing_attrs:
                    self.report({'ERROR'}, f"Missing 3DGS attributes: {', '.join(missing_attrs)}")
                    return {'CANCELLED'}
                
                # Set as vertex type mesh
                obj['3DGS_Mesh_Type'] = 'vert'
                
                # Create color attributes
                SH_0 = 0.28209479177387814
                point_count = len(mesh.vertices)
                
                f_dc_0_data = np.array([v.value for v in mesh.attributes['f_dc_0'].data])
                f_dc_1_data = np.array([v.value for v in mesh.attributes['f_dc_1'].data])
                f_dc_2_data = np.array([v.value for v in mesh.attributes['f_dc_2'].data])
                opacity_data = np.array([v.value for v in mesh.attributes['opacity'].data])
                
                color_data = []
                for i in range(point_count):
                    R = max(0.0, min(1.0, f_dc_0_data[i] * SH_0 + 0.5))
                    G = max(0.0, min(1.0, f_dc_1_data[i] * SH_0 + 0.5))
                    B = max(0.0, min(1.0, f_dc_2_data[i] * SH_0 + 0.5))
                    A = max(0.0, min(1.0, 1 / (1 + np.exp(-opacity_data[i]))))
                    color_data.extend([R, G, B, A])
                
                # Create Col attribute
                if 'Col' in mesh.attributes:
                    mesh.attributes.remove(mesh.attributes['Col'])
                col_attr = mesh.attributes.new(name="Col", type='FLOAT_COLOR', domain='POINT')
                col_attr.data.foreach_set("color", color_data)
                
                # Create KIRI_3DGS_Paint attribute
                if 'KIRI_3DGS_Paint' in mesh.attributes:
                    mesh.attributes.remove(mesh.attributes['KIRI_3DGS_Paint'])
                paint_attr = mesh.attributes.new(name="KIRI_3DGS_Paint", type='FLOAT_COLOR', domain='POINT')
                paint_attr.data.foreach_set("color", color_data)
                mesh.color_attributes.active_color = paint_attr
                
                # Add geometry node modifiers
                sna_append_and_add_geo_nodes_function_execute_6BCD7('KIRI_3DGS_Render_GN', 'KIRI_3DGS_Render_GN', obj)
                sna_append_and_add_geo_nodes_function_execute_6BCD7('KIRI_3DGS_Sorter_GN', 'KIRI_3DGS_Sorter_GN', obj)
                sna_append_and_add_geo_nodes_function_execute_6BCD7('KIRI_3DGS_Adjust_Colour_And_Material', 'KIRI_3DGS_Adjust_Colour_And_Material', obj)
                sna_append_and_add_geo_nodes_function_execute_6BCD7('KIRI_3DGS_Write F_DC_And_Merge', 'KIRI_3DGS_Write F_DC_And_Merge', obj)
                
                # Configure modifiers
                obj.modifiers['KIRI_3DGS_Render_GN'].show_viewport = False
                obj.modifiers['KIRI_3DGS_Adjust_Colour_And_Material'].show_viewport = True
                obj.modifiers['KIRI_3DGS_Write F_DC_And_Merge'].show_viewport = False
                obj.modifiers['KIRI_3DGS_Adjust_Colour_And_Material'].show_render = True
                obj.modifiers['KIRI_3DGS_Write F_DC_And_Merge'].show_render = False
                obj.modifiers['KIRI_3DGS_Render_GN']['Socket_50'] = 1
                
                # Set up properties
                obj['update_rot_to_cam'] = False
                obj.sna_dgs_object_properties.enable_active_camera_updates = False
                obj.sna_dgs_object_properties.active_object_update_mode = 'Enable Camera Updates'
                
                # Append and assign material
                if not property_exists("bpy.data.materials['KIRI_3DGS_Render_Material']", globals(), locals()):
                    before_data = list(bpy.data.materials)
                    bpy.ops.wm.append(
                        directory=os.path.join(os.path.dirname(__file__), 'assets', '3DGS Render APPEND V4.blend') + r'\Material',
                        filename='KIRI_3DGS_Render_Material',
                        link=False
                    )

                # Configure sorter based on material render method
                obj.modifiers['KIRI_3DGS_Sorter_GN'].show_viewport = (bpy.data.materials['KIRI_3DGS_Render_Material'].surface_render_method == 'BLENDED')
                obj.modifiers['KIRI_3DGS_Sorter_GN'].show_render = (bpy.data.materials['KIRI_3DGS_Render_Material'].surface_render_method == 'BLENDED')

                # Remove existing material slots and assign KIRI material
                while len(obj.material_slots) > 0:
                    bpy.context.view_layer.objects.active = obj
                    bpy.context.object.active_material_index = 0
                    bpy.ops.object.material_slot_remove()

                obj.data.materials.append(bpy.data.materials['KIRI_3DGS_Render_Material'])
                obj.modifiers['KIRI_3DGS_Render_GN']['Socket_61'] = bpy.data.materials['KIRI_3DGS_Render_Material']
                
                obj.name = f"3DGS_{image_path.stem}"
                
                self.report({'INFO'}, f"Successfully generated and imported Gaussian Splatting: {obj.name}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, "Failed to generate PLY file")
                return {'CANCELLED'}
                
        except ImportError as e:
            self.report({'ERROR'}, f"ML-Sharp import error: {str(e)}")
            self.report({'ERROR'}, "Please ensure ml-sharp dependencies are installed")
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error generating Gaussians: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}


class SNA_PT_DGS_RENDER_BY_KIRI_ENGINE_6D2B1(bpy.types.Panel):
    """Main panel for minimal 3DGS display"""
    bl_label = 'EasyEnv'
    bl_idname = 'SNA_PT_DGS_RENDER_BY_KIRI_ENGINE_6D2B1'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = ''
    bl_category = 'Easy Env'
    bl_order = 0
    bl_ui_units_x=0

    @classmethod
    def poll(cls, context):
        return not (False)

    def draw_header(self, context):
        layout = self.layout

    def draw(self, context):
        layout = self.layout

        # Check environment status (cached to avoid slow UI)
        status = get_cached_environment_status()
        env_ready = status['python_installed'] and status['packages_installed'] and status['checkpoint_exists']

        # Environment status section (show if not fully installed)
        if not env_ready:
            box = layout.box()
            box.label(text='Environment Setup', icon='PREFERENCES')

            col = box.column(align=True)
            if not status['python_installed']:
                col.label(text='Python: Not Installed', icon='CANCEL')
            else:
                col.label(text='Python: Installed', icon='CHECKMARK')

            if not status['packages_installed']:
                col.label(text='Packages: Not Installed', icon='CANCEL')
            else:
                col.label(text='Packages: Installed', icon='CHECKMARK')

            if not status['checkpoint_exists']:
                col.label(text='Checkpoint: Not Downloaded', icon='CANCEL')
            else:
                col.label(text='Checkpoint: Downloaded', icon='CHECKMARK')

            # Install Environment button
            row = box.row()
            row.scale_y = 1.5
            row.operator('sna.install_environment', text='Install Environment', icon='IMPORT')

            layout.separator()

        # Generate section
        box = layout.box()
        box.label(text='Generate', icon='URL')

        # Device selection
        col = box.column(align=True)
        col.prop(context.scene.sna_generation_settings, 'device', text='Device')

        # Export path selection
        col = box.column(align=True)
        col.prop(context.scene.sna_generation_settings, 'export_path', text='Output')

        # Generate button
        row = box.row()
        row.scale_y = 1.5
        row.enabled = env_ready  # Disable if environment not ready
        row.operator('sna.generate_gaussians_from_image', text='Generate PLY from Image', icon='IMAGE_DATA')

        # (Import PLY button removed)
        
        # Active object controls
        if context.view_layer.objects.active and 'update_rot_to_cam' in context.view_layer.objects.active:
            obj = context.view_layer.objects.active
            
            box = layout.box()
            box.label(text=f'Active: {obj.name}', icon='OBJECT_DATA')
            
            # Camera update mode
            col = box.column()
            col.prop(obj.sna_dgs_object_properties, 'active_object_update_mode', text='')
            
            # Update Active To View button
            if obj.sna_dgs_object_properties.active_object_update_mode != 'Disable Camera Updates':
                row = box.row()
                row.scale_y = 1.3
                icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'eye.svg')
                if os.path.exists(icon_path):
                    op = row.operator('sna.dgs_render_align_active_to_view_30b13', 
                                    text='Update Active To View',
                                    icon_value=load_preview_icon(icon_path))
                else:
                    op = row.operator('sna.dgs_render_align_active_to_view_30b13', 
                                    text='Update Active To View',
                                    icon='RESTRICT_VIEW_OFF')
            

class SNA_GROUP_sna_dgs_object_properties_group(bpy.types.PropertyGroup):
    """Property group for 3DGS object properties"""
    active_object_update_mode: bpy.props.EnumProperty(
        name='Active Object Update Mode',
        description='Controls how Gaussian Splat planes update to camera view',
        items=[
            ('Disable Camera Updates', 'Disable Camera Updates', 'Hide the Gaussian Splat display', 0, 0),
            ('Enable Camera Updates', 'Enable Camera Updates', 'Use planes to represent Gaussian Splats, facing viewport', 0, 1),
            ('Show As Point Cloud', 'Show As Point Cloud', 'Show as simple point cloud', 0, 2)
        ],
        update=sna_update_active_object_update_mode_868D4
    )
    enable_active_camera_updates: bpy.props.BoolProperty(
        name='Enable Active Camera Updates',
        description='Automatically update active object to camera view',
        default=False,
        update=sna_update_enable_active_camera_updates_DE26E
    )


class SNA_GROUP_sna_generation_settings_group(bpy.types.PropertyGroup):
    """Property group for generation settings"""
    device: bpy.props.EnumProperty(
        name="Device",
        description="Device to use for Gaussian Splatting generation",
        items=[
            ('cuda', 'GPU (CUDA)', 'Use NVIDIA GPU - fastest if available', 'MEMORY', 0),
            ('cpu', 'CPU', 'Use CPU - slower but always compatible', 'PREVIEW_RANGE', 1),
        ],
        default='cuda'
    )
    export_path: bpy.props.StringProperty(
        name="Export Path",
        description="Directory to save generated PLY files. Leave empty to use default add-on output folder",
        default="",
        subtype='DIR_PATH'
    )


def register():
    """Register addon classes and properties"""
    global _icons
    _icons = bpy.utils.previews.new()

    # Register property groups
    bpy.utils.register_class(SNA_GROUP_sna_dgs_object_properties_group)
    bpy.types.Object.sna_dgs_object_properties = bpy.props.PointerProperty(
        name='3DGS Object Properties',
        description='Properties for 3DGS objects',
        type=SNA_GROUP_sna_dgs_object_properties_group
    )

    bpy.utils.register_class(SNA_GROUP_sna_generation_settings_group)
    bpy.types.Scene.sna_generation_settings = bpy.props.PointerProperty(
        name='Generation Settings',
        description='Settings for Gaussian Splatting generation',
        type=SNA_GROUP_sna_generation_settings_group
    )

    # Register operators
    bpy.utils.register_class(SNA_OT_Dgs_Render_Align_Active_To_View_30B13)
    bpy.utils.register_class(SNA_OT_Install_Environment)
    bpy.utils.register_class(SNA_OT_Generate_Gaussians_From_Image)

    # Register UI panel
    bpy.utils.register_class(SNA_PT_DGS_RENDER_BY_KIRI_ENGINE_6D2B1)

    print("3DGS Render (Minimal) addon registered")


def unregister():
    """Unregister addon classes and properties"""
    global _icons
    bpy.utils.previews.remove(_icons)

    # Unregister UI panel
    bpy.utils.unregister_class(SNA_PT_DGS_RENDER_BY_KIRI_ENGINE_6D2B1)

    # Unregister operators
    bpy.utils.unregister_class(SNA_OT_Generate_Gaussians_From_Image)
    bpy.utils.unregister_class(SNA_OT_Install_Environment)
    bpy.utils.unregister_class(SNA_OT_Dgs_Render_Align_Active_To_View_30B13)

    # Unregister property groups
    del bpy.types.Scene.sna_generation_settings
    bpy.utils.unregister_class(SNA_GROUP_sna_generation_settings_group)

    del bpy.types.Object.sna_dgs_object_properties
    bpy.utils.unregister_class(SNA_GROUP_sna_dgs_object_properties_group)

    print("3DGS Render (Minimal) addon unregistered")


if __name__ == "__main__":
    register()
