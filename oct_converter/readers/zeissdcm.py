from pathlib import Path
import math
import pydicom
import cv2
import numpy as np
from oct_converter.image_types import OCTVolumeWithMetaData


class ZEISSDCM(object):
    """Class for extracting data from Zeiss's .dcm file format.

    Attributes:
        filepath (str): Path to .img file for reading.
    """

    def __init__(self, filepath):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(self.filepath)

    def read_oct_volume(self):
        """Reads OCT data.

        """

        def find_oct_tags(dataset, data_element):
            if data_element.tag == (0x0407, 0x1005):
                num_frames = len(data_element.value)
                volume=[]
                print(f'Found {num_frames} frames')
                for frame in data_element:
                    scrambled_frame=frame[0x0407, 0x1006]
                    unscrambled_frame = self.unscramble_frame(scrambled_frame)
                    frame = cv2.imdecode(np.frombuffer(unscrambled_frame, np.uint8), flags=1)
                    volume.append(frame[:,:,0]) # is grayscale so we take the first channel
                all_oct_volumes.append(volume)
        ds = pydicom.dcmread(self.filepath)
        if not ds.Manufacturer.startswith("Carl Zeiss Meditec"):
            raise ValueError("This does not appear to be a Zeiss DCM. You may need to read with the DCM class.")
        all_oct_volumes = []
        ds.walk(find_oct_tags)

        all_volumes_out = []
        for volume in all_oct_volumes:
            array = np.rot90(np.array(volume),axes=(1, 2),k=3)
            all_volumes_out.append(
                OCTVolumeWithMetaData(
                    volume=array,
                    patient_id=ds.PatientID,
                    first_name=str(ds.PatientName).split('^')[1],
                    surname=str(ds.PatientName).split('^')[0],
                    sex=ds.PatientSex,
                    acquisition_date=ds.StudyDate,
                    laterality=ds.Laterality,
                )
            )
        return all_volumes_out


    def unscramble_frame(self, frame: bytes) -> bytearray:
        """Return an unscrambled image frame. Thanks to https://github.com/scaramallion for the code,
         as detailed in https://github.com/pydicom/pydicom/discussions/1618.

        Args
        frame (bytes): The scrambled CZM JPEG 2000 data frame as found in the DICOM dataset.

        Returns
        bytearray: The unscrambled JPEG 2000 data.
        """
        # Fix the 0x5A XORing
        frame = bytearray(frame)
        for ii in range(0, len(frame), 7):
            frame[ii] = frame[ii] ^ 0x5A

        # Offset to the start of the JP2 header - empirically determined
        jp2_offset = math.floor(len(frame) / 5 * 3)

        # Double check that our empirically determined jp2_offset is correct
        offset = frame.find(b"\x00\x00\x00\x0C")
        if offset == -1:
            raise ValueError("No JP2 header found in the scrambled pixel data")

        if jp2_offset != offset:
            print(
                f"JP2 header found at offset {offset} rather than the expected "
                f"{jp2_offset}"
            )
            jp2_offset = offset

        d = bytearray()
        d.extend(frame[jp2_offset:jp2_offset + 253])
        d.extend(frame[993:1016])
        d.extend(frame[276:763])
        d.extend(frame[23:276])
        d.extend(frame[1016:jp2_offset])
        d.extend(frame[:23])
        d.extend(frame[763:993])
        d.extend(frame[jp2_offset + 253:])

        assert len(d) == len(frame)

        return d
