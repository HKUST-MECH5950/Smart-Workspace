# Smart-Workspace
MECH5950 Group 3 

## Arduino
This project is using [PlatformIO IDE](https://platformio.org/) for an easier code management.
To use the code, install VScode editor and install the PlatfromIO IDE plug-in. 
After that, create a new Arduino UNO R3 project and copy the lib and src folder to the project floder.

## User interface
The user interface are coded using python. For easy environment management, installing [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html) or [miniconda](https://docs.anaconda.com/miniconda/install/) is suggested.
After install conda or miniconda, run following to install necessary **_Python_** library using conda.
```
conda env create -f ./User_interface/environment.yml
```
To start the user interface, run following.
```
conda activative MECH5950
python ./User_interface/main.py
```

## AI module
To run the AI module, pytorch and scipy are required. Run following to install the library using conda.
### Scipy:
```
conda install anaconda::scipy
```
### Pytorch:
```
# -- cpu version --
conda install pytorch torchvision torchaudio cpuonly -c pytorch
# -- or --
# -- gpu version --
conda install pytorch torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia
```
> [!IMPORTANT]
> **You may need to change the pytorch-cuda version depend on your machine's cuda version**
