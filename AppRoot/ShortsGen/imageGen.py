import openai
import requests
import os
import sys
import re


currentDir = ""
currentPath = ""
if getattr(sys, 'frozen', False):
    currentDir = os.path.dirname(sys.executable)
    currentPath = os.path.abspath(sys.executable)
else:
    currentDir = os.path.dirname(os.path.abspath(__file__))
    currentPath = os.path.abspath(__file__)


class ImageGen:
    model = ""
    systemPrompt = ""
    runLocal = False
    def __init__(self, url, key, runLocal = False):
        if runLocal:
            self.runLocal = True
        else:  
            self.client = openai.OpenAI(api_key=key, base_url=url)
        
    def generateImage(self, prompt, outputPath):
        result = None
        if not self.runLocal:
            try:
                result = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "system", "content": self.systemPrompt},
                            {"role": "user", "content": prompt}]
                )
                urls = re.findall(r'https?://[^\s\)]+', result.choices[0].message.content)
                url = urls[-1]
                response = requests.get(url)
                if response.status_code == 200:
                    with open(outputPath, "wb") as f:
                        f.write(response.content)
                    print(f"Image saved as: {outputPath}")
                else:
                    print("Failed to download image:", response.status_code)
            except Exception as e:
                print(f"错误: {e}")
                print(f"图片生成失败: {prompt}\n返回结果: {result}")
        else:
            print("本地模型生成.....")
            try:
                import txt2img
                txt2img.generate_image(f"{self.systemPrompt}, {prompt}", outputPath)
                print(f"Image saved as: {outputPath}")
            except Exception as e:
                print(f"错误: {e}")
                print(f"图片生成失败: {prompt}\n返回结果{result}")   


