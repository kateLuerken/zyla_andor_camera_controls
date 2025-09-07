import os
import numpy as np
from astropy.io import fits
import argparse
from pyAndorSDK3 import AndorSDK3
from collections import deque
import tifffile as tiff
import matplotlib.pyplot as plt

def make_fits_cube(folder_path, output_filename="fits_cube.fits"):
    print("making cube")
    fits_files = sorted([f for f in os.listdir(folder_path) if f.lower().endswith('.fits')])

    if not fits_files:
        raise ValueError("No FITS files found in the specified folder.")

    data_cube = []

    for fname in fits_files:
        file_path = os.path.join(folder_path, fname)
        with fits.open(file_path) as hdul:
            data = hdul[0].data
            data_cube.append(data)

    # Stack into 3D cube (N, Y, X)
    cube = np.stack(data_cube, axis=0)

    # Create a new FITS HDU and write to file
    hdu = fits.PrimaryHDU(cube)
    hdul = fits.HDUList([hdu])
    output_path = os.path.join(folder_path, output_filename)
    hdul.writeto(output_path, overwrite=True)

    print(f"FITS cube written to {output_path}")

def inspect_fits_cube(filename):
    # Open the FITS file
    with fits.open(filename) as hdul:
        data = hdul[0].data  # Assuming the cube is in the primary HDU

    # Check that data is a 3D cube
    if data.ndim == 3:
        num_frames = data.shape[0]
        print(f"Number of frames in the cube: {num_frames}")
    else:
        print("Data is not a 3D cube.")

def display_fit(filename):
    image_load = fits.open(filename)
    image = image_load[0].data

    fig, ax = plt.subplots()
    im = ax.imshow(image, cmap="gray")

    plt.colorbar(im, ax=ax)
    plt.show()

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--make", help="Make a fits cube")
    parser.add_argument("--inspect", help="Inspect a fits cube")
    parser.add_argument("--display", help="Display file")
    parser.add_argument("--filename", type=str, help="File to use", required=False)
    parser.add_argument("--input_folder", type=str, help="input folder", required=False)
    parser.add_argument("--output_file", type=str, help="output cube", required=False)
    args = parser.parse_args()

    if args.make:
        make_fits_cube(args.input_folder, args.output_file)
    else:
        pass
    
    if args.inspect:
        inspect_fits_cube(args.filename)
    else:
        pass
    
    if args.display:
        display_fit(args.filename)
    else:
        pass


