import os, glob, napari, tifffile
from pathlib import Path
from IXNexplorerGUI import IXNexplorerGUI
import importlib

# data_path = '/Users/ajitj/Google Drive/My Drive/ImageAnalysis/IXNexplore/data/'
# data_path = Path('I:/Soubhagyalaxmi_Jema/20240516_eSAC-HeLa HT1080 U2OS/2024-05-16/20268')
data_path = Path('/Volumes/Shared3/CDB-IXN-Share/Joglekar_Lab/Soubhagyalaxmi_Jema/20240516_eSAC-HeLa HT1080 U2OS/2024-05-16/20268')
viewer = napari.Viewer()
IXNexplorer = IXNexplorerGUI(data_path, viewer)
viewer.window.add_dock_widget(IXNexplorer)