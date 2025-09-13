

import re
import sys
import os



def remove_symbols(input_string):
    # Use regex to remove all non-alphanumeric characters except Chinese characters
    cleaned_string = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff%]', '', input_string)
    return cleaned_string

def writeSrt(timestamps, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for i, item in enumerate(timestamps):
            start_time = format_time(item['start'])
            end_time = format_time(item['end'])
            f.write(f"{i + 1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{item['word']}\n\n")

def readSrt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # Regular expression to match SRT format
    srt_pattern = re.compile(
        r'(\d+)\n'                     # Subtitle number
        r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n'  # Timecodes
        r'([^\n]+(?:\n[^\n]+)*)\n?',   # Subtitle text
        re.MULTILINE
    )
    subtitles = []
    for match in srt_pattern.finditer(content):
        start_time = match.group(2)
        end_time = match.group(3)
        text = match.group(4).replace('\n', ' ').strip()
        # Convert start and end times to seconds
        start_seconds = convert_time_to_seconds(start_time)
        end_seconds = convert_time_to_seconds(end_time)
        # Create dictionary and append to list
        subtitles.append({
            "word": text,
            "start": start_seconds,
            "end": end_seconds
        })
    return subtitles

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02}:{minutes:02}:{int(seconds):02},{milliseconds:03}"

def convert_time_to_seconds(time_str):
    """Convert SRT time format to seconds."""
    hours, minutes, seconds = time_str.split(':')
    seconds, milliseconds = seconds.split(',')
    total_seconds = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
    return total_seconds





def transcribe(inputPath, alignScript = ""):
    import whisper
    print("提示: 第一次运行字幕生成会自动下载whisper的base模型, 必须翻墙才能正常下载")
    model = whisper.load_model("base")
    audio = whisper.load_audio(inputPath)
    # audio = whisper.pad_or_trim(audio)
    result = model.transcribe(audio, word_timestamps = True)
    # print the recognized text
    return extract_word_timestamps(result, alignScript)

def extract_word_timestamps(transcription_result, alignScript = ""):
    timestamps = []
    # Iterate through each segment in the transcription result
    for segment in transcription_result['segments']:
        for word_info in segment['words']:
            word_entry = {
                'word': word_info['word'],
                'start': word_info['start'],
                'end': word_info['end']
            }
            timestamps.append(word_entry)

    alignScript = remove_symbols(alignScript)
    index = 0
    for wordItem in timestamps:
        word = remove_symbols(wordItem["word"])
        
        word_aligned = word
        if alignScript != "":
            for char in word:
                word_aligned += alignScript[0]
                alignScript = alignScript[1:]
        timestamps[index]["word"] = word_aligned if word_aligned != "" else "_"
        index += 1
    timestamps = sorted(timestamps, key=lambda x: x['start'])
    return timestamps



if __name__ == "__main__":
    inputPath = input("file")
    result = transcribe(inputPath, alignScript="")
    writeSrt(result, os.path.splitext(inputPath)[0] + ".srt") 
    print(result)
