import os
import platform
from pathlib import Path

import requests


class FontHandler:
    def __init__(self):
        if platform.system() == "Windows":
            self.data_dir = Path(
                os.environ.get("APPDATA") or os.environ.get("LOCALAPPDATA")
            )
        elif platform.system() == "Linux":
            self.data_dir = Path(
                os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")
            )
        else:
            raise NotImplementedError(f"No implementation for OS: {platform.system()}")

        self.font_dir = self.data_dir / "textmark" / "fonts"
        self.font_dir.mkdir(parents=True, exist_ok=True)
        self.font_cache = {}

        self.font_urls = {
            "NotoSans": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSans/unhinted/otf/NotoSans-Regular.otf",
            "NotoSansSC": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansCJKsc-Regular.otf",
            "NotoSansJP": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf",
            "NotoSansKR": "https://github.com/notofonts/noto-cjk/raw/main/Sans/OTF/Korean/NotoSansCJKkr-Regular.otf",
            "NotoSansBengali": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansBengali/unhinted/otf/NotoSansBengali-Regular.otf",
            "NotoSansDevanagari": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansDevanagari/unhinted/otf/NotoSansDevanagari-Regular.otf",
            "NotoSansArarbic": "https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansArabic/unhinted/otf/NotoSansArabic-Regular.otf",
        }

    def get_font(self, font_name):
        # Check cache first
        if font_name in self.font_cache:
            return self.font_cache[font_name]

        # Dynamically determine the font file extension
        for extension in [".ttf", ".otf"]:
            font_path = self.font_dir / f"{font_name}{extension}"
            if font_path.exists():
                self.font_cache[font_name] = font_path  # Cache the path
                return font_path

        print(f"Font {font_name} not found, downloading...")
        self._download_font(font_name)

        # After download, return the path
        downloaded_font_path = (
            self.font_dir / f"{font_name}{Path(self.font_urls[font_name]).suffix}"
        )
        self.font_cache[font_name] = downloaded_font_path  # Cache the path
        return downloaded_font_path

    def _download_font(self, font_name):
        url = self.font_urls.get(font_name)
        if not url:
            raise ValueError(f"Font URL for {font_name} not found.")

        file_extension = Path(url).suffix
        file_path = self.font_dir / f"{font_name}{file_extension}"

        if file_path.exists():
            print(f"Font {font_name} already exists.")
            return

        print(f"Downloading {font_name}...")
        response = requests.get(url)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)
