import sys
import os
import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import json
import openai 
import time
from imageGen import ImageGen
from datetime import datetime




client = None
imgClient = None

currentDir = ""
currentPath = ""
if getattr(sys, 'frozen', False):
    currentDir = os.path.dirname(sys.executable)
    currentPath = os.path.abspath(sys.executable)
else:
    currentDir = os.path.dirname(os.path.abspath(__file__))
    currentPath = os.path.abspath(__file__)


defaultConfigData = {
    "LLM_key": "sk-WpCb6vXleVk6djvQICFygFTzv3B7GFvCEIN9YSV1C9ydNKW5",
    "LLM_model": "gpt-4o-mini",
    "LLM_url": "https://api.chatanywhere.tech/v1", 
    "LLM_maxTries": 10, 
    "LLM_chunkSize": 1500,
    "LLM_ScriptLength": 5000,
    "Img_Key": "INJEE4EZhJb9uyiiD8W-lrcqjyGDGWIPayxqy3pLK5w",
    "Img_url": "https://api.poe.com/v1",
    "Img_model": "Gemini-2.5-Flash-Image",
    "Img_runLocal": True,
    "translate_to": "Chinese"
}
configData = None


def init():
    global defaultConfigData, configData, client, imgClient
    configFile = os.path.join(currentDir, "config.json")
    try:
        with open(configFile, 'r', encoding='utf-8') as file:
            configData = json.load(file)
            client = openai.OpenAI(api_key=configData["LLM_key"],base_url=configData["LLM_url"])
            imgClient = ImageGen(key=configData["Img_Key"],url=configData["Img_url"], runLocal=configData["Img_runLocal"],)
            imgClient.model = configData["Img_model"]
    except Exception as e:
        if os.path.exists(configFile):
            os.remove(configFile)
        print(f"\n! config.json is corrupted or does not exists, creating a defualt config.json....")
        with open(configFile, 'w', encoding='utf-8') as file:
            json.dump(defaultConfigData, file, ensure_ascii=False, indent=2)
        print("\n请确保config.json中的配置正确之后再重新运行")
        os.startfile(configFile)
        time.sleep(5)
        sys.exit()


def extract_youtube_video_id(url):
    # Regular expression for matching YouTube video URL
    regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com/(?:[^/]+/.*|(?:v|e(?:mbed)?|.+\?.*v)=)|(?:youtu\.be/))([\w-]{10,12})'
    match = re.search(regex, url)
    if match:
        return match.group(1)
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query).get('v', [None])[0]
    elif parsed_url.hostname == 'youtu.be':
        return parsed_url.path[1:]  # Remove leading '/'
    
    return None


def getContentFromLink(videoLink):
    ytt_api = YouTubeTranscriptApi()
    result = ytt_api.fetch(extract_youtube_video_id(videoLink), languages=["zh", "en"])
    content = ""
    for chunk in result.snippets:
        content += chunk.text
    return content

def send_prompt(content, max_tokens=3000, tries = 0):
    try:
        model = configData["LLM_model"]
        print(f"当前使用模型{model}")
        completion = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content":
f"你是一个视频分镜生成AI。根据输入的视频文稿,仅提取与主要话题相关的关键内容并生成分镜信息. 每个分镜应包含:\n"
+"""
1. `index`: 分镜序号, 从1开始
2. `voiceover`: 分镜的稿子内容(10到100字, 中文)
3. `image`: 分镜的图片描述(this needs to be written in English in the format of image generation prompt)

输出格式为 JSON 数组，如下：

{result: [
  {
    "index": 1,
    "voiceover": "分镜1稿子内容",
    "image": "分镜1图片描述"
  },
  {
    "index": 2,
    "voiceover": "分镜2稿子内容",
    "image": "分镜2图片描述"
  }
]}
"""},
                {
                    "role": "user",
                    "content": f"{content}"
                }
            ]
        )
        result = completion.choices[0].message.content

        try:
            result_ls = json.loads(result)
            result_ls = result_ls["result"]
            print("-------------------------------------")
            print(result)
            print("-------------------------------------")
        except Exception as e:
                print(f"! exception:{e}\nretrying{tries + 1}/{configData['maxTries']}...")
                return send_prompt(content, model=model, max_tokens=max_tokens, tries=tries+1)
        return result_ls
    except Exception as e:
        print(f"!_错误: {e}!_")
        return send_prompt(content, model=model, max_tokens=max_tokens, tries=tries+1)
    



def makeFolderPath():
    folderPath = os.path.join(currentDir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    return folderPath

def generateVoiceOver(content, folderPath):
    for voiceLine in content:
        if isinstance(voiceLine, dict):
            fileName = os.path.join(folderPath, f"{voiceLine['index']}.wav")
            voiceLine = voiceLine["voiceover"]
            voiceGen.generateVoice(voiceLine, fileName)
            print(voiceLine)

def generateImages(content, folderPath):
    for image in content:
        if isinstance(image, dict):
            imagePrompt = image["image"]
            fileName = os.path.join(folderPath, f"{image['index']}.png")
            print(imagePrompt)
            imgClient.generateImage(imagePrompt, fileName)

def findSources(folderPath):
    wav_files = []
    png_files = []
    
    # Traverse the directory to find .wav files
    for root, dirs, files in os.walk(folderPath):
        for file in files:
            if file.lower().endswith('.wav'):
                wavFile = os.path.join(root, file)
                wav_files.append(wavFile)
                pngFile = f"{os.path.splitext(wavFile)[0]}.png"
                if os.path.exists(pngFile):
                    png_files.append(pngFile)
    
    # Sort the files based on their numeric suffix
    wav_files.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))
    png_files.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))
    
    # Check if the number of files matches
    if len(wav_files) != len(png_files):
        print("! 图片和视频文件数量不同")
    
    return wav_files, png_files


init()
# videoLink = "https://www.youtube.com/watch?v=oK3JOfPFuGw"
# content = getContentFromLink(videoLink)
# print(f"{content}\n以上为提取到的内容")

# storyBoard = send_prompt(content)
# folderPath = makeFolderPath()
# print("\n\n开始生成语音")
# print("------------------------------")
#import voiceGen
# generateVoiceOver(storyBoard, folderPath)
# print("------------------------------")
# print("语音生成完毕")



# print("\n\n开始生成图片")
# print("------------------------------")
# generateImages(storyBoard, folderPath)
# print("------------------------------")
# print("图片生成完毕")

folderPath = os.path.join(currentDir, "yst")
audios, images = findSources(folderPath)
from moviepy.video.VideoClip import ImageClip

from moviepy.video.compositing import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import moviepy.audio.AudioClip



print("\n\n开始生成视频")
print("------------------------------")
# Lists of image and audio file paths (in matching order)


clips = []  # Store video clips
audioClips = []
for image_path, audio_path in zip(images, audios):
    audio = AudioFileClip(audio_path)
    img_clip = ImageClip(image_path, duration=audio.duration)
    img_clip.audio = audio
    clips.append(img_clip)
    # audioClips.append(audio)

# Concatenate all clips into one video
final_clip = CompositeVideoClip.concatenate_videoclips(clips, method='compose')
# final_clip_audio =  moviepy.audio.AudioClip.CompositeAudioClip(audioClips)

# Export the final video
final_clip.write_videofile(os.path.join(folderPath, "output.mp4"), fps=24, codec='libx264', audio_codec='aac')
print("------------------------------")
print("视频生成完毕")
