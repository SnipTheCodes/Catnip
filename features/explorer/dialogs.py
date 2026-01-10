import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

if sys.platform.startswith("win"):
    from tkinter import Tk, filedialog, messagebox


class BaseDialogHandler(ABC):
    """Abstract base class for handling file and folder selection dialogs."""

    @abstractmethod
    def select_file(self) -> Optional[list[Path]]:
        """Select one or multiple files and return their paths."""
        pass

    @abstractmethod
    def select_folder(self) -> Optional[str]:
        """Select a folder and return its path."""
        pass

    @abstractmethod
    def select_file_save(self) -> Optional[str]:
        """Open a 'Save As' dialog and return the selected file path."""
        pass

    @abstractmethod
    def select_folder_save(self) -> Optional[str]:
        """Select a folder and prompt the user to enter a filename."""
        pass

    @abstractmethod
    def confirm_action(self, title: str, message: str) -> bool:
        """Select a folder and prompt the user to enter a filename."""
        pass


class TkinterDialogHandler(BaseDialogHandler):
    """File dialog handler using Tkinter for Windows."""

    def select_file(self) -> Optional[list[Path]]:
        """Open a file selection dialog and return selected file paths."""
        root = Tk()
        root.withdraw()
        file_paths = filedialog.askopenfilenames()
        root.destroy()
        return [Path(file) for file in file_paths] if file_paths else None

    def select_folder(self) -> Optional[str]:
        """Open a folder selection dialog and return the selected folder path."""
        root = Tk()
        root.withdraw()
        folder_path = filedialog.askdirectory()
        root.destroy()
        return folder_path if folder_path else None

    def select_file_save(self) -> Optional[str]:
        """Open a 'Save As' dialog and return the selected file path."""
        root = Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("All Files", "*.*"), ("Text Files", "*.txt"), ("Python Files", "*.py")]
        )
        root.destroy()
        return file_path if file_path else None

    def select_folder_save(self) -> Optional[str]:
        """Select a folder and prompt the user to enter a filename."""
        root = Tk()
        root.withdraw()
        folder_path = filedialog.askdirectory()
        root.destroy()

        if not folder_path:
            return None  # user canceled

        # ask for filename after selecting folder
        file_name = filedialog.asksaveasfilename(initialdir=folder_path, defaultextension=".txt")
        return Path(file_name) if file_name else None

    def confirm_action(self, title: str, message: str) -> bool:
        """Show a confirmation dialog with Yes/No options."""
        root = Tk()
        root.withdraw()  # Hide the root window
        return messagebox.askyesno(title, message)


class ZenityDialogHandler(BaseDialogHandler):
    """File dialog handler using Zenity for Linux/macOS."""

    def select_file(self) -> Optional[list[Path]]:
        """Open a file selection dialog using Zenity and return selected file paths."""
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", "--multiple", "--separator=,"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return [Path(file) for file in result.stdout.strip().split(",")]
        except FileNotFoundError:
            print("ERROR: Zenity not found. Install it or use another method.")
        return None

    def select_folder(self) -> Optional[str]:
        """Open a folder selection dialog using Zenity and return the selected folder path."""
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            print("ERROR: Zenity not found. Install it or use another method.")
        return None

    def select_file_save(self) -> Optional[str]:
        """Open a 'Save As' dialog using Zenity and return the selected file path."""
        try:
            result = subprocess.run(
                ["zenity", "--file-selection", "--save", "--confirm-overwrite"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except FileNotFoundError:
            print("ERROR: Zenity not found. Install it or use another method.")
        return None

    def select_folder_save(self) -> Optional[str]:
        """Select a folder and prompt the user to enter a filename."""
        try:
            # ask user to select a folder
            folder_result = subprocess.run(
                ["zenity", "--file-selection", "--directory"],
                capture_output=True,
                text=True
            )

            if folder_result.returncode != 0 or not folder_result.stdout.strip():
                return None  # user canceled

            folder_path = folder_result.stdout.strip()

            # ask user to enter filename
            file_result = subprocess.run(
                [
                    "zenity", "--entry",
                    "--title=Save File",
                    "--text=Enter filename:",
                    "--width=400",
                    "--height=150",
                    "--entry-text=example.txt"
                ],
                capture_output=True,
                text=True
            )

            if file_result.returncode != 0 or not file_result.stdout.strip():
                return None  # user canceled

            filename = file_result.stdout.strip()
            if "." not in filename:
                return Path(f"{folder_path}/{filename}.txt")
            else:
                return Path(f"{folder_path}/{filename}")

        except FileNotFoundError:
            print("ERROR: Zenity not found. Install it or use another method.")
        return None

    def confirm_action(self, title: str, message: str) -> bool:
        """Show a confirmation dialog with Yes/No options."""
        result = subprocess.run(
            [
                "zenity", "--question",
                "--title", title,
                "--text", message,
            ],
            capture_output=True,
            text=True
        )
        return result.returncode == 0  # returns True if user clicks "Yes"


def get_dialog_handler() -> BaseDialogHandler:
    """Return the appropriate file dialog handler based on the OS."""
    if sys.platform.startswith("win"):
        return TkinterDialogHandler()
    else:
        return ZenityDialogHandler()
