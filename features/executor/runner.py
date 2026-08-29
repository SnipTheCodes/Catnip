import subprocess
from pathlib import Path
from typing import Callable

from utils.editor import RunnableLanguage


def run_file(file_path: Path) -> str:
    """Run the given file using the appropriate language runner based on its extension."""

    ext: RunnableLanguage = RunnableLanguage(file_path.suffix.lstrip("."))
    return LANGUAGE_RUNNERS[ext](file_path)


def run_python(file_path: Path) -> str:
    try:
        return subprocess.check_output(["python3", str(file_path)],
                                       stderr=subprocess.STDOUT,
                                       text=True)
    except subprocess.CalledProcessError as error:
                return error.output


def run_javascript(file_path: Path) -> str:
    try:
        return subprocess.check_output(["node", str(file_path)],
                                       stderr=subprocess.STDOUT,
                                       text=True)
    except subprocess.CalledProcessError as error:
        return error.output


def run_typescript(file_path: Path) -> str:
    js_file = file_path.with_suffix(".js")

    try:
        try:
            subprocess.check_output(["tsc", str(file_path)],
                                    stderr=subprocess.STDOUT, text=True)
        except subprocess.CalledProcessError as error:
            return error.output
            
        return subprocess.check_output(["node",
                                        str(js_file)],
                                       cwd=file_path.parent,
                                       stderr=subprocess.STDOUT,
                                       text=True)

    finally:
        if js_file.exists():
            js_file.unlink()


def run_java(file_path: Path) -> str:
    try:
        # compile Java source
        subprocess.check_output(
            ["javac", str(file_path)],
            stderr=subprocess.STDOUT,
            text=True)
    except subprocess.CalledProcessError as error:
        return error.output

    # detect generated .class files (javac may generate multiple)
    class_files = list(file_path.parent.glob("*.class"))
    if not class_files:
        return "Java compilation succeeded but no .class file was produced."

    # assume main class is the first generated class
    main_class = class_files[0].stem

    try:
        return subprocess.check_output(
            ["java", "-cp", str(file_path.parent),
             main_class], stderr=subprocess.STDOUT, text=True)
    finally:
        # clean up all generated .class files
        for cf in class_files:
            if cf.exists():
                cf.unlink()


Runner = Callable[[Path], str]

LANGUAGE_RUNNERS: dict[RunnableLanguage, Runner] = {
    RunnableLanguage.PY: run_python,
    RunnableLanguage.JS: run_javascript,
    RunnableLanguage.TS: run_typescript,
    RunnableLanguage.JAVA: run_java,
}
