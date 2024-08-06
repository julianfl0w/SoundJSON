import os
import sys
import pickle
import numpy as np
import soundfile as sf
import librosa
import io
from sfzparser import sfzparser
import base64
import json
from pydub import AudioSegment
from sf2utils.sf2parse import Sf2File
import filecmp
#from pedalboard import *


def spill(obj):
    print("spilling", obj)
    for attr in dir(obj):
        if not attr.startswith("__") and attr != "raw_sample_data":
            print(f"    {attr}: {getattr(obj, attr)}")

def convertFile(filename, compress=True, stopOnFail=True):
    soundJSON = {}
    # if its a dir, look at all files
    if os.path.isdir(filename):
        print("dir " + filename)
        for f in os.listdir(filename):
            fullfilename = os.path.join(filename, f)
            soundJSON.update(convertFile(fullfilename, compress=compress))
        return soundJSON
    
    file_extensions = {
        "sf2": sf22soundJson,
        "sfz": sfz2soundJson,
        #"pkl": lambda f: pickle.load(open(f, "rb")),
        #"json": lambda f: json.loads(open(f, "r").read()),
    }

    ext = filename.split('.')[-1]
    if ext not in file_extensions:
        return {}

    print("processing " + filename)
    return file_extensions[ext](filename, compress=compress)

def sf22soundJson(filename, compress = True):
    masterSoundJsonDict = {}
    with open(filename, "rb") as sf2_file:
        sf2 = Sf2File(sf2_file)
        newdir = filename[:-4]
        filename_noext = filename[:-4]
        os.makedirs(newdir, exist_ok=True)
    
        for sf2inst in sf2.instruments:

            if sf2inst.name == "EOI":
                continue
            print(sf2inst.name)
            soundJsonDict = {}

            soundJsonDict["source"] = "sf2"
            soundJsonDict["displayName"] = sf2inst.name
            soundJsonDict["name"] = sf2inst.name
            soundJsonDict["percussion"] = 0
            soundJsonDict["percussiveSampleIndex"] = 45
            soundJsonDict["loop"] = 0
            soundJsonDict["success"] = True
            soundJsonDict["path"] = list(os.path.split(filename_noext)) + [sf2inst.name]
            soundJsonDict["regions"] = []
            
            if hasattr(sf2inst, "bags"):
                for bag in sf2inst.bags:
                    if hasattr(bag, "sample") and bag.sample is not None:
                        processSf2Sample(sample = bag.sample, soundJsonDict = soundJsonDict, compress=compress)

            outFilename = os.path.join(newdir, sf2inst.name + ".json")
            soundJsonDict["outFilename"] = outFilename
            primaryKey = filename + "_" + sf2inst.name
            soundJsonDict = {primaryKey: soundJsonDict}
            soundJSON = json.dumps(soundJsonDict, indent=2)

            # check if it matches the gold file
            goldfilename = outFilename + ".gold"
            if os.path.exists(goldfilename):
                with open(goldfilename, 'r') as f:
                    goldtext = f.read()
                if goldtext != soundJSON:
                    soundJsonDict[primaryKey]["success"] = False

            masterSoundJsonDict.update(soundJsonDict)

    return masterSoundJsonDict

                        
def sfz2soundJson(filename, compress, replaceDict = {}):

    with open(filename, "r") as f:
        preprocFile = f.read()

    filenameBasedir = os.path.dirname(filename)
    filename_noext = filename[:-4]

    preProcessText = ""
    for ogline in preprocFile.split("\n"):
        ogline = ogline.strip()
        line = ogline.split("//")[0]
        for k, v in replaceDict.items():
            line = line.replace(k, v)
        preProcessText += ogline if ogline.startswith("//") else line
        if "#include" in line:
            includeFilename = os.path.join(
                filenameBasedir, eval(line.split("#include")[1].strip().split(" ")[0])
            )
            preProcessText += "\n" + sfz2soundJson(includeFilename, replaceDict=replaceDict.copy()) + "\n"
        elif line.startswith("#define"):
            k, v = line.split(" ")[1], "".join(line.split(" ")[2:])
            replaceDict[k] = v
        preProcessText += "\n"

    sfzParser = sfzparser.SFZParser(preProcessText)
    soundJsonDict = {}
    soundJsonDict["globalDict"] = {}
    soundJsonDict["masterDict"] = {}
    soundJsonDict["groupDict"] = {}
    soundJsonDict["displayName"] = os.path.split(filename)[-1][:-4]
    soundJsonDict["path"] = os.path.split(filename_noext)
    soundJsonDict["success"] = True
    soundJsonDict["regions"] = []

    for sectionName, regionDict in sfzParser.sections:
        if sectionName == "region":
            for d in [soundJsonDict["groupDict"], soundJsonDict["masterDict"], soundJsonDict["globalDict"]]:
                for k, v in d.items():
                    if k not in regionDict:
                        regionDict[k] = v

            sampleFilename = os.path.join(soundJsonDict["samplesLoadPoint"], regionDict["sample"])
            regionDict["sample"] = sampleFilename

            if not os.path.exists(sampleFilename):
                continue

            # librosa always reads to float32, [-1,1]
            y, samplerate = librosa.load(sampleFilename, sr=None)
            regionDict["gain"] = 0.7/np.max(y)
            if compress:
                audioData = buffer2mp3b64(y, samplerate)
                audioFormat = "mp3"
            else:
                # Open the file in binary mode
                audioFormat = sampleFilename.split(".")[-1]
                with open(sampleFilename, 'rb') as f:
                    # Read the file content
                    file_content = f.read()
                    # Convert the binary content to Base64
                    audioData = base64.b64encode(file_content).decode('utf-8')
                audioFormat = "wav"

            regionDict.update(
                lengthSamples=len(y),
                sampleRate=samplerate,
                audioFormat=audioFormat,
                audioData=audioData,
            )
            soundJsonDict["regions"] += [regionDict]

        elif sectionName in ["global", "master", "group"]:
            soundJsonDict[f"{sectionName}Dict"] = regionDict
        elif sectionName == "control":
            if "default_path" in regionDict or "prefix_sfz_path" in regionDict:
                soundJsonDict["samplesLoadPoint"] = os.path.join(
                    filenameBasedir, regionDict.get("default_path", "").replace("\\", os.sep)
                )
        elif sectionName not in ["comment", "curve", ""]:
            raise Exception(f"Unknown sfz header '{sectionName}'")

    if not soundJsonDict["regions"]:
        raise Exception("Empty regions list")
    outFilename = filename[:-4] + ".json"
    soundJsonDict = {filename: soundJsonDict}

    soundJSON = json.dumps(soundJsonDict, indent=2)

    # check if it matches the gold file
    goldfilename = outFilename + ".gold"
    if os.path.exists(goldfilename):
        with open(goldfilename, 'r') as f:
            goldtext = f.read()
        if goldtext != soundJSON:
            soundJsonDict[filename]["success"] = False

    return soundJsonDict


def buffer2mp3b64(y, samplerate):
    y = y / np.max(np.abs(y))
    y[:32] *= np.arange(32) / 32
    audio_segment = AudioSegment(
        (y * (2 ** 14)).astype(np.int16).tobytes(),
        frame_rate=samplerate,
        sample_width=2,
        channels=1,
    )
    buffer = io.BytesIO()
    audio_segment.export(buffer, format="mp3")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def b642buffer(encoded_str):
    # Decode the Base64 string
    decoded_bytes = base64.b64decode(encoded_str)
    
    with open("bs.wav", "wb+") as f:
        f.write(decoded_bytes)
        
    # Convert the bytes to an audio segment
    buffer = io.BytesIO(decoded_bytes)
    audio_segment = AudioSegment.from_file(buffer, format="wav")
    
    # Extract the raw data from the audio segment
    y = np.frombuffer(audio_segment.raw_data, dtype=np.float32)

    return y, audio_segment.frame_rate

def buffer2b64(y, samplerate):
    # normalize
    y = y / np.max(np.abs(y))

    if not y.dtype == np.float32:
        raise Exception("dtype must be np.float32")
    if any(np.abs(y) > 1):
        raise Exception("must be on range [-1,1]")

    y[:32] *= np.arange(32) / 32  # Apply fade-in

    # Create an AudioSegment with float32 data
    audio_segment = AudioSegment(
        y.tobytes(),
        frame_rate=samplerate,
        sample_width=4,  # 4 bytes for float32
        channels=1,
    )
    
    buffer = io.BytesIO()
    audio_segment.export(buffer, format="wav")  # Export as WAV
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded


def audioProcess(self, sampleData, sample_rate):
    sampleData[:32] *= np.arange(32) / 32
    return sampleData

def processSf2Sample(sample, soundJsonDict, compress):

    # sf2 samples are always 16bit
    y = np.frombuffer(sample.raw_sample_data, dtype=np.int16).astype(np.float32) / (2**15)
    if compress:
        audioData = buffer2mp3b64(y, sample.sample_rate)
        audioFormat = "mp3"
    else:
        audioData = buffer2b64(y, sample.sample_rate)
        audioFormat = "wav"

    regionDict = dict(
        sample_rate=sample.sample_rate,
        sample=sample.name,
        lengthSamples=len(y),
        audioFormat=audioFormat, 
        audioData=audioData,
        pitch_keycenter=int(sample.original_pitch) if hasattr(sample, "original_pitch") else int(sample.name),
        gain = 0.7/np.max(y) 
    )

    if soundJsonDict["percussion"]:
        regionDict["pitch_keycenter"] = soundJsonDict["percussiveSampleIndex"]
        soundJsonDict["percussiveSampleIndex"] += 1

    if hasattr(sample, "start_loop") and soundJsonDict["loop"]:
        regionDict.update(
            loop_start=sample.start_loop if sample.start_loop < sample.start else sample.start_loop - sample.start,
            loop_end=sample.end_loop - sample.start if sample.start_loop >= sample.start else sample.end_loop,
            loop=1,
            loop_mode="loop_continuous",
        )

    regionDict["samplesLoadPoint"] = ""
    soundJsonDict["regions"] += [regionDict]

if __name__ == "__main__":
    convertFile(filename=".", force=True) # convert everything in this dir