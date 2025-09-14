

import re
import sys
import os

from pypinyin import pinyin, Style

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

def extract_chinese(item):
    if isinstance(item, str):
        return ''.join([char for char in item if '\u4e00' <= char <= '\u9fff'])
    elif isinstance(item, list):
        return ''.join([char for sub_item in item for char in extract_chinese(sub_item)])
    return ''  

def extractPinyinList(source):
    chinese_str = extract_chinese(source)
    pinyin_list = [pinyin(char, style=Style.NORMAL, heteronym=True) for char in chinese_str]
    pinyin_list = [pronunciation for sublist in pinyin_list for pronunciation in sublist]
    return pinyin_list

def substring_distance(main_string, sub1, sub2, getString = False):
    index1 = main_string.find(sub1)
    index2 = main_string.find(sub2)
    # Check if both substrings are found
    if index1 == -1 or index2 == -1:
        print(f"!!!: {sub1} : {sub2}")
        raise ValueError("One or both substrings not found in the main string.")
    # Calculate the distance
    distance = abs(index1 - index2)
    # Ensure index1 is less than index2 for slicing
    start_index = min(index1, index2)
    end_index = max(index1, index2)
    # Extract the string in between
    string_in_between = main_string[start_index:end_index]
    # print("String in between:", string_in_between)
    if getString:
        return string_in_between
    return len(string_in_between)

def replace_last_occurrence(original_string, substring, replacement):
    # Find the last occurrence of the substring
    last_index = original_string.rfind(substring)
    # If the substring is found, replace it
    if last_index != -1:
        return (original_string[:last_index] + 
                replacement + 
                original_string[last_index + len(substring):])
    # If the substring isn't found, return the original string
    return original_string

def fixTranscription(srtContent, string):
    isFilePath = False
    filePath = ""
    if isinstance(srtContent, str) and os.path.exists(srtContent):
        isFilePath = True
        filePath = srtContent
        srtContent = readSrt(srtContent)
    srtContent_words = srtContent
    if isinstance(srtContent[0], dict):
        srtContent_words = [item['word'] for item in srtContent]

    exText_wrong = extract_chinese(srtContent_words)
    exText_right = extract_chinese(string)
    pinyinList_wrong = extractPinyinList(exText_wrong)
    pinyinList_right = extractPinyinList(exText_right)
    def isHteronym(l1, l2):
        for p in l1:
            p_withG = p
            p_noG = p
            if p.endswith("n"):
                p_withG = p + "g"
            elif p.endswith("g"):
                p_noG = p
            if p in l2 or p_withG in l2 or p_noG in l2:
                return True
        return False
    correction = ""
    skip = 0
    lastLargeChunk_w = ""
    lastLargeChunk_r = ""
    for pwIndex, pw in enumerate(pinyinList_wrong):
        if skip > 0:
            skip -= 1
            continue

        cache = ""
        cache_bestMatch = ""
        cache_r = ""
        cache_bestMatch_r = ""
        correctionIndex = None
        for prIndex, pr in enumerate(pinyinList_right):
            if isHteronym(pw,pr):
                i = 0
                while True:
                    _pw = pinyinList_wrong[pwIndex + i]
                    _pr = pinyinList_right[prIndex + i]
                    if isHteronym(_pw, _pr):
                        cache += exText_wrong[pwIndex + i]
                        cache_r += exText_right[prIndex + i]
                        i += 1
                        if not ((pwIndex + i) >= len(pinyinList_wrong) or (prIndex + i >= len(pinyinList_right))):
                            continue
                    if len(cache) >= len(cache_bestMatch):
                        correctionIndex = prIndex
                        cache_bestMatch = cache
                        cache_bestMatch_r = cache_r
                    cache = ""
                    cache_r = ""
                    break
        if len(cache_bestMatch) > 10:
            skip = len(cache_bestMatch) - 1
            correction += cache_bestMatch
            if lastLargeChunk_w != "":
                # 两个相同的大块之间的字数完全匹配，那就把这些字强制修正
                gap_w = substring_distance(exText_wrong,lastLargeChunk_w, cache_bestMatch, getString=True) 
                gap_r = substring_distance(exText_right,lastLargeChunk_r, cache_bestMatch_r, getString=True)
                if len(gap_w) == len(gap_r):
                    correction = replace_last_occurrence(correction, gap_w, gap_r)
            lastLargeChunk_w = cache_bestMatch
            lastLargeChunk_r = cache_bestMatch_r
        elif correctionIndex == None or len(cache_bestMatch) < 4:
            correction += exText_wrong[pwIndex]
        else:
            correction += exText_right[correctionIndex]

    for i, srtItem in enumerate(srtContent):
        word = srtItem["word"]
        originalWord = word
        for ii, char in enumerate(word):
            if '\u4e00' <= char <= '\u9fff':
                char_list = list(word)
                char_list[ii] = correction[0]
                word = ''.join(char_list)
                if originalWord != word:
                    print(f"{originalWord}->{word}")
                srtContent[i]["word"] = word
                correction = correction[1:]
    if isFilePath:
        writeSrt(srtContent, filePath)
        print("srt文件校对完成")
    return srtContent
    
    


    



if __name__ == "__main__":
    textList_wrong = ["你好阿""我得名明子%","叫","达愿！"]
    text_right = "你好啊!我的名字叫大源"
    file = "/Users/yu/Desktop/ShortsGen/results/重生掌权之林薇终极逆袭/重生掌权之林薇终极逆袭.srt"
    fixTranscription(textList_wrong,text_right)
    



