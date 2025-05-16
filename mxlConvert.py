# from MuseParse.classes.Input import MxmlParser
import zipfile
import os

def decompress_mxl(file_path, output_folder):
    if not zipfile.is_zipfile(file_path):
        raise ValueError(f"{file_path} is not a valid .mxl (ZIP) file")

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(output_folder)
        print(f"Extracted {file_path} to {output_folder}")

mxl_file = "perfect.mxl"
output_folder = "extracted_mxl"
os.makedirs(output_folder, exist_ok=True)
decompress_mxl(mxl_file, output_folder)


# parser = MxmlParser.MxmlParser()

# object_hierarchy = parser.parse("extracted_mxl/lg-12741397.xml")
