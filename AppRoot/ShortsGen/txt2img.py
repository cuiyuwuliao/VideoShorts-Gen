import requests
import base64
import os
import json
import shutil
# Replace with your API URL


# Function to generate an image using Draw Things API (img2img support)
def generate_image(prompt, outputPath, base64_image=None, comfyUIConfig = None):
    API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"

    print(f"Generating image Locally...")

    params = {
        "prompt": prompt,
        "negative_prompt": "(bokeh, worst quality, low quality, normal quality, (variations):1.4), blur:1.5",
        "seed": 4068211935,
        "steps": 4,
        "guidance_scale": 10,
        "batch_count": 1
    }

    # If base64_image is provided, use img2img mode
    if base64_image:
        params["init_images"] = [base64_image]
        params["denoising_strength"] = 0.75  # Adjust for img2img effect strength

    headers = {"Content-Type": "application/json"}

    if comfyUIConfig == None:
        response = requests.post(API_URL, json=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            images = data.get("images", [])
            if images:
                with open(outputPath, "wb") as img_file:
                    img_file.write(base64.b64decode(images[0]))
                return outputPath
        else:
            print(f"Draw things 图片生成失败: {response.status_code}, {response.text}")
        return None
    else:
        result = generate_image_comfyUI(prompt, outputPath, comfyUIConfig)
        if result != None:
            return result
    return None

# Function to read an image and convert to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    
# 首先需要把comfyUI->设置->服务器配置里: 输出路径改为"C:\\comfyTemp", 端口号改为7860
def generate_image_comfyUI(prompt, outputPath, comfyUIConfig = None):
    API_URL = "http://127.0.0.1:7860/prompt"
    comfyTempDir = ""
    if os.name == "nt":
        comfyTempDir = "C:\\comfyTemp"
    else:
        comfyTempDir = os.path.join(os.path.expanduser("~"), "Downloads/comfyTemp")
    os.makedirs(comfyTempDir, exist_ok=True)
    comfyUIConfig["6"]["inputs"]["text"] = prompt
    response = requests.post(API_URL, json={"prompt" : comfyUIConfig})
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
    
if __name__ == "__main__":
    print(os.listdir(os.path.join(os.path.expanduser("~"), "Downloads/comfyTemp")))
    




