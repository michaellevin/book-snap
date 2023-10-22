import os
from subprocess import check_output, CalledProcessError, STDOUT
import img2pdf
import glob
from pathlib import Path


def system_call(command):
    try:
        output = check_output(command, stderr=STDOUT).decode()
        success = True
    except CalledProcessError as e:
        output = e.output.decode()
        success = False
    return output, success


def create_pdf(dest_folder: str, name: str) -> str:
    """
    Converts all jpeg images in the specified folder to a single PDF and deletes the images.

    :param dest_folder: Folder containing jpeg images.
    :param name: Name of the resulting PDF file.
    """
    # Convert paths to Path objects, which are more versatile
    dest_folder_path = Path(dest_folder)
    pdf_path = dest_folder_path / f"{name}.pdf"

    # Find all JPEG images in the destination folder
    imgs = glob.glob(str(dest_folder_path / "*.jpeg"))

    # Create a PDF from the images
    try:
        with open(pdf_path, "wb") as f:
            f.write(img2pdf.convert(imgs))
    except Exception as e:
        print(f"An error occurred while creating the PDF: {e}")
        return

    # Delete the images
    for img_path in imgs:
        try:
            os.remove(img_path)
        except OSError as e:
            print(f"Error deleting file {img_path}: {e}")

    return pdf_path
