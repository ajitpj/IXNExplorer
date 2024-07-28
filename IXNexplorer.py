import os, sys, subprocess, tifffile, napari
import numpy as np
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
from itertools import groupby

# Data class for storing properties of the experiment
@dataclass
class exptInfo:
    data_dir: Path
    name: str
    date: str
    wells: list
    positions: list
    wavelengths: list
    timepoints: list
    imwidth:  int = 2048
    imheight: int = 2048

def retrieveIXNInfo(data_path: Path):
    data_dir = Path(data_path)

    timepoints = []
    for dir in os.scandir(data_dir):
        if 'TimePoint' in dir.name:
            timepoints.append(dir.name)

    timepoints = sorted(timepoints)

    # Files in the first timepoint directory
    file_list = [f.name for f in os.scandir(data_dir / timepoints[0])
                    if 'thumb' not in f.name.casefold()]

    # Retrieve the date
    img = tifffile.TiffFile(data_dir / timepoints[0] / file_list[0])
    date = img.pages[0].tags['DateTime'].value.split(' ')[0]
    imwidth  = img.pages[0].tags['ImageWidth'].value
    imheight = img.pages[0].tags['ImageLength'].value
    # Infer expt. details from the first directory
    wells = []
    positions = []
    wavelengths = []
    for file in file_list:
        # print(file)
        splits = file.split('_')
        name = splits[0]
        wells.append(splits[1])
        positions.append(splits[2])
        wavelengths.append(splits[3][0:2])

    wells = sorted(list(set(wells)))
    positions = sorted(list(set(positions)))
    wavelengths = sorted(list(set(wavelengths)))

    # Create the expt. info data class
    IXNInfo = exptInfo(data_dir, name, date,
                       wells, positions,
                       wavelengths, timepoints,
                       imwidth, imheight)

    return IXNInfo

def writeStack(IXNGUI, ch_names: List, save_path: Path):
    if not save_path:
        save_path = exptInfo.data_dir
    # This dictionary will save the files for each wavelength
    stub_list = IXNGUI.to_process
    n_files = len(stub_list)
    for n, stub in enumerate(stub_list):
        for i in np.arange(len(exptInfo.wavelengths)):
            # Add date prior to the name.
            save_name = IXNGUI.exptInfo.date+"_"+stub[:-1]+ch_names[i]+'.tif'
            file_path = save_path / save_name
            if not file_path.exists():
                im_array = np.zeros((len(IXNGUI.exptInfo.timepoints),
                                    IXNGUI.exptInfo.imwidth,
                                    IXNGUI.exptInfo.imheight), dtype='uint16')

                # Create a list of files excluding the thumb files
                allfiles = IXNGUI.exptInfo.data_dir.glob('**/'+stub+str(i+1)+'*')
                nonthumbs = [file for file in allfiles if "thumb" not in file.name.casefold()]
                
                sorted_nonthumbs = sorted(nonthumbs, key=lambda x: int(x.parent.name.split("_")[-1]))
                for k, f in enumerate(sorted_nonthumbs):
                    im_array[k,:,:] = tifffile.imread(f)
                print(f'Finished reading position {n+1} out of {n_files}...')

                tifffile.imwrite(file_path, im_array)
                print(f'Finished writing position {n+1} out of {n_files}...')
                IXNGUI.F7.writeprogress.value = 100*(n+1)/(n_files)
            else:
                print(f'A file named {save_name} already exists!')


    return sorted_nonthumbs

def retrieveMetaData(filepath):
    # The interesting setttings start from lines 55-75
    metadata = str(tifffile.TiffFile(filepath).metaseries_metadata).split(',')[55:75]
    formatted = ''
    for line in metadata:
        formatted = formatted+line+'\n'

    return formatted
