from pathlib import Path
import numpy as np
import pydicom
import cv2

def dcm_to_png_conversion(filename:Path|str)->np.ndarray:
    """Extract the image from a DICOM and write it to an image file."""

    # Read the DICOM and extract the image.
    dcm_file = pydicom.dcmread(filename)
    raw_image = dcm_file.pixel_array

    assert len(raw_image.shape) == 2,\
        "Expecting single channel (grayscale) image."

    # Normalize pixels to be in [0, 255].
    raw_image = raw_image - raw_image.min()
    normalized_image = raw_image / raw_image.max()
    rescaled_image = (normalized_image * 255).astype(np.uint8)

    # Correct image inversion.
    if dcm_file.PhotometricInterpretation == "MONOCHROME1":
        rescaled_image = cv2.bitwise_not(rescaled_image)

    # Perform histogram equalization.
    equal_image = cv2.equalizeHist(rescaled_image)

    final_image = cv2.resize( equal_image, ( 224, 224 ) )

    return final_image



