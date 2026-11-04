import os
from pathlib import Path
import sys
import platform as pl
import shutil
import subprocess
from zipfile import ZipFile
from urllib.request import urlopen
import tempfile

# Color codes
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
RESET  = "\033[0m"

ROOT = Path(__file__).resolve().parent

PLATFORM = pl.system().lower()
ARCH = pl.machine() if pl.machine() != 'aarch64' else 'arm64'

# Error messages
def error(msg: str) -> str:
    return RED + msg + RESET

# Warning messages
def warning(msg: str) -> str:
    return YELLOW + msg + RESET

# Informative messages
def message(msg: str) -> str:
    return BLUE + msg + RESET

# Success messages
def success(msg: str) -> str:
    return GREEN + msg + RESET

# Check system compatbility
def check_system() -> None:
    if PLATFORM not in ('linux', 'windows', 'darwin'):
        raise SystemExit(error(f"Platform {PLATFORM} not supported"))

    if ARCH in ('x86', 'i386', 'arm', 'armhf'):
        raise SystemExit(error("32 bit platforms not supported"))

    if ARCH not in ('AMD64', 'x86_64', 'x64', 'arm64'):
        raise SystemExit(error(f"{ARCH} platform architecture not supported"))

    if PLATFORM in ('linux', 'windows') and ARCH == 'arm64':
        raise SystemExit(error(f"Arm platform not supported for {PLATFORM}"))

    print(f'Platform is {message(PLATFORM)}')
    print(f'Arch is {message(ARCH)}')
    print(f'Python version is {message(pl.python_version())}')

# Create .env file
def create_envfile() -> None:
    default = """
    DATA_PATH=''
    DB_HOST='localhost'
    DB_PORT='5432'
    DB_NAME='chat'
    DB_USER='user'
    DB_PASSWORD='password'
    DB_PERSISTANT='true'
    DB_ECHO='false'
    """

    if not Path('.env').exists():
        with open('.env', 'w', encoding='UTF-8') as envfile:
            envfile.write(default)

        print(success(".env file created"))
    else:
        print(success(".env file detected"))

# Install frontend package
def install_frontend() -> None:
    frontend_link = (
        'https://github.com/yorha-dev/'
        'cognium-frontend/releases/v0.1.0/download/'
        'cognium-frontend.zip'
    )
    frontend_path = Path(ROOT / 'frontend' / 'web')
    temp_path = Path(ROOT / 'temp')

    if (frontend_path / 'index.html').exists():
        print(success("Frontend installation found"))

        if question_loop(warning("Do you want to reinstall frontend? (y/n): ")) == 'n':
            return

    frontend_path.mkdir(parents=True, exist_ok=True)

    print(message("Downloading frontend package..."))

    with tempfile.TemporaryDirectory(temp_path) as temp:
        frontend_tmp = Path(temp / 'web')
        backup_path = Path(temp / 'backup')

        with urlopen(frontend_link, timeout=60) as response:
            temp_file = Path(temp / 'cognium-frontend.zip')

            try:
                temp_file.write_bytes(response.read())
            except Exception as err:
                raise SystemExit(
                    error("Could not download frontend artifact")
                ) from err

            with ZipFile(temp_file) as zip_file:
                frontend_tmp.mkdir(parents=True, exist_ok=True)

                zip_file.extractall(frontend_tmp)

                if not (frontend_tmp / 'index.html').exists():
                    raise SystemExit(error('Could not extract frontend package'))

                # Copy old files to tmp dir (backup)
                current_files = list(frontend_path.iterdir())

                if 'index.html' in current_files:
                    print(warning("Making backup of existing frontend..."))

                    for item in current_files:
                        if item.is_file():
                            shutil.copy2(item, backup_path)

                            item.unlink()

                        if item.is_dir():
                            shutil.copytree(
                                item,
                                backup_path / item.name,
                                dirs_exist_ok=True
                            )

                            shutil.rmtree(item)

                # Copy files to frontend/web
                extracted_files = list(frontend_tmp.iterdir())

                for item in extracted_files:
                    if item.is_file():
                        shutil.copy2(item, frontend_path)

                    if item.is_dir():
                        shutil.copytree(
                            item,
                            frontend_path / item.name,
                            dirs_exist_ok=True
                        )

                # Verify if all files was copied
                if len(list(frontend_path.iterdir())) != len(extracted_files):
                    print(warning(
                        "Frontend installation finished with error. "
                        "Restoring frontend backup"
                    ))

                    shutil.rmtree(frontend_path)

                    frontend_path.mkdir(parents=True, exist_ok=True)

                    for item in backup_path.iterdir():
                        if item.is_file():
                            shutil.copy2(item, frontend_path)

                        if item.is_dir():
                            shutil.copytree(
                                item,
                                frontend_path / item.name,
                                dirs_exist_ok=True
                            )

# Handles Python venv
def handle_venv() -> None:
    if not os.path.exists('.venv'):
        try:
            print(message("Creating virtual environment..."))
            subprocess.run(
                [sys.executable, '-m', 'venv', '.venv'],
                check=True
            )
            print(success("Virtual environment created"))
        except subprocess.CalledProcessError as err:
            raise SystemExit(
                error(
                    "An error ocurred during Python virtual environment configuration."
                    "Installation aborted"
                )
            ) from err
    else:
        c = question_loop("Do you want to reinstall venv? (y/N)")

        if c == 'y':
            print(message("Removing old virtual environment..."))

            shutil.rmtree('.venv')

            print(success(".venv successfully removed"))

            try:
                print(message("Creating new virtual environment..."))

                subprocess.run(
                    [sys.executable, '-m', 'venv', '.venv'],
                    check=True
                )

                print(success("New virtual environment created"))
            except subprocess.CalledProcessError as err:
                raise SystemExit(
                    error(
                        "An error ocurred during Python virtual environment configuration."
                        "Installation aborted"
                    )
                ) from err

# Handle backend dependencies
def install_backend_dep() -> None:
    python_exe = os.path.join(
        ROOT,
        '.venv'
        'Scripts' if PLATFORM == 'windows' else 'bin',
        'python.exe' if PLATFORM == 'windows' else 'python'
    )

    if os.path.exists(python_exe):
        try:
            print(message("Installing backend dependencies..."))

            subprocess.run(
                [
                    python_exe, '-m',
                    'pip', 'install',
                    '--no-cache-dir', '-r',
                    'requirements.txt'
                ],
                cwd='backend',
                check=True
            )

            print(success("Backend dependencies installed"))
        except Exception as err:
            raise SystemExit(
                error(f"Could not install dependencies -> {err}")
            ) from err
    else:
        raise SystemExit(error("Python virtual environment not created"))

def question_loop(quest: str) -> str:
    while True:
        c = input(warning(quest)).strip()

        if c in ('', 'N', 'n', 'Y', 'y'):
            return c.lower()

def install() -> None:
    check_system()

    if os.getcwd() != ROOT:
        os.chdir(ROOT)

    # Handle Python venv
    handle_venv()

    # create .env file
    create_envfile()

    # Handle backend dependencies
    install_backend_dep()

    # Install frontend package
    install_frontend()

if __name__ == "__main__":
    install()
