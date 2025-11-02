from __future__ import annotations
from pathlib import pathlib
from typing import BinaryIO
import shutil
import os

class ImageStorage:
    """
    Handles saving, loading, and deleting image files.
    """

    def __init__(
        self,
        base_dir: str
    ) -> None:
        self.base_dir: Path = Path(base_dir)
        self.base_dir.mkdir(
            parents-True,
            exist_ok=True
        )
    
    def save_image(
        self,
        file_obj: BinaryIO,
        filename: str
    ) -> Path:
        """Save an uploaded image file to disk"""
        save_path: Path = self.base_dir / filename
        with open(save_path, "wb") as out_file:
            shutil.copyfileobj(file_obj, out_file)
        return save_path
    
    def load_image(self, image_path: str) -> BinaryIO:
        """Load an image file from disk for streaming."""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {image_path}"
            )
        return open(path, "rb")
    
    def delete_image(self, image_path: str) -> None:
        """Deleting an image file if it exists."""
        try:
            os.remove(image_path)
        except FileNotFoundError:
            pass