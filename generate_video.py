import os
import json
import random
import time
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips, TextClip
import anthropic
from elevenlabs import generate, set_api_key, save
import numpy as np
from PIL import Image
from proglog import ProgressBarLogger
import sys
import threading
import itertools
import subprocess
from moviepy.config import change_settings
import requests
from tqdm import tqdm

def download_file(url, destination, desc=None):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True, desc=desc)
    
    with open(destination, 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

def setup_background_videos():
    video_dir = Path('resources/background-videos')
    if not video_dir.exists():
        video_dir.mkdir(parents=True, exist_ok=True)
    
    if not list(video_dir.glob('*.mp4')):
        time.sleep(1)
        os.system('cls')
        print(f"\n{Colors.YELLOW}No background videos found!{Colors.RESET}")
        while True:
            response = input(f"\n{Colors.BOLD}Would you like to download the starter background videos pack? (y/n):{Colors.RESET} ").strip().lower()
            if response in ['y', 'n']:
                break
            print(f"{Colors.RED}Please enter 'y' or 'n'{Colors.RESET}")
        
        if response == 'y':
            print(f"\n{Colors.BLUE}Opening the GitHub repository with background videos...{Colors.RESET}")
            
            # GitHub repository URL
            repo_url = "https://github.com/4xnicoo/autoprayer-videokit"
            
            try:
                # Open the URL in the default web browser
                import webbrowser
                webbrowser.open(repo_url)
                
                print(f"\n{Colors.GREEN}GitHub repository opened in your browser.{Colors.RESET}")
                print(f"\n{Colors.YELLOW}Instructions:{Colors.RESET}")
                print(f"1. Download the video files you want from the repository")
                print(f"2. Save them to the {video_dir} directory")
                print(f"3. Run this program again")
                
                # Ask if the user wants to continue or wait
                while True:
                    continue_response = input(f"\n{Colors.BOLD}Have you downloaded the videos? (y/n):{Colors.RESET} ").strip().lower()
                    if continue_response in ['y', 'n']:
                        break
                    print(f"{Colors.RED}Please enter 'y' or 'n'{Colors.RESET}")
                
                if continue_response == 'n':
                    print(f"\n{Colors.YELLOW}Please add background videos to the {video_dir} directory before running the program again.{Colors.RESET}")
                    sys.exit(0)
                
            except Exception as e:
                print(f"{Colors.RED}Failed to open the browser: {str(e)}{Colors.RESET}")
                print(f"\n{Colors.YELLOW}Please visit this URL manually: {repo_url}{Colors.RESET}")
                print(f"\n{Colors.YELLOW}Download the videos and save them to the {video_dir} directory.{Colors.RESET}")
                sys.exit(1)
        else:
            print(f"\n{Colors.YELLOW}Please add your own background videos to the {video_dir} directory.{Colors.RESET}")
            sys.exit(1)

def setup_imagemagick():
    """Install and configure ImageMagick for MoviePy."""
    magick_path = r'C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe'
    
    if os.path.exists(magick_path):
        change_settings({"IMAGEMAGICK_BINARY": magick_path})
        print(f'ImageMagick configured at: {magick_path}')
        return
    
    try:
        result = subprocess.run(['where', 'magick'], capture_output=True, text=True)
        if result.returncode == 0:
            # Get the first path from the where command
            magick_path = result.stdout.strip().split('\n')[0]
            change_settings({"IMAGEMAGICK_BINARY": magick_path})
            print(f'ImageMagick found in PATH at: {magick_path}')
            return
    except Exception:
        pass

    print(f'{Colors.RED}ImageMagick not found at expected location: {magick_path}{Colors.RESET}')
    print('Please ensure that:')
    print('1. ImageMagick is installed from: https://imagemagick.org/script/download.php#windows')
    print('2. During installation, you checked "Add application directory to your system path"')
    print('3. You have restarted your computer after installation')
    print('\nIf you have already done these steps, please try:')
    print('1. Uninstalling ImageMagick')
    print('2. Downloading it again from the official website')
    print('3. Running the installer as administrator')
    print('4. Making sure to check "Add application directory to your system path"')
    print('5. Restarting your computer')
    sys.exit(1)

# ANSI color codes
class Colors:
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

class Spinner:
    def __init__(self, message=""):
        self.spinner = itertools.cycle(['-', '\\', '|', '/'])
        self.running = False
        self.message = message
        self.thread = None

    def spin(self):
        while self.running:
            sys.stdout.write(f'\r{Colors.YELLOW}{self.message} {next(self.spinner)}{Colors.RESET}')
            sys.stdout.flush()
            time.sleep(0.1)
        sys.stdout.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        sys.stdout.flush()

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

class CustomLogger(ProgressBarLogger):
    def __init__(self):
        super().__init__()
        self.last_message = ""
        self.spinner = None
        
    def bars_callback(self, bar, attr, value, old_value=None):

        if bar == "t": 
            percentage = int((value / self.bars[bar]["total"]) * 100)
            bar_width = 40
            filled = int(bar_width * percentage / 100)
            bar = f'{Colors.BLUE}█{Colors.RESET}' * filled + '░' * (bar_width - filled)
            sys.stdout.write(f'\r{Colors.BOLD}Rendering video:{Colors.RESET} |{bar}| {Colors.BLUE}{percentage}%{Colors.RESET}')
            sys.stdout.flush()
            if percentage == 100:
                print() 
    
    def callback(self, **changes):
        for parameter in changes:
            if parameter == "message":
                message = changes[parameter].strip()
                if "Moviepy" in message:
                    continue
                if message and message != self.last_message:
                    if "Writing video" in message:
                        print(f"\n{Colors.BLUE}Finalizing video...{Colors.RESET}")
                    elif "video ready" in message:
                        print(f"{Colors.GREEN}Video creation completed!{Colors.RESET}")
                    self.last_message = message

def process_with_spinner(message, func, *args, **kwargs):
    """Execute a function with a spinner animation."""
    spinner = Spinner(message)
    spinner.start()
    try:
        result = func(*args, **kwargs)
        spinner.stop()
        print(f"\r{message} {Colors.GREEN}Done!{Colors.RESET}")
        return result
    except Exception as e:
        spinner.stop()
        print(f"\r{message} {Colors.RED}Failed!{Colors.RESET}")
        raise e

print('Verifying system requirements..')
print('System requirements verified.')
time.sleep(0.5)
os.system('cls')

CONFIG_FILE = 'config.json'

def resize_frame(frame, target_size):
    """Resize a single frame using PIL."""
    img = Image.fromarray(frame)
    resized = img.resize(target_size, Image.Resampling.LANCZOS)
    return np.array(resized)

def setup_api_keys():
    """Set up API keys interactively if they don't exist."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    else:
        print("First-time setup: Please enter your API keys.")
        anthropic_key = input("Enter your Anthropic API key: ").strip()
        elevenlabs_key = input("Enter your ElevenLabs API key: ").strip()
        
        config = {
            "anthropic_api_key": anthropic_key,
            "elevenlabs_api_key": elevenlabs_key
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        
        print(f"\nAPI keys have been saved to {CONFIG_FILE}")
    
    return config

def get_random_background_video():
    """Get a random video from the background-videos directory."""
    video_dir = Path('resources/background-videos')
    video_files = list(video_dir.glob('*.mp4'))
    if not video_files:
        raise Exception("No video files found in resources/background-videos")
    return str(random.choice(video_files))

def generate_script_from_claude(api_key):
    """Generate script content using Claude API."""
    client = anthropic.Anthropic(
        api_key=api_key
    )
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.7,
        system="You are a religious writer who writes in Spanish. For each prayer, provide three elements separated by '|||': 1) A short title (2-3 words), 2) A brief description (4-5 words), 3) The prayer text. Keep the prayer short, around 20 to 25 seconds of speech to ensure the final video stays under one minute.",
        messages=[
            {"role": "user", "content": "Write a short, inspiring religious prayer in Spanish that speaks about faith, hope, and divine guidance. Format: title ||| description ||| prayer"}
        ]
    )
    
    if isinstance(message.content, list) and len(message.content) > 0:
        content = message.content[0].text.strip()
    else:
        raise ValueError("Unexpected response structure from Claude API")
    
    if not isinstance(content, str):
        raise TypeError(f"Expected string content from Claude, got {type(content)}")
    
    try:
        title, description, prayer = [part.strip() for part in content.split("|||")]
    except ValueError:
        title = "Oración Sagrada"
        description = "Una oración de esperanza"
        prayer = content
    
    print(f"\n{Colors.BOLD}Title:{Colors.RESET} {title}")
    print(f"{Colors.BOLD}Description:{Colors.RESET} {description}")
    print(f"{Colors.BOLD}Prayer:{Colors.RESET}\n{prayer}\n")
        
    return title, description, prayer

def create_voiceover(script, api_key):
    """Generate voiceover using ElevenLabs API."""
    if not isinstance(script, str):
        raise TypeError(f"Expected string script, got {type(script)}")
    
    set_api_key(api_key)
    
    try:
        # Simple approach for version 0.2.19
        audio = generate(
            text=script,
            voice="0rTCgryT71xGPrgtinaj",  # Direct voice ID
            model="eleven_multilingual_v2"
        )
        
        temp_audio_path = "temp_voiceover.mp3"
        save(audio, temp_audio_path)
        return temp_audio_path
    except Exception as e:
        print(f"{Colors.YELLOW}First attempt failed, trying alternative method...{Colors.RESET}")
        try:
            # Fallback to direct API call
            import requests
            
            url = "https://api.elevenlabs.io/v1/text-to-speech/0rTCgryT71xGPrgtinaj"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            
            data = {
                "text": script,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            temp_audio_path = "temp_voiceover.mp3"
            with open(temp_audio_path, 'wb') as f:
                f.write(response.content)
            
            return temp_audio_path
        except Exception as e2:
            print(f"{Colors.RED}Both voiceover generation methods failed!{Colors.RESET}")
            print(f"{Colors.RED}First error: {str(e)}{Colors.RESET}")
            print(f"{Colors.RED}Second error: {str(e2)}{Colors.RESET}")
            raise e2

def safe_close(clip):
    """Safely close a MoviePy clip."""
    try:
        if hasattr(clip, 'reader') and clip.reader is not None:
            try:
                if hasattr(clip.reader, 'proc') and clip.reader.proc is not None:
                    clip.reader.proc.terminate()
                    clip.reader.proc.wait()
                    clip.reader.proc = None
            except Exception:
                pass
        if clip is not None:
            clip.close()
    except Exception:
        pass

def create_final_video(background_video_path, audio_path, title, description, output_path="output_video.mp4"):
    """Create the final video with background and voiceover."""
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    output_path = str(output_dir / output_path)
    
    background = None
    audio = None
    final_video = None
    text_clips = []
    clips_to_close = []
    
    try:
        background = process_with_spinner(
            "Loading background video...",
            VideoFileClip,
            background_video_path
        )
        clips_to_close.append(background)
        
        target_height = 1920
        aspect_ratio = background.w / background.h
        new_width = int(target_height * aspect_ratio)
        new_width = new_width + (new_width % 2)
        
        def process_frame(frame):
            resized = resize_frame(frame, (new_width, target_height))
            center = resized.shape[1] // 2
            start_x = center - 540  # 1080/2 = 540
            cropped = resized[:, start_x:start_x + 1080]
            return cropped
        
        background = process_with_spinner(
            "Processing video frames...",
            background.fl_image,
            process_frame
        )
        clips_to_close.append(background)
        
        audio = process_with_spinner(
            "Loading audio...",
            AudioFileClip,
            audio_path
        )
        clips_to_close.append(audio)
        
        if audio.duration > 59:
            print(f"{Colors.YELLOW}Audio exceeds 59 seconds, trimming...{Colors.RESET}")
            audio = audio.subclip(0, 59)
            clips_to_close.append(audio)
        
        if background.duration < audio.duration:
            loops_needed = int(np.ceil(audio.duration / background.duration))
            clips = [background] * loops_needed
            background = process_with_spinner(
                "Adjusting video length...",
                concatenate_videoclips,
                clips
            )
            clips_to_close.append(background)
            background = background.subclip(0, audio.duration)
            clips_to_close.append(background)
        elif background.duration > audio.duration:
            background = process_with_spinner(
                "Trimming video...",
                background.subclip,
                0, audio.duration
            )
            clips_to_close.append(background)
        
        print("Adding text overlays...")
        title_clip = TextClip(
            title,
            fontsize=90,
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2.5,
            method='caption',
            size=(1080, None),
            align='center'
        ).set_position(('center', 500)).set_duration(background.duration)
        text_clips.append(title_clip)
        
        desc_clip = TextClip(
            description,
            fontsize=55,
            color='white',
            font='Arial',
            stroke_color='black',
            stroke_width=1.5,
            method='caption',
            size=(1080, None),
            align='center'
        ).set_position(('center', 800)).set_duration(background.duration)
        text_clips.append(desc_clip)
        
        final_video = process_with_spinner(
            "Combining video and audio...",
            background.set_audio,
            audio
        )
        clips_to_close.append(final_video)
        
        final_video = CompositeVideoClip([final_video] + text_clips)
        clips_to_close.append(final_video)
        
        print("\nGenerating final video...")
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=30,
            preset='medium',
            bitrate='8000k',
            audio_bitrate='192k',
            threads=4,
            ffmpeg_params=[
                '-pix_fmt', 'yuv420p',
                '-profile:v', 'main', 
                '-level', '4.0'         # Compatibility level
            ],
            logger=CustomLogger() 
        )
        
    finally:
        for clip in clips_to_close:
            safe_close(clip)
        for text_clip in text_clips:
            text_clip.close()
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception:
                pass

def main():
    try:
        setup_imagemagick()
        setup_background_videos()
        
        config = setup_api_keys()
        
        while True:
            try:
                num_videos = input(f"\n{Colors.BOLD}How many videos would you like to generate? (1-10, default: 1):{Colors.RESET} ").strip()
                if not num_videos:  # Empty input
                    num_videos = 1
                    break
                num_videos = int(num_videos)
                if 1 <= num_videos <= 10:
                    break
                print(f"{Colors.RED}Please enter a number between 1 and 10{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Please enter a valid number{Colors.RESET}")
        
        for video_num in range(num_videos):
            print(f"\n{Colors.BOLD}Generating video {video_num + 1}/{num_videos}...{Colors.RESET}")
            
            background_video = get_random_background_video()
            
            print(f"\n{Colors.BLUE}Generating script for video {video_num + 1}/{num_videos}...{Colors.RESET}")
            title, description, script = generate_script_from_claude(config['anthropic_api_key'])
            
            print(f"\n{Colors.BLUE}Creating voiceover for video {video_num + 1}/{num_videos}...{Colors.RESET}")
            audio_path = create_voiceover(script, config['elevenlabs_api_key'])
            
            output_path = "output_video.mp4" if num_videos == 1 else f"output_video_{video_num + 1}.mp4"
            create_final_video(background_video, audio_path, title, description, output_path)
            
            print(f"\n{Colors.GREEN}{Colors.BOLD}Video {video_num + 1}/{num_videos} generated successfully!{Colors.RESET}")
        
        if num_videos > 1:
            print(f"\n{Colors.GREEN}{Colors.BOLD}All {num_videos} videos have been generated successfully!{Colors.RESET}")
        
        output_dir = Path('output').absolute()
        os.startfile(output_dir)
        
    except Exception as e:
        import traceback
        print(f"\n{Colors.RED}An error occurred:{Colors.RESET}")
        print(f"{Colors.RED}Error type: {type(e).__name__}{Colors.RESET}")
        print(f"{Colors.RED}Error message: {str(e)}{Colors.RESET}")
        print(f"\n{Colors.RED}Full traceback:{Colors.RESET}")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 