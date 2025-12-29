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

Tutorial
[![Watch the video](https://img.youtube.com/vi/pbBLFKZL080/0.jpg)](https://www.youtube.com/watch?v=pbBLFKZL080)


### Installation
<img width="657" height="258" alt="InstallFromDisk" src="https://github.com/user-attachments/assets/223d4564-ec89-4379-baeb-7797100a1cdc" />

1. Download the zip file from GitHub Releases page
2. Go to Preferences, Add-ons, Install from disk and choose the downloaded zip file

### Use
<img width="921" height="239" alt="UI_Panel" src="https://github.com/user-attachments/assets/2bb67591-66e1-4019-aaa5-4ced80bd6d13" />

1. `Environment Setup Panel` : Checking the status of installation. If all the files got installed, this panel will be gone. Just need to install once
2. `Install Environment Button` : Install all the files needed for this Add On with internet (It's self-contained. Won't affect your computer's system)
3. `Device Mode` : Choose to generate 3D scene with GPU or CPU
4. `Output Folder` : Choose the output folder for the generated 3D scene file
5. `Generate Button` : Choose an image and start generating 3D scene
6. `View Mode` : Choose to display 3D scene as Gaussian Splats or Point Clouds (need to select the object first)
7. `Update Splats Direction` : Update Gaussian Splats to face the viewport (need to select the object first)
8. `Color Adjustment` : Adjust the brightness, contrast, hue and saturation of the Gaussian Splats (need to select the object first)


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
