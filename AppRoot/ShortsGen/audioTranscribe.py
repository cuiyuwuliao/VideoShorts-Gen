
import whisper
import re
model = whisper.load_model("base")


def transcribe(inputPath, alignScript = ""):
    audio = whisper.load_audio(inputPath)
    audio = whisper.pad_or_trim(audio)
    result = model.transcribe(audio, word_timestamps = True)
    # print the recognized text
    return extract_word_timestamps(result, alignScript)

def is_chinese_char(char):
    # Check if the character falls within the Chinese Unicode range
    return '\u4e00' <= char <= '\u9fff'

def remove_symbols(input_string):
    # Use regex to remove all non-alphanumeric characters except Chinese characters
    cleaned_string = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', input_string)
    return cleaned_string

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
    if alignScript != "":
        alignScript = remove_symbols(alignScript)
        index = 0
        for wordItem in timestamps:
            word = remove_symbols(wordItem["word"])
            print(word)
            word_aligned = ""
            for char in word:
                word_aligned += alignScript[0]
                alignScript = alignScript[1:]
                

            timestamps[index]["word"] = word_aligned
            index += 1
    return timestamps



inputPath = input("file")
result = transcribe(inputPath, alignScript="大家好！我是你们的人工智能主子。今天给大家带来的故事是: 投资避险技巧解析")
print(result)
