import sys
import os
import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import json
import openai 
import time


client = None
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
    "translate_to": "Chinese"
}
configData = None


def init():
    global defaultConfigData, configData, client
    configFile = os.path.join(currentDir, "config.json")
    try:
        with open(configFile, 'r', encoding='utf-8') as file:
            configData = json.load(file)
            client = openai.OpenAI(api_key=configData["LLM_key"],base_url=configData["LLM_url"])
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
3. `image`: 分镜的图片描述

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
                print(f"! exception:{e}\nretrying{tries + 1}/{configData["maxTries"]}...")
                return send_prompt(content, model=model, max_tokens=max_tokens, tries=tries+1)
        return result_ls
    except Exception as e:
        print(f"!_错误: {e}!_")
        return send_prompt(content, model=model, max_tokens=max_tokens, tries=tries+1)
    




def generateVoiceOver(content):
    for voiceLine in content:
        if isinstance(voiceLine, dict):
            voiceLine = voiceLine["voiceover"]
        print(voiceLine)
    pass

def generateImages(content):
    pass

init()
videoLink = "https://www.youtube.com/watch?v=ePctDtjShfA"
content = getContentFromLink(videoLink)
print(f"{content}\n以上为提取到的内容")

storyBoard = send_prompt(content)

generateVoiceOver(storyBoard)


