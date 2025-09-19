一键通过YouTube视频链接或txt文本来生成视频
支持Windows和mac运行


使用说明
1. 第一次运行时, 运行setup.bat
2. 运行AppRoot\ShortsGen.exe
3. 第一次运行时, 先点击一下Home页面的任意功能按钮, 会自动生成样本配置(config.json)，之后可以在"ShortsGen.exe->setting->API和模型相关设置"中进行配置
4. 在"ShortsGen.exe->setting->API和模型相关设置" 中配置模型，根据样本的数据形和下面的"配置解释"来进行配置
5. 点击"ShortsGen.exe->Home->"从稿子生成视频"即可一键生成视频(支持通过txt文件, Youtube链接, 或已生成好的分镜稿, 也可以直接输入"-t 要生成的内容"，如:"-t 用八岁小孩能理解的方式解释傅里叶变换的原理和运用")



###如不需要GUI,或者在mac上运行, 可以直接运行shortsGen.py


###若要使用comfyUI进行本地生图, 需要在confyUI服务器设置里将端口号设置为7860, 导出路径设置为："C:\comfyTemp"(Windows) 或 "Users/你的用户名/Downloads/comfyTemp" (Mac)

###Mac系统会优先通过Draw things本地生图, 需要开启服务器并将端口号设置为7860, 生成模型参数会沿用Draw things应用中的设置, 配置中填的参数会被忽略


配置解释：

"LLM_key": "语言模型服务的API key"

"LLM_model": "用来生成视频分镜的语言模型"

"LLM_url": "语言模型服务的地址"

"LLM_maxToken": 限制token数量

“LLM_storyboardPromptFile”: 指定其他分镜prompt文件(txt文件), 留空会使用默认prompt

"Img_Key": "图像模型服务的API key"

"Img_url": "图像模型服务的地址"

"Img_model": "用来生成分镜图的图像模型"

"Img_stylePrompt": "用英文描述生成图像的风格, 也可以不描述, 如果要写很长, 可以把这里留空然后填写到AppRoot\ShortsGen\prompt_图片.txt"

"Img_local_model": "comfyUI中的图像模型文件名(model.safetensors), 必须先本地启动了ComfyUI才能正常使用, 且模型必须在ComfyUI的checkpoints根目录下"

"Img_local_lora_1": "comfyUI中的图像LoRA模型名称(model.safetensors), 必须先本地启动了ComfyUI才能正常使用, 且模型必须在ComfyUI的loras根目录下, 如果看不懂或不需要使用LoRA可以填null"

"Img_local_lora_2": "第二个lora的名称, 两个参数lora都分别允许填: null, 模型名称string, 或者含强度的模型名称-{"name": "模型名称string", "model_strengh": 0.9},

"Img_local_steps": comfyUI模型的采样次数, 一般设置为20，采样次数越多通常效果越好, 但生成速度会变慢

"Img_local_width": comfyUI输出图片的宽度

"Img_local_height": comfyUI输出图片的高度

"Img_local_random": 为true时, 每次使用相同prompt会生成出不同的图片, 为false时相同的prompt会生成相同的图片

"Img_runLocal": 为true时使用comfyUI(必须先本地启动了ComfyUI才能正常使用),为false时使用上面填写的API服务

"Voice_Key": "tts语音模型服务的API key"

"Voice_url": "tts语言模型服务的地址"

"Voice_model": "要使用的tts语音模型"

"Voice_stylePrompt": "语音生成的自定义参数, 可以不填, 填写方式需要符合API服务的要求, 如果要写很长, 可以把这里留空然后填写到AppRoot\ShortsGen\prompt_语音.txt"

"Voice_intro": "视频的开场白, 可以写任意内容"

"Voice_runLocal": 为true时,使用系统默认的tts(很难听), 为false时使用上面填写的API服务

"custom_storyPath": 生成的视频和相关资产的导出路径, 必须为一个文件夹路径
