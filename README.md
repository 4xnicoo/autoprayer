# AutoPrayer Video Generator

Automatically generate beautiful vertical prayer videos with voiceovers in Spanish. This project combines background videos with AI-generated prayers and professional voiceovers.
> [!NOTE]  
> This program utilizes experimental AI technology. This is a side project, it may be unstable. Use at your own risk.
## Features

- Generate one or multiple prayer videos
- AI-generated prayers in Spanish using Claude
- Professional voiceover using ElevenLabs
- Beautiful text overlays with title and description
- Vertical video format (1080x1920) perfect for social media
- Automatic video resizing and cropping
- Progress indicators and spinners for better UX

## Requirements

- Python 3.12.5
- ImageMagick - [Download Here](https://imagemagick.org/script/download.php#windows)
- Anthropic API key (for Claude)
- ElevenLabs API key (for voiceover)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/AutoPrayer.git
cd AutoPrayer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ImageMagick from: https://imagemagick.org/script/download.php#windows
   - Make sure to check "Add application directory to your system path" during installation

4. Create a `resources/background-videos` directory and add your background videos (mp4 format)

## Configuration

On first run, you'll be prompted to enter your API keys:
   - Anthropic API key for Claude
   - ElevenLabs API key for voiceover generation

You can generate API keys at: [Anthropic Console](https://console.anthropic.com/settings/keys) | [ElevenLabs](https://elevenlabs.io/app/settings/api-keys)
> [!WARNING]  
> Anthropic and ElevenLabs API has usage costs. Although small, the usage costs can become expensive quickly. We are not responsible for any software failures resulting in elevated API costs/usage.

You will need to add .mp4 videos to the `resources/background-videos` folder.
If you do not have any, you can download the default videos pack (type Y on startup prompt.)
> [!TIP]  
> When uploading your own video, ensure it is 1080x1920 9:16 (short-form video format).



These will be saved in `config.json` for future use.

## Usage

Run the script:
```bash
python generate_video.py
```

The script will:
1. Ask how many videos you want to generate (1-10)
2. Generate unique prayers using Claude
3. Create voiceovers using ElevenLabs
4. Combine with random background videos
5. Add text overlays
6. Save the final videos in the `output` folder

## Output

Generated videos will be:
   - Saved in the `output` directory
   - Format: 1080x1920 (vertical)
   - Compatible with most video players and social media platforms
   - Named as `output_video.mp4` or `output_video_1.mp4`, `output_video_2.mp4`, etc. for multiple videos

>[!CAUTION]
>*Please double-check any videos before making them public. We are not responsible for any offensive content. Remember, this is AI-powered, and AI makes mistakes.*
