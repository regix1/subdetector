# Subtitle Detector

A tool to detect the language of subtitles in media files and standalone subtitle files.

## Features

- Detect languages in embedded subtitles (VOB, ASS, PGS)
- Analyze standalone subtitle files
- Support for multiple subtitle tracks
- Works with text-based and image-based subtitles
- Uses metadata when available, falls back to content detection

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

### Basic Commands

```bash
# Analyze all subtitle tracks in a media file
subdetector movie.mkv

# Analyze a specific subtitle track (by index)
subdetector movie.mkv -t 2

# Analyze a standalone subtitle file
subdetector subtitle.srt
```

### Command-Line Options

```
usage: subdetector [-h] [-t TRACK] file

Detect subtitle languages in media files or subtitle files

positional arguments:
  file                  Media file or subtitle file path

optional arguments:
  -h, --help            show this help message and exit
  -t TRACK, --track TRACK
                        Specific subtitle track index to analyze (for media files only)
```

## Examples

### Analyzing a Media Container with Multiple Subtitle Tracks

```bash
$ subdetector movie.mkv
Detecting subtitle language in: movie.mkv

Results:
Stream #2 (subrip): en [metadata]
Stream #3 (ass): fr [text-detection]
Stream #4 (hdmv_pgs_subtitle): ja [ocr-detection]
```

### Analyzing a Specific Subtitle Track

```bash
$ subdetector movie.mkv -t 3
Detecting subtitle language in: movie.mkv

Results:
Stream #3 (ass): fr [text-detection]
```

### Analyzing a Standalone Subtitle File

```bash
$ subdetector english_subtitles.srt
Detecting subtitle language in: english_subtitles.srt

Results:
Subtitle file (srt): en [text-detection]
```

## Supported Formats

- **Text-based subtitles**:
  - SubRip (`.srt`)
  - Advanced SubStation Alpha (`.ass`)
  - SubStation Alpha (`.ssa`)
  - WebVTT (`.vtt`)

- **Image-based subtitles**:
  - HDMV Presentation Graphic Stream (`.sup`, `.pgs`)
  - DVD-Video Object (`.sub`, `.idx`)

## Detection Method

The tool uses several methods to detect the subtitle language:

1. **Metadata Detection**: Checks if the language is specified in the file's metadata.
2. **Text Detection**: For text-based subtitles, analyzes the subtitle content.
3. **OCR Detection**: For image-based subtitles, performs OCR on extracted frames.

## Troubleshooting

### No Subtitle Tracks Found

If the tool reports no subtitle tracks found:
- For MKV files: Ensure subtitles are properly muxed.
- For standalone files: Check if the file is corrupted.

### Unknown Language

If the language is reported as "Unknown":
- For text subtitles: The subtitle may have too little text or highly specialized terminology.
- For image subtitles: OCR may have failed due to complex fonts or background.

### FFmpeg or Tesseract Errors

Ensure that both FFmpeg and Tesseract OCR are properly installed and in your PATH.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT