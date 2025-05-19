#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
import json
import re
from langdetect import detect
import pytesseract
from PIL import Image
import argparse

def extract_subtitle_track(media_file, stream_index, output_dir):
    """Extract a subtitle track from media file"""
    format_ext = {
        'ass': 'ass',
        'subrip': 'srt',
        'hdmv_pgs_subtitle': 'sup',
        'dvd_subtitle': 'sub'
    }
    
    stream_info = get_stream_info(media_file, stream_index)
    codec_name = stream_info.get('codec_name', '')
    ext = format_ext.get(codec_name, 'sub')
    
    output_file = os.path.join(output_dir, f"track_{stream_index}.{ext}")
    
    cmd = [
        "ffmpeg", "-i", media_file, 
        "-map", f"0:{stream_index}", 
        "-c", "copy", 
        output_file
    ]
    
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_file if os.path.exists(output_file) else None

def get_stream_info(media_file, stream_index):
    """Get detailed info about a specific stream"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", 
           "-show_streams", "-select_streams", str(stream_index), media_file]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = json.loads(result.stdout)
    
    if 'streams' in data and len(data['streams']) > 0:
        return data['streams'][0]
    return {}

def get_subtitle_streams(media_file):
    """Get all subtitle streams from media file"""
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", 
           "-show_streams", "-select_streams", "s", media_file]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    data = json.loads(result.stdout)
    
    return data.get('streams', [])

def detect_text_subtitle_language(subtitle_file):
    """Detect language for text-based subtitles"""
    try:
        with open(subtitle_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except:
        try:
            # Try another common encoding
            with open(subtitle_file, 'r', encoding='latin-1', errors='replace') as f:
                content = f.read()
        except:
            return None
        
    # Strip formatting for ASS/SSA files
    if subtitle_file.endswith(('.ass', '.ssa')):
        # Remove header
        if '[Events]' in content:
            content = content.split('[Events]')[1]
        
        # Extract only dialogue text
        dialogue_pattern = r'Dialogue:[^,]*(?:,[^,]*){8},([^\n]*)'
        dialogue_matches = re.findall(dialogue_pattern, content)
        
        if dialogue_matches:
            # Strip formatting codes like {\an8} or {\i1}
            clean_text = re.sub(r'{\\[^}]*}', '', ' '.join(dialogue_matches))
            content = clean_text
    
    # Use longest lines for better detection
    lines = [line for line in content.split('\n') if len(line) > 20]
    if not lines:
        lines = [line for line in content.split('\n') if line.strip()]
    
    sample = '\n'.join(lines[:20])  # Use first 20 substantial lines
    
    if not sample.strip():
        return None
    
    try:
        return detect(sample)
    except:
        return None

def extract_images_from_pgs(sup_file, output_dir, max_frames=10):
    """Extract image frames from PGS/SUP file"""
    output_pattern = os.path.join(output_dir, 'frame_%04d.png')
    
    cmd = [
        "ffmpeg", "-i", sup_file,
        "-vf", "select='eq(pict_type,I)'",
        "-vsync", "0",
        "-frames:v", str(max_frames),
        output_pattern
    ]
    
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return sorted(Path(output_dir).glob('frame_*.png'))

def detect_image_subtitle_language(subtitle_file, temp_dir):
    """Detect language for image-based subtitles (VOB, PGS)"""
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    # Extract frames
    frames = extract_images_from_pgs(subtitle_file, frames_dir)
    
    if not frames:
        return None
    
    # OCR each frame and collect text
    all_text = []
    for frame_path in frames[:5]:  # Limit to first 5 frames
        try:
            img = Image.open(frame_path)
            text = pytesseract.image_to_string(img)
            if text.strip():
                all_text.append(text)
        except Exception as e:
            print(f"OCR error: {e}")
    
    combined_text = "\n".join(all_text)
    
    if not combined_text.strip():
        return None
    
    try:
        return detect(combined_text)
    except:
        return None

def is_media_file(file_path):
    """Check if file is a media container or standalone subtitle"""
    # Common media container extensions
    media_extensions = ['.mkv', '.mp4', '.avi', '.mov', '.m4v', '.ts', '.mpg', '.mpeg', '.vob', '.iso']
    # Standalone subtitle extensions
    subtitle_extensions = ['.srt', '.ass', '.ssa', '.sub', '.sup', '.idx', '.pgs']
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # First, try to probe with ffprobe to see if it's a media file
    cmd = ["ffprobe", "-v", "error", file_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # If ffprobe returns non-zero, or the file has a subtitle extension, it's likely a subtitle
    if result.returncode != 0 or ext in subtitle_extensions:
        return False
    
    return True

def detect_subtitle_format(subtitle_file):
    """Detect the format of a subtitle file"""
    ext = os.path.splitext(subtitle_file)[1].lower()
    
    # Try to determine by extension
    if ext in ['.srt', '.vtt']:
        return 'text'
    elif ext in ['.ass', '.ssa']:
        return 'text'
    elif ext in ['.sup', '.pgs']:
        return 'image'
    elif ext in ['.sub', '.idx']:
        # VOB/SUB could be either binary or text format
        try:
            with open(subtitle_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(1000)  # Read first 1000 chars
                # If it contains readable text, likely a text subtitle
                if re.search(r'[a-zA-Z]{5,}', content):
                    return 'text'
        except:
            pass
        return 'image'
    
    # Fallback: try to open as text
    try:
        with open(subtitle_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read(1000)
            if re.search(r'[a-zA-Z]{5,}', content):
                return 'text'
    except:
        pass
    
    # Default to image if can't determine
    return 'image'

def detect_subtitle_languages(media_file, track_index=None):
    """Detect languages for subtitle tracks in media file or standalone subtitle"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Check if it's a media file or a subtitle file
        if is_media_file(media_file):
            subtitle_streams = get_subtitle_streams(media_file)
            
            # Filter for specific track if requested
            if track_index is not None:
                subtitle_streams = [s for s in subtitle_streams if s['index'] == track_index]
            
            if not subtitle_streams:
                return []
            
            results = []
            for stream in subtitle_streams:
                stream_index = stream['index']
                codec_name = stream.get('codec_name', '')
                
                # Check if language is in metadata
                language = None
                if 'tags' in stream and 'language' in stream['tags']:
                    language = stream['tags']['language']
                    source = 'metadata'
                else:
                    # Extract and detect
                    subtitle_file = extract_subtitle_track(media_file, stream_index, temp_dir)
                    
                    if subtitle_file:
                        if codec_name in ['ass', 'subrip', 'srt']:
                            language = detect_text_subtitle_language(subtitle_file)
                            source = 'text-detection'
                        elif codec_name in ['hdmv_pgs_subtitle', 'dvd_subtitle']:
                            language = detect_image_subtitle_language(subtitle_file, temp_dir)
                            source = 'ocr-detection'
                        else:
                            language = None
                            source = 'unknown-format'
                
                results.append({
                    'stream_index': stream_index,
                    'format': codec_name,
                    'language': language,
                    'source': source
                })
        else:
            # It's a standalone subtitle file
            subtitle_format = detect_subtitle_format(media_file)
            
            language = None
            if subtitle_format == 'text':
                language = detect_text_subtitle_language(media_file)
                source = 'text-detection'
            else:
                language = detect_image_subtitle_language(media_file, temp_dir)
                source = 'ocr-detection'
            
            results = [{
                'stream_index': 0,
                'format': os.path.splitext(media_file)[1][1:],  # extension without dot
                'language': language,
                'source': source
            }]
            
        return results

def main():
    parser = argparse.ArgumentParser(description='Detect subtitle languages in media files or subtitle files')
    parser.add_argument('file', help='Media file or subtitle file path')
    parser.add_argument('-t', '--track', type=int, help='Specific subtitle track index to analyze (for media files only)')
    args = parser.parse_args()
    
    file_path = args.file
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' does not exist")
        sys.exit(1)
    
    print(f"Detecting subtitle language in: {file_path}")
    languages = detect_subtitle_languages(file_path, args.track)
    
    if not languages:
        print("No subtitle tracks found or specified track index doesn't exist")
        sys.exit(1)
    
    print("\nResults:")
    for track in languages:
        if is_media_file(file_path):
            print(f"Stream #{track['stream_index']} ({track['format']}): " +
                  f"{track['language'] or 'Unknown'} [{track['source']}]")
        else:
            print(f"Subtitle file ({track['format']}): " +
                  f"{track['language'] or 'Unknown'} [{track['source']}]")

if __name__ == "__main__":
    main()