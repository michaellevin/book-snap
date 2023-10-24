import os
from subprocess import check_output, CalledProcessError, STDOUT
import img2pdf
import glob
from pathlib import Path
import hashlib


def system_call(command):
    """
    Executes a system command and returns its output.

    Args:
        command (str): The command to execute.

    Returns:
        str: The output of the command if successful.

    Raises:
        RuntimeError: If the command fails, an exception is raised with the reason.
    """
    try:
        # The output is returned as bytes, so we decode it to UTF-8 (or the appropriate encoding).
        output = check_output(command, stderr=STDOUT).decode(
            "utf-8"
        )  # Adding shell=True might be necessary depending on the command being executed.
    except CalledProcessError as e:
        # e.output contains the combined standard output and standard error of the command.
        error_message = e.output.decode("utf-8")
        raise RuntimeError(
            f"Command execution failed: {error_message}"
        ) from e  # Including original exception information.

    return output  # Only reached if no exception was raised.


def hash_url(url: str) -> int:
    """
    Generate a unique integer ID from the library URL.
    This example uses a hash function to ensure the uniqueness of the ID,
    converting the hash to an integer to be used as the ID.
    """
    # Create a hash of the URL
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    # Convert the hash to an integer. We use only the first few characters to avoid large numbers.
    unique_id = int(
        url_hash[:10], 16
    )  # This will convert the hexadecimal hash substring to an integer.
    return unique_id


def create_pdf(dest_folder: str, title: str) -> str:
    """
    Converts all jpeg images in the specified folder to a single PDF and deletes the images.

    :param dest_folder: Folder containing jpeg images.
    :param title: Title of the resulting PDF file.
    """
    # Convert paths to Path objects, which are more versatile
    dest_folder_path = Path(dest_folder)
    pdf_path = dest_folder_path / f"{title}.pdf"

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
