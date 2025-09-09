from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import os
import math
from PIL import Image
import numpy

def findSources(folderPath):
    if not os.path.isdir(folderPath):
        folderPath = os.path.dirname(folderPath)
    wav_files = []
    png_files = []
    png_lost = []
    # Traverse the directory to find .wav files
    for root, dirs, files in os.walk(folderPath):
        for file in files:
            if file.lower().endswith('.wav'):
                wavFile = os.path.join(root, file)
                wav_files.append(wavFile)
                pngFile = f"{os.path.splitext(wavFile)[0]}.png"
                png_files.append(pngFile)
                if not os.path.exists(pngFile):
                    png_lost.append(pngFile)
    
    # Sort the files based on their numeric suffix
    wav_files.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))
    png_files.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))
    
    # Check if the number of files matches
    if len(png_lost) != 0:
        if len(png_lost) == len(wav_files):
            print("! 警告: 至少需要一张图片才能正常生成视频, 图片需要命名为分镜号, 如: 1.png")
            return
        print("! 警告: 以下缺失的图片不会在视频中显示")
        #显示上一张能用的图片
        latestValidIamge = ""
        index = 0
        for file in png_files:
            if file in png_lost:
                print(f"无图片: {file}")
                png_files[index] = latestValidIamge
            else:
                latestValidIamge = file
            index += 1
    return png_files, wav_files

def makeVideo(images, audios, folderPath, transitionTime = 0):
    clips = []  # Store video clips
    for image_path, audio_path in zip(images, audios):
        audio = AudioFileClip(audio_path)
        senceDuration = audio.duration + transitionTime
        img_clip = ImageClip(image_path, duration=senceDuration)
        img_clip = zoom_in_effect(img_clip)
        img_clip.audio = audio
        clips.append(img_clip)

    # Concatenate all clips into one video
    final_clip = CompositeVideoClip.concatenate_videoclips(clips, method='compose')

    if os.path.isdir(folderPath):
        filename = os.path.join(folderPath, f"{os.path.basename(folderPath)}.mp4")
    else:
        filename = folderPath
    final_clip.write_videofile(filename, fps=10, codec='libx264', audio_codec='aac')


def zoom_in_effect(clip, zoom_ratio=0.04):
    def effect(get_frame, t):
        img = Image.fromarray(get_frame(t))
        base_size = img.size

        new_size = [
            math.ceil(img.size[0] * (1 + (zoom_ratio * t))),
            math.ceil(img.size[1] * (1 + (zoom_ratio * t)))
        ]

        # The new dimensions must be even.
        new_size[0] = new_size[0] + (new_size[0] % 2)
        new_size[1] = new_size[1] + (new_size[1] % 2)

        img = img.resize(new_size, Image.LANCZOS)

        x = math.ceil((new_size[0] - base_size[0]) / 2)
        y = math.ceil((new_size[1] - base_size[1]) / 2)

        img = img.crop([
            x, y, new_size[0] - x, new_size[1] - y
        ]).resize(base_size, Image.LANCZOS)

        result = numpy.array(img)
        img.close()

        return result

    return clip.transform(effect)