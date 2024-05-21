import os, sys, subprocess, napari, tifffile, re
from pathlib import Path
from importlib import reload
import numpy as np
from magicgui import magicgui, widgets
from magicclass import magicclass, MagicTemplate
from magicclass.widgets import PushButton,TextEdit, LineEdit, ComboBox, ProgressBar
from magicclass import field, FieldGroup, vfield
from napari.types import ImageData, ArrayLike, LayerDataTuple
from typing import List, Dict
from IXNexplorer import retrieveIXNInfo, retrieveMetaData
from magicclass.utils import thread_worker


@magicclass
class IXNexplorerGUI(MagicTemplate):

    @magicclass(layout="vertical")
    class Frame1:
        w1_channel = field(LineEdit, options={'value': "phase"})
        w2_channel = field(LineEdit, options={'value': "GFP"})
        w3_channel = field(LineEdit, options={'value': "mCherry"})
        w4_channel = field(LineEdit, options={'value': "Cy5"})
    
    @magicclass(layout="horizontal")
    class Frame2:
        well_select   = field(ComboBox, options={'choices': ['A1','A2']})
        posi_select   = field(ComboBox, options={'choices': ['S1','S2']})
    
    @magicclass(layout="vertical")
    class Frame4:
        save_path = field(LineEdit, options={'value': ""})
    
    @magicclass(layout="vertical")
    class Frame3:
        add_position  = field(PushButton, name = "Add position")
        write_all = field(PushButton, name = "Write all")

    @magicclass(layout="horizontal")
    class Frame5:
        ch1 = field(PushButton)
        ch2 = field(PushButton)
        ch3 = field(PushButton)
        ch4 = field(PushButton)
    
    @magicclass
    class Frame6:
        metadata = field(TextEdit, label="MetaData")
    
    @magicclass
    class F7:
        positions_to_write = field(TextEdit)
        writeprogress = field(ProgressBar, options={"min": 0.0, "max": 100.0,
                                                    "label": "Progress"}, 
                              )
    
    # @thread_worker(force_async=True, progress = {'desc': "Please wait."})
    def _writeStack(self, ch_names: List, save_path: str):
        if save_path:
            save_path = Path(save_path)
        else:
            save_path = self.exptInfo.data_dir
        # This dictionary will save the files for each wavelength
        
        n_files = len(self.to_process)
        for n, stub in enumerate(self.to_process):
            for i in np.arange(len(self.exptInfo.wavelengths)):
                # Add date prior to the name.
                save_name = self.exptInfo.date+"_"+stub[:-1]+ch_names[i]+'.tif'
                file_path = save_path / save_name
                if not file_path.exists():
                    im_array = np.zeros((len(self.exptInfo.timepoints), 
                                        self.exptInfo.imwidth,
                                        self.exptInfo.imheight), dtype='uint16')
                    
                    # Create a list of files excluding the thumb files
                    allfiles = self.exptInfo.data_dir.glob('**/'+stub+str(i+1)+'*')
                    nonthumbs = [file for file in allfiles if "thumb" not in file.name]
                    # I am so clever (after googling a bit)
                    sorted_nonthumbs = sorted(nonthumbs, key=lambda x: int(x.parent.name.split("_")[-1]))
                    for k, f in enumerate(sorted_nonthumbs):
                        im_array[k,:,:] = tifffile.imread(f)
                    print(f'Finished reading position {i+1} out of {n_files}...')

                    tifffile.imwrite(file_path, im_array)
                    print(f'Finished writing position {i+1} out of {n_files}...')
                    self.F7.writeprogress.value = 100*(n+1)/(n_files)
                else:
                    print(f'A file named {save_name} already exists!')
        return
    

    def __init__(self, data_path: str, viewer: napari.Viewer):
            super().__init__()
            self.w_dir = Path(os.getcwd())
            self.exptInfo = retrieveIXNInfo(data_path)
            self.Frame2.well_select.options = {'choices': ['']+ self.exptInfo.wells}
            self.Frame2.posi_select.options = {'choices': ['']+ self.exptInfo.positions}
            self.viewer   = viewer
            self.current_name_stub = []
            self.to_process = []
            self.Frame5.ch1.enabled = False
            self.Frame5.ch2.enabled = False
            self.Frame5.ch3.enabled = False
            self.Frame5.ch4.enabled = False
            self.Frame3.add_position.enabled = False
            self.Frame3.write_all.enabled = False
            self.F7.writeprogress.value = 0.0
            
    
    def __post_init__(self, ):
         self.Frame2.well_select.label = 'Well'
         self.Frame2.posi_select.label = 'Position'
         self.Frame1.w1_channel.value = 'phs'
         self.Frame1.w2_channel.value = 'GFP'
         self.Frame1.w3_channel.value = 'mCh'
         self.Frame1.w4_channel.value = 'Cy5'
    
    def _removeLayers(self,):
        # Remove previous layers
         num_layers = len(self.viewer.layers)
         if num_layers>0:
            for i in np.arange(num_layers):
                self.viewer.layers.remove(self.viewer.layers[-1])

    
    @Frame2.well_select.connect
    @Frame2.posi_select.connect
    def _loadPositiongivenWell(self, ):

         well = self.Frame2.well_select.value
         pos  = self.Frame2.posi_select.value
         # For the initial choice
         if pos == "":
             pos = 's1'
             self.Frame2.posi_select.value = 's1'
        
         parts = [self.exptInfo.name, well, pos, 'w']
         name_stub = "_".join(parts)
         self.current_name_stub = name_stub
         self._removeLayers() # remove old layers
         
         self.current_names = [] # Used for retrieving metadata
         for i in np.arange(len(self.exptInfo.wavelengths)):
             #Remove thumbnail files
             allfiles = Path(self.exptInfo.data_dir 
                           / self.exptInfo.timepoints[0]).glob(name_stub+str(i+1)+'*')
             nonthumbs = [file for file in allfiles if "thumb" not in file.name]
             
             for f in nonthumbs:
                self.viewer.add_image(tifffile.imread(f), 
                                   name = name_stub+str(i+1),
                                   colormap='gray')
                self.current_names.append(f)
         #Enable metadata buttons
         self.Frame3.add_position.enabled = True
         self.Frame3.write_all.enabled = True
         self.Frame5.ch1.enabled = True
         self.Frame5.ch2.enabled = True
         self.Frame5.ch3.enabled = True
         self.Frame5.ch4.enabled = True
         self.Frame6.metadata.value = self.retrieveMetaData(self.current_names[0])
    
    @Frame3.add_position.connect
    def _addtoQueue(self, ):
        self.to_process.append(self.current_name_stub)
        to_write = ""
        for entry in self.to_process:
            to_write = to_write + entry[-8:-2] + "\n"
        self.F7.positions_to_write.value = to_write
        return
    
    @Frame3.write_all.connect
    def _processAll(self, ):
        chNames = [self.Frame1.w1_channel.value,
                   self.Frame1.w2_channel.value,
                   self.Frame1.w3_channel.value,
                   self.Frame1.w4_channel.value,]

        save_path = self.Frame4.save_path.value
        self.thumbs = self._writeStack(chNames, save_path)
        # print(self.to_process)

    @Frame5.ch1.connect
    def _ch1MetaData(self,):
        self.Frame6.metadata.value = retrieveMetaData(self.current_names[0])

    @Frame5.ch2.connect
    def _ch2MetaData(self,):
        if len(self.current_names) > 3:
            self.Frame6.metadata.value = retrieveMetaData(self.current_names[1])
            print(retrieveMetaData(self.current_names[1]), self.current_names[1])
    
    @Frame5.ch3.connect
    def _ch3MetaData(self,):
        if len(self.current_names) > 3:
            self.Frame6.metadata.value = retrieveMetaData(self.current_names[2])
    
    @Frame5.ch4.connect
    def _ch4MetaData(self,):
        if 4 == len(self.current_names):
            self.Frame6.metadata.value = retrieveMetaData(self.current_names[3])
    

    
    