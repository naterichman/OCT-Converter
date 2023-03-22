import dataclasses
import enum
import datetime

class OPTAcquisitionDevice(enum.Enum):
	"""OPT Acquisition Device enumeration.

	Contains code designator, code value and code meaning for each entry.
	"""
	OCTScanner = ("SRT", "A-00FBE", "Optical Coherence Tomography Scanner")
	RetinalThicknessAnalyzer = ("SRT", "R-FAB5A", "Retinal Thickness Analyzer")
	ConfocalScanningLaserOphthalmoscope = ("SRT", "A-00E8B", "Confocal Scanning Laser Ophthalmoscope")
	ScheimpflugCamera = ("DCM", "111626", "Scheimpflug Camera")
	ScanningLaserPolarimeter = ("SRT", "A-00E8C", "Scanning Laser Polarimeter")
	ElevationBasedCornealTomographer = ("DCM", "111945", "Elevation-based corneal tomographer")
	ReflectionBasedCornealTopographer = ("DCM", "111946", "Reflection-based corneal topographer")
	InterferometryBasedCornealTomographer = ("DCM", "111947", "Interferometry-based corneal tomographer")
	Unspecified = ("OCT-converter", "D-0001", "Unspecified scanner")


class OPTAnatomyStructure(enum.Enum):
	"""OPT Anatomy enumeration.

	Contains code designator, code value and code meaning for each entry.
	"""
	AnteriorChamberOfEye = ('SRT', 'T-AA050', 'Anterior chamber of eye'),
	BothEyes = ('SRT', 'T-AA180', 'Both eyes'),
	ChoroidOfEye = ('SRT', 'T-AA310', 'Choroid of eye'),
	CiliaryBody = ('SRT', 'T-AA400', 'Ciliary body'),
	Conjunctiva = ('SRT', 'T-AA860', 'Conjunctiva'),
	Cornea = ('SRT', 'T-AA200', 'Cornea'),
	Eye = ('SRT', 'T-AA000', 'Eye'),
	Eyelid = ('SRT', 'T-AA810', 'Eyelid'),
	FoveaCentralis = ('SRT', 'T-AA621', 'Fovea centralis'),
	Iris = ('SRT', 'T-AA500', 'Iris'),
	LacrimalCaruncle = ('SRT', 'T-AA862', 'Lacrimal caruncle'),
	LacrimalGland = ('SRT', 'T-AA910', 'Lacrimal gland'),
	LacrimalSac = ('SRT', 'T-AA940', 'Lacrimal sac'),
	Lens = ('SRT', 'T-AA700', 'Lens'),
	LowerEyeLid = ('SRT', 'T-AA830', 'Lower Eyelid'),
	OphthalmicArtery = ('SRT', 'T-45400', 'Ophthalmic artery'),
	OpticNerveHead = ('SRT', 'T-AA630', 'Optic nerve head'),
	Retina = ('SRT', 'T-AA610', 'Retina'),
	Sclera = ('SRT', 'T-AA110', 'Sclera'),
	UpperEyeLid = ('SRT', 'T-AA820', 'Upper Eyelid')
	Unspecified = ('OCT-converter', 'A-0001', 'Unspecified anatomy')


class OCTDetectorType(enum.Enum):
	CCD = "CCD"
	CMOS = "CMOS"
	PHOTO = "PHOTO"
	INT = "INT"
	Unknown = "UNKNOWN"


@dataclasses.dataclass
class DicomMetadata():
	# Patient Info
	first_name: str
	last_name: str
	patient_id: str
	patient_sex: str
	patient_dob: datetime.datetime

	# Study and Series
	study_id: str
	series_id: str
	laterality: str
	acquisition_date: datetime.datetime

	# Manufacturer info
	manufacturer: str
	manufacturer_model: str = 'unknown'
	device_serial: str = 'unknown'
	software_version: str = 'unknown'
	opt_acquisition_device: OPTAcquisitionDevice = OPTAcquisitionDevice.Unspecified
	detector_type: OCTDetectorType = OCTDetectorType.Unknown

	# Anatomy
	opt_anatomy: OPTAnatomyStructure = OPTAnatomyStructure.Unspecified

	# Image params
	pixel_spacing = [1.0, 1.0]
	slice_thickness = 1.0
	image_orientation = [1, 0, 0, 0 , 1, 0]
