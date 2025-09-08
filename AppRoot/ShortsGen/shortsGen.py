import sys
import os
import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
import json
import openai 
import time
from imageGen import ImageGen
from voiceGen import VoiceGen
from datetime import datetime
import videoEditor
import shutil




client = None
imgClient = None
voiceClient = None

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
    "LLM_maxToken": 5000,
    "Img_Key": "INJEE4EZhJb9uyiiD8W-lrcqjyGDGWIPayxqy3pLK5w",
    "Img_url": "https://api.poe.com/v1",
    "Img_model": "Gemini-2.5-Flash-Image",
    "Img_runLocal": False,
    "Voice_Key": "INJEE4EZhJb9uyiiD8W-lrcqjyGDGWIPayxqy3pLK5w",
    "Voice_url": "https://api.poe.com/v1",
    "Voice_model": "Hailuo-Speech-02",
    "Voice_runLocal": False,
    "custom_storyPath": None
}

defaultStoryPrompt = """
你是一个分镜创作专家。根据输入的视频文稿,提取与主要话题相关的内容并撰写分镜信息
重要规则:
1. 确保完整和详细性
2. 不同分镜的台词需要逻辑衔接通畅 
3. 当有特殊名词或人物首次出现时, 应先做出介绍

输出格式为一个JSON 数组，包含以下信息:
1. `index`: 分镜序号, 从1开始
2. `voiceover`: 分镜的稿子内容(10到300字, 稿子内容需要为中文, )
3. `image`: 分镜的图片描述(this needs to be written in English in the format of image generation prompts)

格式参考：
{"result": [
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
"""

defaultImagePrompt = "生成涂鸦插画风格的图片"
storyPrompt = None
configData = None
outputPath_storyBoard = currentDir


def init():
    global defaultConfigData, configData, client, imgClient, storyPrompt, voiceClient, outputPath_storyBoard
    configFile = os.path.join(currentDir, "config.json")
    promptFile_story = os.path.join(currentDir, "prompt_分镜.txt")
    promptFile_image = os.path.join(currentDir, "prompt_图片.txt")
    try:
        with open(configFile, 'r', encoding='utf-8') as file:
            configData = json.load(file)
            client = openai.OpenAI(api_key=configData["LLM_key"],base_url=configData["LLM_url"])
            imgClient = ImageGen(key=configData["Img_Key"],url=configData["Img_url"], runLocal=configData["Img_runLocal"])
            imgClient.model = configData["Img_model"]
            voiceClient = VoiceGen(key=configData["Voice_Key"],url=configData["Voice_url"], runLocal=configData["Voice_runLocal"])
            voiceClient.model = configData["Voice_model"]
            if configData["custom_storyPath"] != None:
                outputPath_storyBoard =configData["custom_storyPath"]
                print(f"**分镜会导出到:{outputPath_storyBoard}")
    except Exception as e:
        if os.path.exists(configFile):
            os.remove(configFile)
        print(f"\n! config.json is corrupted or does not exists, creating a defualt config.json....")
        with open(configFile, 'w', encoding='utf-8') as file:
            json.dump(defaultConfigData, file, ensure_ascii=False, indent=2)
        print("\n请确保config.json中的配置正确之后再重新运行")
        time.sleep(5)
        sys.exit()
    try:
        if not os.path.exists(promptFile_story):
            # Write the default content to the file with UTF-8 encoding
            with open(promptFile_story, 'w', encoding='utf-8') as file:
                file.write(defaultStoryPrompt)
                print(f"\n没有找到分镜prompt文件, 已自动创建默认prompt文件: {promptFile_story}")
                storyPrompt = defaultStoryPrompt
        # Read the file and extract content as a single string with UTF-8 encoding
        with open(promptFile_story, 'r', encoding='utf-8') as file:
            storyPrompt = file.read()
            if storyPrompt == "":
                storyPrompt = defaultStoryPrompt
                print(f"\n你没有写分镜prompt, 将使用默认prompt:\n{storyPrompt}")
            else:
                print(f"\n**读取到自定义分镜prompt:\n{storyPrompt}")
    except Exception as e:
        print(f"\n处理分镜prompt文件时遇到错误: {e}")
    try:
        if not os.path.exists(promptFile_image):
            # Write the default content to the file with UTF-8 encoding
            with open(promptFile_image, 'w', encoding='utf-8') as file:
                file.write(defaultImagePrompt)
                print(f"\n没有找到图片prompt文件, 已自动创建默认prompt文件: {promptFile_image}")
                imgClient.systemPrompt = defaultStoryPrompt
        # Read the file and extract content as a single string with UTF-8 encoding
        with open(promptFile_image, 'r', encoding='utf-8') as file:
            imgClient.systemPrompt = file.read()
            if imgClient.systemPrompt == "":
                imgClient.systemPrompt = defaultImagePrompt
                print(f"\n你没有写图片prompt, 图片生成时不会使用system prompt")
            else:
                print(f"\n**读取到自定义图片prompt:\n{imgClient.systemPrompt}")
    except Exception as e:
        print(f"\n处理图片prompt文件时遇到错误: {e}")


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

def generateStoryBoard(content, max_tokens=4000, outputPath = None):
    try:
        model = configData["LLM_model"]
        print(f"当前使用模型: {model}")
        completion = client.chat.completions.create(
            model=model,
            max_tokens=configData["LLM_maxToken"],
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": storyPrompt,
                },
                {
                    "role": "user",
                    "content": f"{content}"
                }
            ]
        )
        result = completion.choices[0].message.content
        print(result)
        try:
            result_ls = json.loads(result)
            result_ls = result_ls["result"]
            if outputPath != None:
                #如果是一个folder, 让AI创建一个文件名
                if os.path.exists(outputPath) and os.path.isdir(outputPath):
                    print("正在为生成的稿子命名...")
                    story = ""
                    for sence in result_ls:
                        voiceLine = sence["voiceover"]
                        story += voiceLine
                    name = sendPrompt(f"{story}\n为这个视频稿取一个15字以内, 不含特殊符号的名字")
                    os.makedirs(os.path.join(outputPath, name), exist_ok=True)
                    outputPath = os.path.join(outputPath, name, f"{name}.json")
                with open(outputPath, 'w', encoding='utf-8') as file:
                    json.dump(result_ls, file, ensure_ascii=False, indent=2)
                    print(f"分镜保存到了: {outputPath}")
        except Exception as e:
                print(f"!_错误: {e}!_")
                return None, None
        return result_ls, outputPath
    except Exception as e:
        print(f"!_错误: {e}!_")
        return None, None
    
def sendPrompt(userPrompt, systemPrompt= "", max_tokens=3000):
    formatInstruction = """\nProvide a straight response without reiterating the input, Your response must be enclosed as a child in the following json structure(even if your answer is already an json object)\n
    {"response":"your response"}
    """ 
    systemPrompt += formatInstruction
    try:
        model = configData["LLM_model"]
        completion = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": systemPrompt,
                },
                {
                    "role": "user",
                    "content": f"{userPrompt}"
                }
            ]
        )
        result = completion.choices[0].message.content
        print(result)
        result = json.loads(result)["response"]
        print(result)
        return result
    except Exception as e:
        print(f"!_错误: {e}!_")
    


def readStoryBoard(folderPath):
    if os.path.exists(folderPath):
        if os.path.isdir(folderPath):
            projectName = os.path.basename(folderPath)
            folderPath = os.path.join(folderPath, f"{projectName}.json")
    if not os.path.exists(folderPath) or not folderPath.endswith(".json"):
        print("! 分镜文件不存在或不是json文件")
        return
    
    with open(folderPath, 'r', encoding='utf-8') as file:
        result = json.load(file)
        try:
            result[0]["index"]
            result[0]["voiceover"]
            result[0]["image"]
        except Exception as e:
            print(f"! 分镜文件内容无效:{e}\n{result}")
            return None
        return result


def generateVoiceOver(content, folderPath, index=None):
    for sence in content:
        if isinstance(voiceLine, dict):
            if index != None and sence['index'] != index:
                continue
            fileName = os.path.join(folderPath, f"{sence['index']}.wav")
            voiceLine = sence["voiceover"]
            voiceClient.generateVoice(voiceLine, fileName)
            print(f"生成语音: {voiceLine}")

def generateImages(content, folderPath, index=None):
    for sence in content:
        if isinstance(sence, dict):
            if index != None and sence['index'] != index:
                continue
            imagePrompt = sence["image"]
            fileName = os.path.join(folderPath, f"{sence['index']}.png")
            print(f"生成图片: {imagePrompt} ")
            imgClient.generateImage(imagePrompt, fileName)

def copy_file_with_timestamp(file, cacheFile):
    timestamp = datetime.now().strftime("%m%d%H%M%S")
    base, ext = os.path.splitext(cacheFile)
    new_file_name = f"{base}_{timestamp}{ext}"
    shutil.copy(file, new_file_name)

def rework(files, cacheOriginal = True):
    if isinstance(files, str):
        files = [files]
    storyFile = ""
    storyBoard = []
    for file in files:
        json_files = [f for f in os.listdir(os.path.dirname(file)) if f.endswith('.json')]
        for json in json_files:
            try:
                storyBoard = readStoryBoard(file)
                storyFile = file
                break
            except Exception as e:
                print(f"! 发现一个无效的分镜文件: {json}")
        if storyBoard != "":
            break

    for file in files:
        index = os.path.basename(file)
        index, ext = int(os.path.splitext(index))
        if cacheOriginal:
            folder = os.path.dirname(file)
            cacheFolder = os.makedirs(os.path.join(folder, "oldAssets"), exist_ok=True)
            cacheFile = os.path.join(cacheFolder, os.path.basename(file))
            copy_file_with_timestamp(file, cacheFile)
        if file.lower().endswith(".wav"):
            generateVoiceOver(storyBoard, os.path.dirname(file), index = index)
        elif file.lower().endswith(".png"):
            generateImages(storyBoard, os.path.dirname(file), index = index)
        elif file == storyFile:
            pass
    


init()
# videoLink = "https://www.youtube.com/watch?v=oK3JOfPFuGw"
# content = getContentFromLink(videoLink)
# print(f"{content}\n以上为提取到的内容")


# print("\n\n开始生成分镜")
# print("------------------------------")
# storyBoard, storyPath = generateStoryBoard(content, outputPath=outputPath_storyBoard)
# folderPath = os.path.dirname(storyPath)
# print("------------------------------")
# print("分镜生成完毕")



# print("\n\n开始生成语音")
# print("------------------------------")
# generateVoiceOver(storyBoard, folderPath)
# print("------------------------------")
# print("语音生成完毕")



# print("\n\n开始生成图片")
# print("------------------------------")
# generateImages(storyBoard, folderPath)
# print("------------------------------")
# print("图片生成完毕")

# # storyFile = input("input: ")
# # folderPath = storyFile
# # storyBoard = readStoryBoard(storyFile)


# print("\n\n开始合成视频")
# print("------------------------------")
# images, voices = videoEditor.findSources(folderPath)
# videoEditor.makeVideo(images, voices, folderPath)
# print("------------------------------")
# print("视频合成完毕")




if __name__ == "__main__":
    init()
    arg = None
    filePath = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if len(sys.argv) > 2:
            filePath = sys.argv[2]
    if arg == None:
        arg = input("argument: ")

    if arg == "rework":
        while filePath == None or not os.path.exists(filePath):
            filePath = input("拖入需要重新生成的文件(分镜稿, 图片或音频):\n")

