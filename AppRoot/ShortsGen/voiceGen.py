from gradio_client import Client, handle_file
import os
import sys
import shutil




currentDir = ""
currentPath = ""
if getattr(sys, 'frozen', False):
    currentDir = os.path.dirname(sys.executable)
    currentPath = os.path.abspath(sys.executable)
else:
    currentDir = os.path.dirname(os.path.abspath(__file__))
    currentPath = os.path.abspath(__file__)



client = Client("http://localhost:9872/")



def generateVoice(prompt, outputPath):
    result = client.predict(
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