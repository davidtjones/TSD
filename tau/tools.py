import requests
import zipfile
from pathlib import Path
import os
import platform
from io import BytesIO


def download_and_unpack_font(font_name="Roboto", font_url="https://fonts.google.com/download?family=Roboto"):
    if platform.system() == "Windows":
        data_dir = Path(os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA'))
    elif platform.system() == "Linux":
        data_dir = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))
    else:
        raise NotImplementedError(f"No implementation for OS: {platform.system()}")
    
    font_dir = data_dir / 'tau' / 'fonts'
    font_dir.mkdir(parents=True, exist_ok=True)

    font_path = font_dir / f'{font_name}-Regular.ttf'
    if font_path.exists():
        return str(font_path)
    
    # Download the font
    try:
        print("Getting font...")
        response = requests.get(font_url)
        response.raise_for_status()
        zip_file = zipfile.ZipFile(BytesIO(response.content))

        # Extract the needed font file
        for file_name in zip_file.namelist():
            if file_name.endswith('Roboto-Regular.ttf'):
                zip_file.extract(file_name, font_dir)

                extracted_font_path = font_dir / file_name
                extracted_font_path.rename(font_path)
                break
    except Exception as e:
        raise RuntimeError(f"Failed to download or unpack the font: {e}")
    
    return str(font_path)
    
