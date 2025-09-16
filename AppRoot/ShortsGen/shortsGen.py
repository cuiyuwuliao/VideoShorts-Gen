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
import random

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
    "LLM_key": "Your POE.com API KEY",
    "LLM_model": "GPT-5",
    "LLM_url": "https://api.poe.com/v1", 
    "LLM_maxToken": 5000,
    "Img_Key": "Your POE.com API KEY",
    "Img_url": "https://api.poe.com/v1",
    "Img_model": "Gemini-2.5-Flash-Image",
    "Img_stylePrompt": "In the style of simple pencil drawings",
    "Img_local_model":"sd_xl_base_1.0.safetensors",
    "Img_local_lora":None,
    "Img_local_steps":20,
    "Img_local_width": 576,
    "Img_local_height": 1024,
    "Img_local_random": True,
    "Img_runLocal": True,
    "Voice_Key": "Your POE.com API KEY",
    "Voice_url": "https://api.poe.com/v1",
    "Voice_model": "Hailuo-Speech-02",
    "Voice_stylePrompt": "--language Chinese --speed 1.2 --voice Lively_Girl",
    "Voice_intro": "",
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
3. `image`: 简短的分镜的图片描述(this needs to be written in English in the format of image generation prompts)

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

storyPrompt = None
configData = None
outputPath_storyBoard = currentDir

def update_json_file(file_path):
    from collections import OrderedDict
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            try:
                existing_data = json.load(file, object_pairs_hook=OrderedDict)
            except json.JSONDecodeError:
                print("Error reading JSON file. Please check the file format.")
                return
    else:
        print(f"File not found: {file_path}")
        return
    modified = False
    existing_keys = set(existing_data.keys())
    # Create an ordered dictionary for the new data
    updated_data = OrderedDict()
    for key, default_value in defaultConfigData.items():
        if key not in existing_keys:
            updated_data[key] = default_value
            modified = True
        else:
            updated_data[key] = existing_data[key]
    if modified:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(updated_data, file, indent=4, ensure_ascii=False)
        print("Json设置验证完毕, 存在新增字段")
    else:
        print("Json设置验证完毕, 无新增字段")

def init():
    global defaultConfigData, configData, client, imgClient, storyPrompt, voiceClient, outputPath_storyBoard
    configFile = os.path.join(currentDir, "config.json")
    promptFile_story = os.path.join(currentDir, "prompt_分镜.txt")
    promptFile_image = os.path.join(currentDir, "prompt_图片.txt")
    promptFile_voice = os.path.join(currentDir, "prompt_语音.txt")

    try:
        update_json_file(configFile)
        with open(configFile, 'r', encoding='utf-8') as file:
            configData = json.load(file)
            client = openai.OpenAI(api_key=configData["LLM_key"],base_url=configData["LLM_url"])

            voiceClient = VoiceGen(key=configData["Voice_Key"],url=configData["Voice_url"], runLocal=configData["Voice_runLocal"])
            voiceClient.model = configData["Voice_model"]

            imgClient = ImageGen(key=configData["Img_Key"],url=configData["Img_url"], runLocal=configData["Img_runLocal"])
            imgClient.model = configData["Img_model"]
            imgLocalConfigPath = os.path.join(currentDir, "prompt_ComfyUI.json")
            if configData["Img_local_lora"] != None:
                imgLocalConfigPath = os.path.join(currentDir, "prompt_ComfyUI_Lora.json")
            with open(imgLocalConfigPath, "r", encoding='utf-8') as file:
                data = json.load(file)
                data["9"]["inputs"]["filename_prefix"] = "temp_ComfyImage"
                data["4"]["inputs"]["ckpt_name"] = configData["Img_local_model"]
                data["3"]["inputs"]["steps"] = configData["Img_local_steps"]
                data["5"]["inputs"]["width"] = configData["Img_local_width"]
                data["5"]["inputs"]["height"] = configData["Img_local_height"]
                if configData["Img_local_random"]:
                    data["3"]["inputs"]["seed"] = random.randint(0, 2_147_483_647)
                if configData["Img_local_lora"] != None:
                    data["11"]["inputs"]["lora_name"] = configData["Img_local_lora"]
                imgClient.localConfig = data

            if configData["custom_storyPath"] != None:
                outputPath_storyBoard =configData["custom_storyPath"]
                print(f"**分镜会导出到:{outputPath_storyBoard}")
    except Exception as e:
        if os.path.exists(configFile):
            os.remove(configFile)
        print(f"\n! {e}\n! config.json is corrupted or does not exists, creating a defualt config.json....")
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
                file.write("")
                print(f"\n没有找到图片prompt文件, 已自动创建默认prompt文件: {promptFile_image}")
                imgClient.systemPrompt = defaultStoryPrompt
        # Read the file and extract content as a single string with UTF-8 encoding
        with open(promptFile_image, 'r', encoding='utf-8') as file:
            imgClient.systemPrompt = file.read()
            if isinstance(configData["Img_stylePrompt"], str): #如有, Config里的图片prompt会覆写txt prompt的内容
                if configData["Img_stylePrompt"] != "":
                    imgClient.systemPrompt = configData["Img_stylePrompt"]
            if imgClient.systemPrompt == "":
                print(f"\n你没有写图片prompt, 图片生成时不会使用system prompt")
            else:
                print(f"\n**读取到自定义图片prompt:\n{imgClient.systemPrompt}")
    except Exception as e:
        print(f"\n处理图片prompt文件时遇到错误: {e}")
    try:
        if not os.path.exists(promptFile_voice):
            with open(promptFile_voice, 'w', encoding='utf-8') as file:
                file.write("")
                voiceClient.voiceParams = ""
        with open(promptFile_voice, 'r', encoding='utf-8') as file:
            voiceClient.voiceParams = file.read()
            if isinstance(configData["Voice_stylePrompt"], str): #如有, Config里的语音prompt会覆写txt prompt的内容
                if configData["Voice_stylePrompt"] != "":
                    imgClient.systemPrompt = configData["Voice_stylePrompt"]
            if voiceClient.voiceParams == "":
                print(f"\n你没有写语音prompt风格参数, 将使用模型的默认风格")
            else:
                print(f"\n**读取到自定义语音prompt:\n{voiceClient.voiceParams}")
    except Exception as e:
        print(f"\n处理语音prompt文件时遇到错误: {e}")


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

def extract_json_content_regex(text):
    pattern = ""
    for t in text:
        if t in ["{", "["]:
            if t == "{":
                pattern = r'\{.*\}'
                break
            else:
                pattern = r'\[.*\]'
    match = re.search(pattern, text, re.DOTALL)
    return match.group(0) if match else text

def generateStoryBoard(content, outputPath = None):
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
        result = extract_json_content_regex(result)
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
                    name = sendPrompt(f"{story}\n为这个视频稿取一个15字以内, 不含特殊符号和空格的名字")
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
    
def sendPrompt(userPrompt, systemPrompt= "", modifyJson = False, additionalPrompt = ""):
    formatInstruction = """\nDo not reiterate the input, Your response must be enclosed as a child oject in the following json structure\n
    {"response":"your response"}
    """ 
    if modifyJson:
        formatInstruction = "\ncrucial: your job is to modify the input json data, and your response should be in the exact same format as the input"
    systemPrompt += formatInstruction
    try:
        model = configData["LLM_model"]
        print(f"systemPrompt: {systemPrompt}")
        print(f"userPrompt: {userPrompt}")
        print("####AI请求开始####")
        completion = client.chat.completions.create(
            model=model,
            max_tokens=configData["LLM_maxToken"],
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": systemPrompt,
                },
                {
                    "role": "user",
                    "content": f"{userPrompt}\n\n{additionalPrompt}"
                }
            ]
        )        
        result = completion.choices[0].message.content
        print("####AI请求结束####")
        print(f"结果:\n{result}")
        result = extract_json_content_regex(result)
        result = json.loads(result)
        if not modifyJson:
            result = result["response"]
        return result
    except Exception as e:
        print(f"!_错误: {e}!_")
    


def readStoryBoard(folderPath):
    if os.path.exists(folderPath):
        if os.path.isdir(folderPath):
            projectName = os.path.basename(folderPath)
            folderPath = os.path.join(folderPath, f"{projectName}.json")
    if not os.path.exists(folderPath) or not folderPath.lower().endswith('.json'):
        print(f"! 分镜文件不存在或不是json文件: {folderPath}")
        return
    with open(folderPath, 'r', encoding='utf-8') as file:
        result = json.load(file)
        if isValidStoryBoard(result):
            return result
        else:
            print(f"! 分镜文件内容无效:{e}\n{result}")
            return None
        

def isValidStoryBoard(storyBoardData):
    try:
        storyBoardData[0]["index"]
        storyBoardData[0]["voiceover"]
        storyBoardData[0]["image"]
    except Exception:
        return False
    return True




def generateVoiceOver(content, folderPath, index=None):
    for scene  in content:
        if isinstance(scene , dict):
            if index != None and scene ['index'] != index:
                continue
            fileName = os.path.join(folderPath, f"{scene ['index']}.wav")
            voiceLine = scene ["voiceover"]
            if scene ['index'] == 1:
                projectName = os.path.basename(folderPath)
                intro = configData.get("Voice_intro", None)
                if intro != None:
                    intro = intro.replace("$projectName", projectName)
                else:
                    intro = None
                
                voiceLine = f"{intro}。{voiceLine}"
            voiceClient.generateVoice(voiceLine, fileName)
            print(f"生成语音: {voiceLine}")

def generateImages(content, folderPath, index=None):
    for scene in content:
        if isinstance(scene , dict):
            if index != None and scene ['index'] != index:
                continue
            imagePrompt = scene ["image"]
            fileName = os.path.join(folderPath, f"{scene['index']}.png")
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
        for jsonfile in json_files:
            jsonfile = os.path.join(os.path.dirname(file), jsonfile)
            try:
                storyBoard = readStoryBoard(jsonfile)
                storyFile = jsonfile
                break
            except Exception as e:
                print(f"! 发现一个无效的分镜文件: {jsonfile}")
        if storyBoard != "":
            break
    story = '\n'.join(item['voiceover'] for item in storyBoard)
    for file in files:
        index = os.path.basename(file)
        index, ext = os.path.splitext(index)
        if cacheOriginal:
            folder = os.path.dirname(file)
            cacheFolder = os.path.join(folder, "oldAssets")
            os.makedirs(os.path.join(folder, "oldAssets"), exist_ok=True)
            cacheFile = os.path.join(cacheFolder, os.path.basename(file))
            copy_file_with_timestamp(file, cacheFile)
        if file.lower().endswith(".wav") or file.lower().endswith(".aiff") :
            generateVoiceOver(storyBoard, os.path.dirname(file), index = int(index))
        elif file.lower().endswith(".png"):
            generateImages(storyBoard, os.path.dirname(file), index = int(index))
        elif file.lower().endswith(".srt"):
            ## 通过AI修改，但是字幕太长时会不准, 所以弃用
            # from audioTranscribe import readSrt
            # from audioTranscribe import writeSrt
            # srtContent = readSrt(file)
            # wordContent = [item['word'] for item in srtContent]
            # userPrompt = json.dumps(wordContent, ensure_ascii=False)
            # userPrompt += f"\n参考下面原文替换上面list中错误汉字, 保持len(list)长度完全不变, 不要修改汉字以外的任何东西, 返回一个长度为{len(srtContent)}的list\n"
            # userPrompt += story
            # systemPrompt = "\n你需要返回一个json格式的list, 以及list的长度\n"
            # newWordContent = sendPrompt(userPrompt, systemPrompt, modifyJson=True)
            # if len(newWordContent) != len(wordContent):
            #     input(f"! AI修正srt字幕数量不匹配, 期望:{len(wordContent)}, 得到:{len(newWordContent)}\n按回车重新生成")
            # for i, wordItem in enumerate(srtContent):
            #     srtContent[i]["word"] = newWordContent[i]
            # writeSrt(srtContent, file)
            from audioTranscribe import fixTranscription
            srtContent = fixTranscription(file, story)
        elif file == storyFile:
            newStoryBoard = []
            additionalPrompt = input("请输入分镜的修改要求: ")
            while additionalPrompt != "":
                userPrompt = json.dumps(storyBoard, ensure_ascii=False)
                systemPrompt = "你是一个分镜助理, 你需要按照用户的要求修改用户提供的json分镜中的内容, 并返回一个相同格式的json分镜\n"
                print("正在生成新的分镜稿...")
                newStoryBoard = sendPrompt(userPrompt, systemPrompt, modifyJson=True, additionalPrompt=additionalPrompt)
                print(newStoryBoard)
                if isValidStoryBoard(newStoryBoard):
                    print("(^_^)格式通过验证, 请放心使用")
                else:
                    print("! 格式不正确, 建议重试")
                additionalPrompt = input("按回车采用分镜稿, 你也可以继续输入修改意见来重试: ")
            with open(file, 'w', encoding='utf-8') as file:
                json.dump(newStoryBoard, file, ensure_ascii=False, indent=2)
                print(f"新分镜保存到了: {file}")


def remove_quotes(s):
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s





if __name__ == "__main__":
    try:
        init()
        print()
        arg = None
        filePath = ""
        fileList = []
        extraImgBatch = ""
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if len(sys.argv) > 2:
                filePath = sys.argv[2]
        choices = {"Video_Compose":"0", "Video_Generate":"1", "Image":"2", "Voice":"3", "Rework":"4", "StoryBoard": "5", "caption": "6"}
        while arg not in choices.values():
            print("操作列表")
            for key, value in choices.items():
                print(f"{value}: {key}")
            arg = remove_quotes(input("请输入操作序号: "))

        if arg == "1":
            while filePath == "" :
                filePath = input("拖入分镜稿, txt文档或复制油管链接(需包含字幕), 生成图片, 语音和视频: \n")
                filePath = remove_quotes(filePath)
                if filePath.startswith("http") or filePath.startswith("-t ") or os.path.exists(filePath):
                    break
            
        if arg == "2":
            while filePath == "" or not os.path.exists(filePath):
                filePath = remove_quotes(input("拖入分镜稿, 仅生成图片: \n"))
            while True:
                extraImgBatch = input("要额外生成多少批？(输入整数, 不输入则不额外生成): ")
                if extraImgBatch.isdigit():
                    extraImgBatch = int(extraImgBatch)
                    if extraImgBatch > 0:
                        break
                if extraImgBatch == "" or extraImgBatch == None:
                    extraImgBatch = 0
                    break
                

        if arg == "3":
            while filePath == "" or not os.path.exists(filePath):
                filePath = remove_quotes(input("拖入分镜稿, 仅生成语音: \n"))

        if arg == "4":
            while len(fileList) == 0:
                filePath = input("拖入需要重新生成的文件(分镜稿, 图片, 语音, srt字幕): \n")
                fileList_unchecked = filePath.split(" ")
                hasStoryBoard = False
                for file in fileList_unchecked:
                    file = remove_quotes(file)
                    if file.endswith(".json"):
                        hasStoryBoard = True
                    if not os.path.exists(file):
                        print(f"文件不合规: {file}")
                        fileList = []
                        break
                    fileList.append(file)
                if len(fileList) > 1 and hasStoryBoard:
                    print("! 分镜稿仅支持单独处理, 你可以先修改分镜稿再通过分镜稿生成图片和音频\n")
                    fileList = []

        if arg == "0":
            while filePath == "" or not os.path.exists(filePath):
                filePath = remove_quotes(input("拖入分镜稿或项目文件夹(请先确保图片和语音已生成), 合成视频: \n"))

        if arg == "5":
            while filePath == "" :
                filePath = input("拖入txt文档或复制油管链接(需包含字幕), 生成分镜稿 \n")
                filePath = remove_quotes(filePath)
                if filePath.startswith("http") or filePath.startswith("-t ") or os.path.exists(filePath):
                    break
        if arg == "6":
            while filePath == "" or not os.path.exists(filePath):
                filePath = input("拖入要添加字幕的视频(优先使用同目录的同名srt文件,没有时自动生成)\n")
                filePath = remove_quotes(filePath)

        content = ""
        folderPath = ""
        videoPath = ""
        if arg in ["1", "2", "3", "5"]:
            if filePath.startswith("http"):
                videoLink = filePath
                content = getContentFromLink(videoLink)
                print(f"{content}\n以上为提取到的内容")
            elif filePath.endswith(".txt"): 
                with open(filePath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    print(f"{content}\n以上为读取到的内容")
            elif filePath.startswith("-t "):
                content = filePath[3:]
                print(f"{content}\n通过上面内容生成")
            if content != "":
                print("\n\n开始生成分镜")
                print("------------------------------")
                storyBoard, storyPath = generateStoryBoard(content, outputPath=outputPath_storyBoard)
                folderPath = os.path.dirname(storyPath)
                print("------------------------------")
                print("分镜生成完毕")

            else:#直接给的分镜文件，读分镜
                print("正在读取分镜文件...")
                storyBoard = readStoryBoard(filePath)
                folderPath = os.path.dirname(filePath)

        if arg in ["1", "2"]:
            print("\n\n开始生成图片")
            print("------------------------------")
            generateImages(storyBoard, folderPath)
            if isinstance(extraImgBatch, int) and extraImgBatch > 0:
                batchIndex = 1
                for _ in range(extraImgBatch):
                    print(f"正在生成额外的批次({batchIndex}/{extraImgBatch})")
                    batchFolder = os.path.join(folderPath, f"extra_{batchIndex}")
                    increment = 1
                    while os.path.exists(batchFolder):
                        batchFolder = os.path.join(folderPath, f"extra_{batchIndex + increment}")
                        increment += 1
                    os.mkdir(batchFolder)
                    generateImages(storyBoard, batchFolder)
                    batchIndex += 1
            print("------------------------------")
            print("图片生成完毕")

        if arg in ["1", "3"]:   
            print("\n\n开始生成语音")
            print("------------------------------")
            generateVoiceOver(storyBoard, folderPath)
            print("------------------------------")
            print("语音生成完毕")

        if arg in ["4"]:
            rework(fileList)

        if arg in ["0", "1"]:
            print("\n\n开始合成视频")
            print("------------------------------")
            if folderPath == "": 
                folderPath = filePath
            if not os.path.isdir(folderPath):
                folderPath = os.path.dirname(folderPath)
            images, voices = videoEditor.findSources(folderPath)
            videoPath = videoEditor.makeVideo(images, voices, folderPath)
            print("------------------------------")
            print("视频合成完毕")

        if arg in ["0", "1", "6"]:
            if arg != "6":
                print("提示: 视频生成完毕, 正在生成字幕版视频, 若不需要可以直接关闭")
            else:
                videoPath = filePath
            print("\n\n开始添加字幕")
            print("------------------------------")
            srtFile = videoEditor.autoSubtitle(videoPath, render=False)
            print(f"字幕生成到了: {srtFile}")
            print("正在尝试用原始文本校对字幕:")
            try:
                rework(srtFile)
            except Exception as e:
                print(f"错误:{e}\n\n字幕校对失败: 请检查分镜稿是否存在且合法")
            print("正在给视频添加字幕")
            videoEditor.autoSubtitle(videoPath, render=True, readSrt=True)
            print("------------------------------")
            print("字幕添加完毕")
        
        input("\n@(^_^)@运行结束, 可以关闭咯!")
    except Exception as e:
        print(f"!_错误: {e}!_")
        input("\n请按回车键退出")
