import requests
import base64
import os

# Replace with your API URL
API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"
STEPS = 4

# Function to generate an image using Draw Things API (img2img support)
def generate_image(prompt, outputPath, base64_image=None):
    print(f"Generating image with {STEPS} steps...")

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

    print(f"Error generating image: {response.status_code}, {response.text}")
    return None

# Function to read an image and convert to base64
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
    

