# EasyEnv
EasyEnv is a Blender Add On which can generate 3D gaussain splatting environment based on a single image. Leverage the technique of ml-sharp (from Apple) and 3DGS Render (from Kiri Engine). 

![Examples](https://github.com/user-attachments/assets/a85b0244-0f98-47ce-b5ba-00616bfd864a)


## Prerequisite
```diff
Although the Add On support CPU, still highly recommend using GPU for faster 3D scene generation
```
- ***Tested Platform*** : Windows
- ***Blender Version*** : 4.3 and above (4.4, 4.5, 5.0...)
- ***Full File Size*** : 10GB (after all files got downloaded)
- ***Suggested GPU*** : NVIDIA RTX series or GTX 16 series or newer (Tested on RTX 2070)
- ***Suggested GPU drivers*** : NVIDIA driver version 525.60.13 or newer (for CUDA 12.x support)
- ***Suggested Blender Render*** : EEVEE


## Installation & Use

Video tutorial

[![Watch the video](https://img.youtube.com/vi/pbBLFKZL080/0.jpg)](https://www.youtube.com/watch?v=pbBLFKZL080)


### Installation
<img width="657" height="258" alt="InstallFromDisk" src="https://github.com/user-attachments/assets/223d4564-ec89-4379-baeb-7797100a1cdc" />

1. Download the zip file from GitHub Releases page
2. Go to Preferences, Add-ons, Install from disk and choose the downloaded zip file

### Use

<img width="804" height="239" alt="EasyEnv_UI" src="https://github.com/user-attachments/assets/f49d0928-6039-4af1-b91a-b97aedd78638" />

***Environment Setup Panel***

1. `Environment Setup Panel` : Checking the status of installation. If all the files got installed, this panel will be gone. Just need to install once
2. `Install Environment Button` : Install all the files needed for this Add On with internet (It's self-contained. Won't affect your computer's system)

***Generate Panel***

3. `Device Mode` : Choose to generate 3D scene with GPU or CPU
4. `Output Folder` : Choose the output folder for the generated 3D scene file (.ply)
5. `Create Camera Checkbox` : Create the camera of original input image when generating 3D scene. `Set Render Resolution Checkbox` : Set the render resolution to match with original input image
6. `Generate PLY Button` : Choose an input image and start generating 3D scene
7. `Import PLY Button` : Import the existing Gaussian Splatting 3D scene file (.ply) into the scene

***Adjustment Panel***

8. `View Mode` : Choose to display 3D scene as Gaussian Splats or Point Clouds (need to select the object first)
9. `Update Splats Direction` : Update Gaussian Splats to face the viewport (need to select the object first)
10. `Color Adjustment` : Adjust the brightness, contrast, hue and saturation of the Gaussian Splats (need to select the object first)


## Input Image
- `Supported Input Image Format` : .jpg, .png
- `Camera Metadata(EXIF)` : If the input image includes camera metadata, the created camera in Blender will try to match it's focal length, width and height. Otherwise it will use default focal length(35mm). Make sure to check the `Create Camera Checkbox` and `Set Render Resolution Checkbox` if you want to create the camera and set render resolution automatically when generating 3D scene
- Some example images with camera metadata: https://pixelpeeper.com/photos
<img width="363" height="509" alt="metadata" src="https://github.com/user-attachments/assets/da6b29a9-e5c4-451f-99cb-2ca461071c23" />


## Manual Installation
- If your Blender does not have access to the internet, you can manually download the whole file, place it in Blender's Extensions folder and skip the installation process
- For example, extract the EasyEnv file from the zip file and place it in this folder : `C:\Users\TimChen\AppData\Roaming\Blender Foundation\Blender\4.3\extensions\user_default` (use your own Blender extension path)
- After place the entire file in Blender's Extensions folder, enable the Add On through the Add On panel
- Full size ZIP file link : https://drive.google.com/drive/folders/1c8wVdXtA7EKcuABRp-QfWXXhxgiCUVrK?usp=sharing
```diff
-Sometimes the Environment Setup Panel may show up with python packages not found if we place the folder manually. Just close Blender and open again
```

<img width="639" height="144" alt="placeinfolder" src="https://github.com/user-attachments/assets/0a7cbebe-142c-48b7-b495-f6ad87266d90" />

![EnableAddOn](https://github.com/user-attachments/assets/3e40f3a5-89ee-445b-9837-0d01bee5d097)

## Acknowledgments
- ml-sharp (Sharp Monocular View Synthesis in Less Than a Second) by Apple Inc. : https://github.com/apple/ml-sharp?tab=readme-ov-file
- 3DGS Render Blender Addon by Kiri Engine : https://github.com/Kiri-Innovation/3dgs-render-blender-addon?tab=readme-ov-file
