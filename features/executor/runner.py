import subprocess
from pathlib import Path

from .constants import RUNNER_SUPPORTED_LANGUAGES


def run_file(file_path: Path) -> str:
    """
    Run a file if supported and return output text.
    """

    ext = file_path.suffix.lstrip(".")

    if ext not in RUNNER_SUPPORTED_LANGUAGES:
        return "Not supported file!"

    return run_script(file_path, ext)


def run_script(file_path: str, extension: str = "js") -> None:
    if extension not in RUNNER_SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported script extension: {extension}")

    try:
        if extension == "py":
            output = subprocess.check_output(
                ["python3", str(file_path)],
                stderr=subprocess.STDOUT,
                text=True)

        elif extension == "js":
            output = subprocess.check_output(
                ["node", str(file_path)],
                stderr=subprocess.STDOUT,
                text=True)

        elif extension == "ts":
            js_file = file_path.with_suffix(".js")

            try:
                subprocess.check_output(
                    ["tsc", str(file_path)],
                    stderr=subprocess.STDOUT,
                    text=True
                )

                output = subprocess.check_output(
                    ["node", str(js_file)],
                    cwd=file_path.parent,
                    stderr=subprocess.STDOUT,
                    text=True
                )

            finally:
                if js_file.exists():
                    js_file.unlink()

        elif extension == "java":
            class_file = file_path.with_suffix(".class")
            class_name = file_path.stem

            try:
                subprocess.check_output(
                    ["javac", str(file_path)],
                    stderr=subprocess.STDOUT,
                    text=True
                )

                output = subprocess.check_output(
                    ["java", "-cp", str(file_path.parent), class_name],
                    stderr=subprocess.STDOUT,
                    text=True
                )

            finally:
                if class_file.exists():
                    class_file.unlink()
        else:
            raise ValueError(f"Unsupported script extension: {extension}")
    except subprocess.CalledProcessError as e:
        output = e.output

    return output
