from oct_converter.readers import ZEISSDicom

filepath = "../sample_files/sample_zeissdcm.dcm"
img = ZEISSDicom(filepath)

oct_volumes, fundus_volumes = img.read_data()  # returns a list OCT and fudus images

for idx, volume in enumerate(oct_volumes):
    volume.save(f"zeiss_volume_{idx}.png")  # save all volumes

for idx, image in enumerate(fundus_volumes):
    image.save(f"zeiss_image_{idx}.png")
