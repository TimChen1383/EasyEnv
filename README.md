# EasyEnv
EasyEnv is a Blender Add On which can generate 3D gaussain splatting environment based on a single image. Leverage the technique from ml-sharp (from Apple) and 3DGS Render (from Kiri Engine). 

(put some sample result here)


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

(add tutorial video here)

### Installation
1. Download the zip file from GitHub Realses page 

### Use
<img width="921" height="239" alt="UI_Panel" src="https://github.com/user-attachments/assets/2bb67591-66e1-4019-aaa5-4ced80bd6d13" />

1. `Environment Checking Panel` : Checking the status of installation. If all the files got installed, this panel will be gone
2. `Install Environment Button` : Install all the files needed for this Add On with internet (It's self-contained. Won't affect your computer's system)
3. `Device Mode` : Choose to generate 3D scene with GPU or CPU
4. `Output Folder` : Choose the output folder for the generated 3D scene file
5. `Generate Button` : Choose an image and start generating 3D scene
6. `View Mode` : Choose to display 3D scene as Gaussian Splats or Point Clouds (need to select the object first)
7. `Update Splats Direction` : Update Gaussian Splats to face the viewport (need to select the object first)
8. `Color Adjustment` : Adjust the brightness, contrast, hue and saturation of the Gaussian Splats (need to select the object first)


## Manual Installation
- If your Blender does not have access to the internet, you can manually download the whole file, place it in Blender's Extensions folder and skip the installation process
- For example, extract the EasyEnv file from the zip file and place it in this folder : C:\Users\TimChen\AppData\Roaming\Blender Foundation\Blender\4.3\extensions\user_default (use your own Blender extension path)
- After place the entire file in Blender's Extensions folder, enable 
- Full ZIP file link (10GB) :

![folder](https://github.com/user-attachments/assets/2b442f18-2db5-4bbe-a0dc-3673a25b0d59)
![EnableAddOn](https://github.com/user-attachments/assets/3e40f3a5-89ee-445b-9837-0d01bee5d097)

