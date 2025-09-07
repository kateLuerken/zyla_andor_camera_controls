import argparse
import numpy as np
import os
from pyAndorSDK3 import AndorSDK3
from collections import deque
import ctypes
from astropy.io import fits
import tifffile as tiff
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import folder_to_cube
import time


def process_image(acquisition):
    raw_img = acquisition._np_data
    raw_img + 1
    acquisition._np_data = raw_img
    return acquisition

def speckle_capture(frame_count, exposure, output_folder, crop=False):

    sdk3 = AndorSDK3()
    cam = sdk3.GetCamera(0)
    print(cam.SerialNumber)
    
    timeout = 1000
    cam.TriggerMode == "Software"
    cam.CycleMode == "Fixed"
    cam.FrameCount = frame_count
    cam.ExposureTime = exposure
    
    if crop == True:
        cam.AOIHeight = 428
        cam.AOIWidth = 428 
        cam.AOILeft = 860 #960
        cam.AOITop = 860 #960
    else:
        pass

    imgsize = cam.ImageSizeBytes
    for _ in range(0, frame_count):
        buf = np.empty((imgsize,), dtype='B')
        cam.queue(buf, imgsize)

    series = deque()
    frame = None
    try:
        cam.AcquisitionStart()
        frame = 0
        while(True):
            cam.SoftwareTrigger()
            acq = cam.wait_buffer(timeout)
            acq = process_image(acq)
            series.append(acq)

            frame += 1
            percent = int((frame/frame_count)*100)
            print("{}% complete series".format(percent), end="\r")
            if frame >= frame_count:
                print()
                break
    except Exception as e:
        if frame is not None:
            print()
            print("Error on frame "+str(frame))
        cam.AcquisitionStop()
        cam.flush()
        raise e
    cam.AcquisitionStop()
    cam.flush()

    capture_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(capture_dir, output_folder)
    os.makedirs(output_dir, exist_ok=True)

    # save list(series) as FITS cube
    for i, acq in enumerate(series):
    # using acq.save() includes acquisition information
    # in the fits header such as PixelEncoding and AOI settings
        acq.save(f"{output_folder}/acq_{i}.fits", True)
        #print(f"{output_folder}/acq_{i}.fits")

    fits_cube_name = output_folder + "_cube.fits"
    fits_cube_path = os.path.join(output_folder, fits_cube_name)

    # comment these 2 below if you don't want data cubes
    #folder_to_cube.make_fits_cube(output_folder, fits_cube_name)
    #folder_to_cube.inspect_fits_cube(fits_cube_path)

    image_load = fits.open(f"{output_folder}/acq_0.fits")
    image = image_load[0].data
    
    fig, ax = plt.subplots()
    im = ax.imshow(image, cmap="gray")
    
    height, width = image.shape
    x = (width - 100) // 2
    y = (height - 100) // 2
    rect = patches.Rectangle((x, y), 100, 100, linewidth=1, edgecolor='r', facecolor='none')
    #ax.add_patch(rect)
    
    plt.colorbar(im, ax=ax)
    plt.show()

    return list(series)

def live_view(exposure):
    sdk3 = AndorSDK3()
    cam = sdk3.GetCamera(0)
    print(cam.SerialNumber)
    
    timeout = 10
    cam.TriggerMode == "Continuous"
    cam.CycleMode == "Fixed"
    cam.FrameCount = frame_count
    cam.ExposureTime = exposure
    
    # next four lines get commented out if you need full frame
    cam.AOIHeight = 128
    cam.AOIWidth = 128
    cam.AOILeft = 960
    cam.AOITop = 960

    imgsize = cam.ImageSizeBytes
    for _ in range(0, frame_count):
        buf = np.empty((imgsize,), dtype='B')
        cam.queue(buf, imgsize)

    cam.AcquisitionStart()
    cam.SoftwareTrigger()
    acq = cam.wait_buffer(timeout)
    # acq = process_image(acq)
    acq = acq.image
    cam.AcquisitionStop()
    frame = np.array(acq, copy=False)
    print("CHK 1")

    plt.ion()
    fig, ax = plt.subplots()
    im = ax.imshow(frame, cmap="gray")
    plt.show(block=False)

    stop_flag = {"stop": False}
    def on_key(event):
        stop_flag["stop"] = True
    fig.canvas.mpl_connect("key_press_event", on_key)
    
    i = 2
    try:
        while not stop_flag["stop"]:
            print(f"CHK {i}")
            cam.AcquisitionStart()
            cam.SoftwareTrigger()
            try:
                acq = cam.wait_buffer(timeout)
                #acq = process_image(acq)
                acq = acq.image
                frame = np.array(acq, copy=False)
            except Exception as e:
                if "TIMEDOUT" in str(e) or "13" in str(e):
                    print(f"Frame {i} timed out, skipping...")
                else:
                    raise
            cam.AcquisitionStop()
            im.set_data(frame)
            fig.canvas.draw()
            fig.canvas.flush_events()
            plt.pause(1)
            #time.sleep(1)
            i += 1  
    finally:    
        plt.ioff()
        plt.close(fig)

    return "Done"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("frames", type=int, help="Number of frames to capture.")
    parser.add_argument("exp", type=float, help="Exposure time, in seconds.")
    parser.add_argument("out", type=str, help="Output folder name.")
    parser.add_argument("--live", action="store_true", help="Display live view")
    parser.add_argument("--crop", action="store_true", help="Capture only ROI")
    # parser.add_argument("display", type=bool, default=False, help="Display first output frame.")
    args = parser.parse_args()


    #### DO NOT TOUCH
    dll_path = r"C:\Program Files\Andor SDK3\atcore.dll"
    atcore = ctypes.WinDLL(dll_path)
    sdk_path = r"C:\Program Files\Andor SDK3"
    ctypes.WinDLL(os.path.join(sdk_path, "atusb_libusb.dll"))
    ctypes.WinDLL(os.path.join(sdk_path, "atusb_libusb10.dll"))
    ctypes.WinDLL(os.path.join(sdk_path, "atdevregcam.dll"))  
    atcore = ctypes.WinDLL(os.path.join(sdk_path, "atcore.dll"))
    status = atcore.AT_InitialiseLibrary()
    ####

    frame_count = args.frames
    exposure = args.exp
    output_folder = args.out 
    # display_frame = args.display
    print(frame_count, exposure, output_folder)

    if args.live:
        live_view(exposure)
    elif args.crop:
        speckle_capture(frame_count, exposure, output_folder, crop=True)
    else:
        speckle_capture(frame_count, exposure, output_folder, crop=False)
    
    print("All done!")