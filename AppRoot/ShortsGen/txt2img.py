import requests
import base64
import os
import json
import shutil
# Replace with your API URL


# Function to generate an image using Draw Things API (img2img support)
def generate_image(prompt, outputPath, base64_image=None):
    API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
    STEPS = 4
    print(f"Generating image Locally...")

    params = {
        "prompt": prompt,
        "negative_prompt": "(bokeh, worst quality, low quality, normal quality, (variations):1.4), blur:1.5",
        "seed": 4068211935,
        "steps": STEPS,
        "guidance_scale": 10,
        "batch_count": 1
    }

    # If base64_image is provided, use img2img mode
    if base64_image:
        params["init_images"] = [base64_image]
        params["denoising_strength"] = 0.75  # Adjust for img2img effect strength

    headers = {"Content-Type": "application/json"}
    response = requests.post(API_URL, json=params, headers=headers)

    if response.status_code == 200:
        data = response.json()
        images = data.get("images", [])
        if images:
            with open(outputPath, "wb") as img_file:
                img_file.write(base64.b64decode(images[0]))
            return outputPath
    else:
        result = generate_image_comfyUI(prompt, outputPath)
        if result != None:
            return result


    print(f"Draw things 图片生成失败: {response.status_code}, {response.text}")
    return None

# Function to read an image and convert to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
# 首先需要把comfyUI->设置->服务器配置里: 输出路径改为"C:\\comfyTemp", 端口号改为7860
def generate_image_comfyUI(prompt, outputPath):
    import sys
    currentDir = ""
    if getattr(sys, 'frozen', False):
        currentDir = os.path.dirname(sys.executable)
    else:
        currentDir = os.path.dirname(os.path.abspath(__file__))
    API_URL = "http://127.0.0.1:7860/prompt"
    jsonFile = os.path.join(currentDir, "prompt_ComfyUI.json")
    comfyTempDir = "C:\\comfyTemp"
    os.makedirs(comfyTempDir, exist_ok=True)
    with open(jsonFile, "r", encoding='utf-8') as file:
        data = json.load(file)
        data["6"]["inputs"]["text"] = prompt
        data["9"]["inputs"]["filename_prefix"] = "temp_ComfyImage"
        response = requests.post(API_URL, json={"prompt" : data})
        if response.status_code == 200:
            import time
            for _ in range (200):
                for filename in os.listdir(comfyTempDir):
                    if filename.startswith("temp_ComfyImage") and filename.endswith(".png"):
                        shutil.move(os.path.join(comfyTempDir, filename), outputPath)
                        return outputPath
                time.sleep(1)
            print(f"comfyUI超时未找到生成的图片: {outputPath}")
        else:
            print(f"comfyUI图片生成失败: {response.status_code}, {response.text}")
            return None




