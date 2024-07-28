import os, glob, napari, tifffile
from pathlib import Path
from IXNexplorerGUI import IXNexplorerGUI
import importlib

# data_path = '/Users/ajitj/Google Drive/My Drive/ImageAnalysis/IXNexplore/data/'
# data_path = Path('I:/Soubhagyalaxmi_Jema/20240516_eSAC-HeLa HT1080 U2OS/2024-05-16/20268')
path_str = '/Volumes/Joglekar_Lab/Anish_Virdi/20240727-pPA130-pPS131-pPS-137-doxdosage/AB-041122/2024-07-25/20284'
viewer = napari.Viewer()
IXNexplorer = IXNexplorerGUI(Path(path_str), viewer)
viewer.window.add_dock_widget(IXNexplorer)
