# Subtitle Detector

A tool to detect the language of subtitles in media files.

## Features

- Detect languages in embedded subtitles (VOB, ASS, PGS)
- Analyze standalone subtitle files
- Support for multiple subtitle tracks

## Installation

```bash
pip install subdetector
```

## System Requirements

Before using subdetector, install the required system dependencies:

### Ubuntu/Debian
```bash
sudo apt install ffmpeg tesseract-ocr
```

### macOS
```bash
brew install ffmpeg tesseract
```

### Windows
Download and install:
- [FFmpeg](https://ffmpeg.org/download.html)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)

## Usage

```bash
# Analyze all subtitle tracks in a media file
subdetector movie.mkv

# Analyze a specific subtitle track
subdetector movie.mkv -t 2

# Analyze a standalone subtitle file
subdetector subtitle.srt
```

## License

MIT