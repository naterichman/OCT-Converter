from pydicom.dataset import FileDataset, FileMetaDataset, Dataset
from pydicom.uid import generate_uid, OphthalmicTomographyImageStorage, ExplicitVRLittleEndian
from pydicom.encaps import encapsulate
from oct_converter.dicom import implementation_uid
import numpy as np
from oct_converter.dicom.metadata import DicomMetadata
from pathlib import Path
import typing as t
import tempfile
from datetime import datetime


OPT_DETECTOR_TYPE = ["CCD", "CMOS", "PHOTO", "INT"]

def opt_base_dicom() -> t.Tuple[Path, Dataset]:
	suffix = '.dcm'
	file_ = Path(tempfile.NamedTemporaryFile(suffix=suffix).name)

	# Populate required values for file meta information
	file_meta = FileMetaDataset()
	file_meta.MediaStorageSOPClassUID = OphthalmicTomographyImageStorage
	file_meta.MediaStorageSOPInstanceUID = generate_uid()
	file_meta.ImplementationClassUID = implementation_uid
	file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

	# Create the FileDataset instance with file meta, preamble and empty DS
	ds = FileDataset(str(file_), {}, file_meta=file_meta, preamble=b"\0" * 128)
	ds.is_little_endian = True
	ds.is_implicit_VR = False  # Explicit VR
	return file_, ds


def populate_patient_info(ds: Dataset, meta: DicomMetadata) -> Dataset:
	# Patient Module PS3.3 C.7.1.1
	ds.PatientName = f"{meta.last_name}^{meta.first_name}"
	ds.PatientID = meta.patient_id
	ds.PatientSex = meta.patient_sex
	ds.PatientBirthDate = meta.patient_dob.strftime('%Y%m%d')
	return ds


def populate_manufacturer_info(ds: Dataset, meta: DicomMetadata) -> Dataset:
	# General and enhanced equipment module PS3.3 C.7.5.1, PS3.3 C.7.5.2
	ds.Manufacturer = meta.manufacturer
	ds.ManufacturerModelName = meta.manufacturer_model
	ds.DeviceSerialNumber = meta.device_serial
	ds.SoftwareVersions = meta.software_version

	# OPT parameter module PS3.3 C.8.17.9
	# TODO: support other device types and load from manufacturer
	cd, cv, cm = meta.opt_acquisition_device.value
	ds.AcquisitionDeviceTypeCodeSequence = [Dataset()]
	ds.AcquisitionDeviceTypeCodeSequence[0].CodeValue = cv
	ds.AcquisitionDeviceTypeCodeSequence[0].CodingSchemeDesignator = cd
	ds.AcquisitionDeviceTypeCodeSequence[0].CodeMeaning = cm
	ds.DetectorType = meta.detector_type.value
	return ds


def populate_opt_series(ds: Dataset, meta: DicomMetadata) -> Dataset:
	# General study module PS3.3 C.7.2.1
	# Deterministic StudyInstanceUID based on study ID
	ds.StudyInstanceUID = generate_uid(entropy_srcs=[meta.study_id])

	# General series module PS3.3 C.7.3.1
	ds.SeriesInstanceUID = generate_uid(entropy_srcs=[meta.series_id])
	ds.Laterality = meta.laterality
	# Ophthalmic Tomography Series PS3.3 C.8.17.6
	ds.Modality = 'OPT'
	ds.SeriesNumber = int(meta.series_id)

	# SOP Common module PS3.3 C.12.1
	ds.SOPClassUID = OphthalmicTomographyImageStorage
	ds.SOPInstanceUID = generate_uid()
	return ds


def populate_ocular_region(ds: Dataset, meta: DicomMetadata) -> Dataset:
	# Ocular region imaged module PS3.3 C.8.17.5
	cd, cv, cm = meta.opt_anatomy.value
	ds.ImageLaterality = meta.laterality
	ds.AnatomicRegionSequence = [Dataset()]
	ds.AnatomicRegionSequence[0].CodeValue = cv
	ds.AnatomicRegionSequence[0].CodingSchemeDesignator = cd
	ds.AnatomicRegionSequence[0].CodeMeaning = cm
	return ds


def opt_shared_functional_groups(ds: Dataset, meta: DicomMetadata) -> Dataset:
	# ---- Shared
	shared_ds = [Dataset()]
	# Frame anatomy PS3.3 C.7.6.16.2.8
	shared_ds[0].FrameAnatomySequence = [Dataset()]
	shared_ds[0].FrameAnatomySequence[0] = ds.AnatomicRegionSequence[0].copy()	
	shared_ds[0].FrameAnatomySequence[0].FrameLaterality = meta.laterality
	# Pixel Measures PS3.3 C.7.6.16.2.1 
	shared_ds[0].PixelMeasuresSequence = [Dataset()]
	shared_ds[0].PixelMeasuresSequence[0].PixelSpacing = meta.pixel_spacing
	shared_ds[0].PixelMeasuresSequence[0].SliceThickness = meta.slice_thickness
	# Plane Orientation PS3.3 C.7.6.16.2.4
	shared_ds[0].PlaneOrientationSequence = [Dataset()]
	shared_ds[0].PlaneOrientationSequence[0].ImageOrientationPatient = meta.image_orientation
	ds.SharedFunctionalGroupsSequence = shared_ds
	return ds


def write_opt_dicom(
	meta: DicomMetadata,
	frames: t.List[np.ndarray]
):
	file_, ds = opt_base_dicom()
	ds = populate_patient_info(ds, meta)
	ds = populate_manufacturer_info(ds, meta)
	ds = populate_opt_series(ds, meta)
	ds = populate_ocular_region(ds, meta)
	ds = opt_shared_functional_groups(ds, meta)

	# TODO: Frame of reference if fundus image present

	# OPT Image Module PS3.3 C.8.17.7
	ds.ImageType = ['DERIVED', 'SECONDARY']
	ds.SamplesPerPixel = 1
	ds.AcquisitionDateTime = meta.acquisition_date.strftime('%Y%m%d%H%M%S.%f')
	ds.AcquisitionNumber = 1
	ds.PhotometricInterpretation = 'MONOCHROME2'
	# Unsigned integer
	ds.PixelRepresentation = 0
	# Use 16 bit pixel
	ds.BitsAllocated = 16
	ds.BitsStored = ds.BitsAllocated
	ds.HighBit = ds.BitsAllocated - 1
	ds.SamplesPerPixel = 1
	ds.NumberOfFrames = len(frames)


	# Multi-frame Functional Groups Module PS3.3 C.7.6.16
	dt = datetime.now()
	ds.ContentDate = dt.strftime('%Y%m%d')
	timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
	ds.ContentTime = timeStr
	ds.InstanceNumber = 1

	per_frame = []
	pixel_data_bytes = list()
	# Convert to a 3d volume
	pixel_data = np.array(frames).astype(np.uint16)
	ds.Rows = pixel_data.shape[1]
	ds.Columns = pixel_data.shape[2]
	for i in range(pixel_data.shape[0]):
		# Per Frame Functional Groups
		frame_fgs = Dataset()
		frame_fgs.PlanePositionSequence = [Dataset()]
		ipp = [0, 0, i*meta.slice_thickness]
		frame_fgs.PlanePositionSequence[0].ImagePositionPatient = ipp
		frame_fgs.FrameContentSequence = [Dataset()]
		frame_fgs.FrameContentSequence[0].InStackPositionNumber = i + 1
		frame_fgs.FrameContentSequence[0].StackID = '1'

		# Pixel data
		frame_dat = pixel_data[i, :, :]
		pixel_data_bytes.append(frame_dat.tobytes())
		per_frame.append(frame_fgs)
	ds.PerFrameFunctionalGroupsSequence = per_frame
	ds.PixelData = pixel_data.tobytes()
	ds.save_as(file_)
	return file_