from gradio_client import Client, handle_file
import os
import sys
import shutil
import openai
import requests
import re


currentDir = ""
currentPath = ""
if getattr(sys, 'frozen', False):
    currentDir = os.path.dirname(sys.executable)
    currentPath = os.path.abspath(sys.executable)
else:
    currentDir = os.path.dirname(os.path.abspath(__file__))
    currentPath = os.path.abspath(__file__)



client_local = None


# 本地生成函数, 需要打开并设置好本地服务器再使用
def generateVoice_local(prompt, outputPath):
    global client_local
    if client_local == None:
        client_local = Client("http://localhost:9872/") #端口号记得填正确
    result = client_local.predict(
            ref_wav_path=handle_file(os.path.join(currentDir, "audio.wav")),
            prompt_text="",
            prompt_language="中文",
            text=prompt,
            text_language="中文",
            how_to_cut="凑四句一切",
            top_k=15,
            top_p=1,
            temperature=1,
            ref_free=False,
            speed=1,
            if_freeze=False,
            inp_refs=None,
            sample_steps="8",
            if_sr=False,
            pause_second=0.3,
            api_name="/get_tts_wav"
    )
    shutil.copy(result, outputPath)
    os.remove(result)

import subprocess

def macLocalTTS(text, outputPath):
    try:
        # Use the 'say' command to generate speech and save it as a WAV file
        subprocess.run(['say', '-v', 'Tingting', "-r", "200", '-o', outputPath.replace(".wav", ".aiff"), text], check=True)
        print(f"WAV audio file successfully created: {outputPath}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while generating the WAV file: {e}")



class VoiceGen:
    model = "Hailuo-Speech-02"
    runLocal = False
    voiceParams = ""
    def __init__(self, url, key, runLocal = False):
        if runLocal:
            self.runLocal = runLocal
        else:  
            self.client = openai.OpenAI(api_key=key, base_url=url)
        
    def generateVoice(self, prompt, outputPath):
        result = None
        if not self.runLocal:
            try:
                result = self.client.chat.completions.create(
                    model="Hailuo-Speech-02",
                    messages=[{"role": "user", "content": prompt+self.voiceParams}]
                )
                urls = re.findall(r'https?://[^\s\)]+', result.choices[0].message.content)
                url = urls[-1]
                response = requests.get(url)
                if response.status_code == 200:
                    with open(outputPath, "wb") as f:
                        f.write(response.content)
                    print(f"Voice saved as: {outputPath}")
                else:
                    print("Failed to download Voice:", response.status_code)
            except Exception as e:
                print(f"错误: {e}")
                print(f"语音生成失败: {prompt}\n返回结果: {result}")
        else:
            print("本地模型生成.....")
            try:
                # generateVoice_local(prompt, outputPath)
                macLocalTTS(prompt, outputPath)
            except Exception as e:
                print(f"错误: {e}")
                print(f"语音生成失败: {prompt}\n返回结果{result}")   
