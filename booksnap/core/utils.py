import hashlib
from subprocess import check_output, CalledProcessError, STDOUT

# from pathlib import Path


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
