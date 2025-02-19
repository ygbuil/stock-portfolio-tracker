import shutil
from pathlib import Path

from loguru import logger


def delete_current_artifacts(directory: Path) -> None:
    """Delete all files and subdirectories in the specified directory except for `.gitkeep`.

    Args:
        directory: The path to the directory where files and folders should be deleted.
    """
    logger.info(f"Deleting existing artifacts in: {directory}")

    for item in directory.iterdir():
        if item.name == ".gitkeep":
            continue  # Skip .gitkeep file

        if item.is_file():
            item.unlink()
            logger.info(f"Deleted file: {item}")
        elif item.is_dir():
            shutil.rmtree(item)
            logger.info(f"Deleted directory: {item}")

    logger.info("Cleanup completed.")
