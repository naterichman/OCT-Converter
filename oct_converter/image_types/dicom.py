from pydicom.dataset import FileDataset, FileMetaDataset, Dataset
from pydicom.sequence import Sequence
from pydicom.uid import generate_uid, OphthalmicTomographyImageStorage, ExplicitVRLittleEndian
from . import implementation_uid, version
import tempfile
from datetime import datetime

OPT_ACQUISITION_DEVICE = {
	"oct_scan": ("SRT", "A-00FBE", "Optical Coherence Tomography Scanner"),
	"rt_analyzer": ("SRT", "R-FAB5A", "Retinal Thickness Analyzer"),
	"cslo": ("SRT", "A-00E8B", "Confocal Scanning Laser Ophthalmoscope"),
	"s_camera": ("DCM", "111626", "Scheimpflug Camera"),
	"scan_las_pol": ("SRT", "A-00E8C", "Scanning Laser Polarimeter"),
	"e_based_c_tomo": ("DCM", "111945", "Elevation-based corneal tomographer"),
	"r_based_c_topo": ("DCM", "111946", "Reflection-based corneal topographer"),
	"i_based_c_tomo": ("DCM", "111947", "Interferometry-based corneal tomographer"),
}

OPT_ANATATOMY_STRUCTURE = {
	'anterior_chamber_of_eye': ('SRT', 'T-AA050', 'Anterior chamber of eye'),
	'both_eyes': ('SRT', 'T-AA180', 'Both eyes'),
	'choroid_of_eye': ('SRT', 'T-AA310', 'Choroid of eye'),
	'ciliary_body': ('SRT', 'T-AA400', 'Ciliary body'),
	'conjunctiva': ('SRT', 'T-AA860', 'Conjunctiva'),
	'cornea': ('SRT', 'T-AA200', 'Cornea'),
	'eye': ('SRT', 'T-AA000', 'Eye'),
	'eyelid': ('SRT', 'T-AA810', 'Eyelid'),
	'fovea_centralis': ('SRT', 'T-AA621', 'Fovea centralis'),
	'iris': ('SRT', 'T-AA500', 'Iris'),
	'lacrimal_caruncle': ('SRT', 'T-AA862', 'Lacrimal caruncle'),
	'lacrimal_gland': ('SRT', 'T-AA910', 'Lacrimal gland'),
	'lacrimal_sac': ('SRT', 'T-AA940', 'Lacrimal sac'),
	'lens': ('SRT', 'T-AA700', 'Lens'),
	'lower_eyelid': ('SRT', 'T-AA830', 'Lower Eyelid'),
	'ophthalmic_artery': ('SRT', 'T-45400', 'Ophthalmic artery'),
	'optic_nerve_head': ('SRT', 'T-AA630', 'Optic nerve head'),
	'retina': ('SRT', 'T-AA610', 'Retina'),
	'sclera': ('SRT', 'T-AA110', 'Sclera'),
	'upper_eyelid': ('SRT', 'T-AA820', 'Upper Eyelid')
}



OPT_DETECTOR_TYPE = ["CCD", "CMOS", "PHOTO", "INT"]

def write_opt_dicom(
	firstname,
	surname,
	patient_id,
	sex,
	dob,
	acquisition_date,
	laterality,
	image_id,
	study_id,
	series_id,
	manufacturer
):
    # Create some temporary filenames
	suffix = '.dcm'
	filename = tempfile.NamedTemporaryFile(suffix=suffix).name
	# Populate required values for file meta information
	file_meta = FileMetaDataset()
	file_meta.MediaStorageSOPClassUID = OphthalmicTomographyImageStorage
	file_meta.MediaStorageSOPInstanceUID = generate_uid()
	file_meta.ImplementationClassUID = implementation_uid
	ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

	# Create the FileDataset instance with file meta, preamble and empty DS
	ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
	ds.is_little_endian = True
	ds.is_implicit_VR = False  # Explicit VR

	# Patient Module PS3.3 C.7.1.1
	ds.PatientName = f"{surname}^{firstname}"
	ds.PatientID = patient_id
	ds.PatientSex = sex

	# General study module PS3.3 C.7.2.1
	# Deterministic StudyInstanceUID based on study ID
	ds.StudyInstanceUID = generate_uid(entropy_srcs=[study_id])

	# General series module PS3.3 C.7.3.1
	ds.SeriesInstanceUID = generate_uid(entropy_srcs=[series_id])
	ds.Laterality = laterality
	# Ophthalmic Tomography Series PS3.3 C.8.17.6
	ds.Modality = "OPT"
	ds.SeriesNumber = int(series_id)

	# SOP Common module PS3.3 C.12.1
	ds.SOPClassUID = OphthalmicTomographyImageStorage
	ds.SOPInstanceUID = generate_uid()

	# TODO: Frame of reference if fundus image present

	# General and enhanced equipment module PS3.3 C.7.5.1, PS3.3 C.7.5.2
	ds.Manufacturer = manufacturer
	ds.ManufacturerModelName = 'unknown'
	ds.DeviceSerialNumber = 'unknown'
	ds.SoftwareVersions = ['unknown']

	# OPT parameter module PS3.3 C.8.17.9
	# TODO: support other device types and load from manufacturer
	cd, cv, cm = OPT_ACQUISITION_DEVICE['oct_scan']
	ds.AcquisitionDeviceTypeCodeSequence = [Dataset()]
	ds.AcquisitionDeviceTypeCodeSequence[0].CodeValue = cv
	ds.AcquisitionDeviceTypeCodeSequence[0].CodingSchemeDesignator = cd
	ds.AcquisitionDeviceTypeCodeSequence[0].CodeMeaning = cm
	ds.DetectorType = OPT_DETECTOR_TYPE[0] 

	# Ocular region imaged module PS3.3 C.8.17.5
	cd, cv, cm = OPT_ANATATOMY_STRUCTURE['retina']
	ds.ImageLaterality = laterality
	ds.AnatomicRegionSequence = [Dataset()]
	ds.AnatomicRegionSequence[0].CodeValue = cv
	ds.AnatomicRegionSequence[0].CodingSchemeDesignator = cd
	ds.AnatomicRegionSequence[0].CodeMeaning = cm

	# Multi-frame Functional Groups Module PS3.3 C.7.6.16
	dt = datetime.now()
	ds.ContentDate = dt.strftime('%Y%m%d')
	timeStr = dt.strftime('%H%M%S.%f')  # long format with micro seconds
	ds.ContentTime = timeStr
	ds.InstanceNumber = 1
	# ---- Shared
	shared_ds = [Dataset()]
	# Frame anatomy PS3.3 C.7.6.16.2.8
	shared_ds[0].FrameAnatomySequence = [Dataset()]
	shared_ds[0].FrameAnatomySequence[0] = ds.AnatomicRegionSequence[0].copy()	
	shared_ds[0].FrameAnatomySequence[0].FrameLaterality = laterality
	# Pixel Measures PS3.3 C.7.6.16.2.1 
	shared_ds[0].PixelMeasuresSequence = [Dataset()]
	shared_ds[0].PixelMeasuresSequence[0].PixelSpacing = []
	shared_ds[0].PixelMeasuresSequence[0].SliceThickness = []
	# Plane Orientation PS3.3 C.7.6.16.2.4
	shared_ds[0].PlaneOrientationSequence = [Dataset()]
	shared_ds[0].PlaneOrientationSequence[0].ImageOrientationPatient = []
	ds.SharedFunctionalGroupsSequence = shared_ds
	per_frame = []
	for frame in frames:
		frame_fgs = Dataset()

		# stuff

		per_frame.append(frame_fgs)
	ds.PerFrameFunctionalGroupsSequence = per_frame
	ds.PixelData = pixel_array
	ds.save_as(output_filename)