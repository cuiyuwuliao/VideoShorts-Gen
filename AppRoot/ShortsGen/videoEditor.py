from moviepy.video.VideoClip import ImageClip
from moviepy.video.compositing import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import os
import math
from PIL import Image
import numpy
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy import TextClip
import sys

currentDir = ""
fontFile = ""
if getattr(sys, 'frozen', False):
    currentDir = os.path.dirname(sys.executable)
else:
    currentDir = os.path.dirname(os.path.abspath(__file__))
fontFile = os.path.join(currentDir, "Chinese.otf")
if not os.path.exists(fontFile):
    fontFile = ""



def findSources(folderPath):
    if not os.path.isdir(folderPath):
        folderPath = os.path.dirname(folderPath)
    wav_files = []
    png_files = []
    png_lost = []
    # Traverse the directory to find .wav files
    for file in os.listdir(folderPath):
        if file.lower().endswith('.wav') or file.lower().endswith('.aiff') :
            wavFile = os.path.join(folderPath, file)
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

def makeVideo(images, audios, folderPath, transitionTime = 0.5, subtitile = True):
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
    return filename


# if render = False, return srt path, if True, return video path
def autoSubtitle(videoPath, dynamic = True, readSrt = True, render = True):
        import audioTranscribe
        if not isinstance(videoPath,str) and os.path.exists(videoPath):
            print("! 字幕添加失败: 无效视频或路径")
            return videoPath
        videoClip = VideoFileClip(videoPath)
        srtPath = os.path.splitext(videoPath)[0]+".srt"
        generator = lambda txt: TextClip(
            fontFile,
            txt,
            font_size = videoClip.w/15,
            color= 'yellow',
            stroke_color="black",
            stroke_width=5
        )
        subtitileTimestamps = []
        if readSrt:
            if not os.path.exists(srtPath):
                print("! 视频同目录下没有找到srt字幕文件, 正在通过whisper生成....")
                subtitileTimestamps = audioTranscribe.transcribe(videoPath)
                audioTranscribe.writeSrt(subtitileTimestamps, srtPath)
            else:
                subtitileTimestamps = audioTranscribe.readSrt(srtPath)
        else:
            subtitileTimestamps = audioTranscribe.transcribe(videoPath)
            audioTranscribe.writeSrt(subtitileTimestamps, srtPath)
        if not render:
            return srtPath
        
        if not dynamic:
                sub = SubtitlesClip(srtPath, make_textclip=generator, encoding='utf-8').with_position(("center", videoClip.h/3))
                videoClip = CompositeVideoClip.CompositeVideoClip([videoClip, sub])
        else:
            sameLineWords = []
            textClips = []
            for index, wordItem in enumerate(subtitileTimestamps):
                if index in sameLineWords:
                    continue
                wordLine = []
                lineIndex = index
                lastWordEndTime = 0
                lineLength = videoClip.w/10 #用于当前字的横轴起始点
                while lineIndex < len(subtitileTimestamps):
                    word = subtitileTimestamps[lineIndex]["word"]
                    start = subtitileTimestamps[lineIndex]["start"]
                    end = subtitileTimestamps[lineIndex]["end"]
                    wordClip = generator(word)
                    if (start - lastWordEndTime < 0.5 or lastWordEndTime == 0): #如果和上个字在0.5秒之内，加入同一行字幕
                        if (lineLength + wordClip.w) < (videoClip.w - videoClip.w/10) or len(wordLine) == 0: #如果同一行放不下了，就不加入(除非第一个字就放不下)
                            wordClip = wordClip.with_position((lineLength, videoClip.h * 0.75))
                            wordClip.start = start
                            sameLineWords.append(lineIndex)
                            lineLength += wordClip.w
                            lineIndex = lineIndex + 1
                            wordLine.append({"wordClip":wordClip,"start":start, "end":end})
                        else:
                            lastWordEndTime = end
                            break
                    else:
                        lastWordEndTime = end
                        break
                    lastWordEndTime = end
                lastWordEndTime = wordLine[-1]["end"]
                for item in wordLine:#每个字设置持续时间 = 所属行最后一个字念完的时间 - 该字的起始时间
                    duration = lastWordEndTime - item["start"]
                    textClips.append(item["wordClip"].with_duration(duration))
                wordLine = []
            videoClip = CompositeVideoClip.CompositeVideoClip([videoClip] + textClips)

        outputPath = f"{os.path.splitext(videoPath)[0]}_caption.mp4"
        videoClip.write_videofile(outputPath, fps=videoClip.fps, codec='libx264', audio_codec='aac')
        return outputPath




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


if __name__ =="__main__":
    path = input("file: ")
    # path = "/Users/yu/Desktop/ShortsGen/results/地球表面积比例趣味误解/地球表面积比例趣味误解.mp4"
    # images, audios = findSources(path)
    # makeVideo(images, audios, path)
    autoSubtitle(path, readSrt=False)