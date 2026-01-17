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
            # compile Java source
            try:
                compile_output = subprocess.check_output(
                    ["javac", str(file_path)],
                    stderr=subprocess.STDOUT,
                    text=True
                )
            except subprocess.CalledProcessError as e:
                output = e.output
                return output

            # detect generated .class files (javac may generate multiple)
            class_files = list(file_path.parent.glob("*.class"))
            if not class_files:
                return "Java compilation succeeded but no .class file was produced."

            # assume main class is the first generated class
            main_class = class_files[0].stem

            try:
                output = subprocess.check_output(
                    ["java", "-cp", str(file_path.parent), main_class],
                    stderr=subprocess.STDOUT,
                    text=True
                )
            finally:
                # clean up all generated .class files
                for cf in class_files:
                    if cf.exists():
                        cf.unlink()
        else:
            raise ValueError(f"Unsupported script extension: {extension}")
    except subprocess.CalledProcessError as e:
        output = e.output

    return output
