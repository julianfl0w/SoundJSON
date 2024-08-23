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

def toFile(outFilename, outjson):
    #outFilename = os.path.join(*v["path"]) + ".json"
    directory = os.path.dirname(outFilename)

    fillIn(outjson)
    outjson = json.dumps(outjson, indent=2)
    os.makedirs(directory, exist_ok=True)
    with open(outFilename, 'w+') as f:
        f.write(outjson)
    print(f"wrote {outFilename}")

def convertFile(infilename, compress=True, force=False, stopOnFail=True):
    soundJSON = {}
    # if its a dir, look at all files
    if os.path.isdir(infilename):
        print("dir " + infilename)
        for f in os.listdir(infilename):
            fullfilename = os.path.join(infilename, f)
            try:
                convertFile(fullfilename, compress=compress)
            except:
                print("Not Successful")
    
    file_extensions = {
        "sf2": sf22soundJson,
        "sfz": sfz2soundJson,
        #"pkl": lambda f: pickle.load(open(f, "rb")),
        #"json": lambda f: json.loads(open(f, "r").read()),
    }

    ext = infilename.split('.')[-1]
    if ext not in file_extensions:
        return {}

    print("processing " + infilename)
    soundJSON = file_extensions[ext](infilename, compress=compress)
    return soundJSON

def find_nearest(theList, x):
    nearest = min(theList, key=lambda num: abs(num - x))
    return nearest

def midi_note_to_frequency_multiplier(src, dst):
    distance = dst - src
    multiplier = 2 ** (distance / 12)
    return multiplier

def fillIn(soundJSON, keyCount = 128):
    for inst, instrumentJSON in soundJSON.items():
        extantKeys = []
        key2samples = instrumentJSON["key2samples"]

        # get extant references
        for keycenter in range(128):
            if key2samples[keycenter]:
                extantKeys += [keycenter]
        
        if not len(extantKeys):
            print("No Keys!")
            return

        for keycenter in range(keyCount):
            if not key2samples[keycenter]:
                nearestKey = find_nearest(extantKeys, keycenter)
                for sampleReference in key2samples[nearestKey]:
                    newDict = json.loads(json.dumps(sampleReference)) # to create an independant dict object
                    newDict["keyTrigger"] = keycenter
                    newDict["pitchBend"] = midi_note_to_frequency_multiplier(dst=keycenter, src=nearestKey)
                    referencedSampleNo = newDict["sampleNo"]
                    newDict["targetKeyCenter"] = instrumentJSON["samples"][referencedSampleNo]["pitch_keycenter"]
                    key2samples[keycenter] += [newDict]

def sf22soundJson(inFilename, compress = True, keyCount = 128):

    with open(inFilename, "rb") as sf2_file:
        sf2 = Sf2File(sf2_file)
        newdir = inFilename[:-4]
        filename_noext = inFilename[:-4]
        os.makedirs(newdir, exist_ok=True)
    
        for sf2inst in sf2.instruments:
            outFilename = inFilename[:-4] + ".json"
            if os.path.exists(outFilename):
                continue

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
            soundJsonDict["key2samples"] = [[] for _ in range(keyCount)] 
            soundJsonDict["samples"] = []
            
            if hasattr(sf2inst, "bags"):
                for bag in sf2inst.bags:
                    if hasattr(bag, "sample") and bag.sample is not None:
                        sampleDict = processSf2Sample(sample = bag.sample, soundJsonDict = soundJsonDict, compress=compress)


            soundJsonDict["outFilename"] = outFilename
            primaryKey = inFilename + "_" + sf2inst.name
            soundJsonDict = {primaryKey: soundJsonDict}
            soundJSON = json.dumps(soundJsonDict, indent=2)

            # check if it matches the gold file
            goldfilename = outFilename + ".gold"
            if os.path.exists(goldfilename):
                with open(goldfilename, 'r') as f:
                    goldtext = f.read()
                if goldtext != soundJSON:
                    soundJsonDict[primaryKey]["success"] = False

            toFile(outFilename, soundJsonDict)

                        
def sfz2soundJson(filename, compress, keyCount = 128, replaceDict = {}):
    print("processing sfz")

    outFilename = filename[:-4] + ".json"
    if os.path.exists(outFilename):
        print("Reading " + outFilename)
        with open(outFilename, 'r') as f:
            return f.read()

    if not os.path.exists(filename):
        print(f"{filename} not found!")
        return 
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
            preProcessText += "\n" + json.dumps(sfz2soundJson(includeFilename, compress=compress, replaceDict=replaceDict.copy())) + "\n"
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
    soundJsonDict["key2samples"] = [[] for _ in range(keyCount)] 
    soundJsonDict["samples"] = []
    soundJsonDict["samplesLoadPoint"] = os.path.dirname(filename)

    for sectionName, sampleDict in sfzParser.sections:
        if sectionName == "region":
            for d in [soundJsonDict["globalDict"], soundJsonDict["masterDict"], soundJsonDict["groupDict"]]:
                for k, v in d.items():
                    sampleDict[k] = v

            sampleFilename = os.path.join(soundJsonDict["samplesLoadPoint"], sampleDict["sample"])
            sampleDict["sampleFilename"] = sampleFilename

            if not os.path.exists(sampleFilename):
                continue

            # librosa always reads to float32, [-1,1]
            y, samplerate = librosa.load(sampleFilename, sr=None)
            sampleDict["gain"] = 0.7/np.max(y)
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

            sampleDict.update(
                sampleNo=len(soundJsonDict["samples"]),
                lengthSamples=len(y),
                sampleRate=samplerate,
                audioFormat=audioFormat,
                audioData=audioData,
            )
            
            try:
                sampleDict["pitch_keycenter"] = int(sampleDict["pitch_keycenter"])
            except:
                sampleDict["pitch_keycenter"] = sfzparser.sfz_note_to_midi_key(sampleDict["pitch_keycenter"])
            referenceDict = {"sampleNo": len(soundJsonDict["samples"]), "pitchBend": 1, "keyTrigger": sampleDict["pitch_keycenter"]}
            soundJsonDict["key2samples"][sampleDict["pitch_keycenter"]] += [referenceDict]
            soundJsonDict["samples"] += [sampleDict]

        elif sectionName in ["global", "master", "group"]:
            soundJsonDict[f"{sectionName}Dict"] = sampleDict
        elif sectionName == "control":
            if "default_path" in sampleDict or "prefix_sfz_path" in sampleDict:
                soundJsonDict["samplesLoadPoint"] = os.path.join(
                    filenameBasedir, sampleDict.get("default_path", "").replace("\\", os.sep)
                )
        elif sectionName not in ["comment", "curve", ""]:
            raise Exception(f"Unknown sfz header '{sectionName}'")

    if not soundJsonDict["key2samples"]:
        raise Exception("Empty key2samples list")
    soundJsonDict = {filename: soundJsonDict}

    toFile(outFilename, soundJsonDict)

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
    y = np.frombuffer(audio_segment.raw_data, dtype=np.int16)

    return y, audio_segment.frame_rate

def buffer2wavb64(y, samplerate):
    # Check and normalize the input
    if not y.dtype == np.int16:
        raise Exception("dtype must be np.int16")

    # Apply fade-in
    z = y.copy()
    z[:32] = y[:32] * np.arange(32) / 32  

    # Create an AudioSegment with float32 data
    audio_segment = AudioSegment(
        z.tobytes(),
        frame_rate=samplerate,
        sample_width=2, 
        channels=1,
    )
    
    # Export the audio segment to a buffer and encode it in base64
    buffer = io.BytesIO()
    audio_segment.export(buffer, format="wav")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return encoded


def audioProcess(self, sampleData, sample_rate):
    sampleData[:32] *= np.arange(32) / 32
    return sampleData

def processSf2Sample(sample, soundJsonDict, compress):

    # sf2 samples are always 16bit
    y = np.frombuffer(sample.raw_sample_data, dtype=np.int16)
    
    if compress:
        audioData = buffer2mp3b64(y, sample.sample_rate)
        audioFormat = "mp3"
    else:
        audioData = buffer2wavb64(y, sample.sample_rate)
        audioFormat = "wav"
    # sometimes the key is given by the sample name
    pitch_keycenter = int(sample.original_pitch) if hasattr(sample, "original_pitch") else int(sample.name)
    sampleDict = dict(
        sampleNo=len(soundJsonDict["samples"]),
        channels = 1,
        sample_rate=sample.sample_rate,
        sample=sample.name,
        lengthSamples=len(y),
        audioFormat=audioFormat, 
        audioData=audioData,
        pitch_keycenter=pitch_keycenter,
        gain = (2**16)/np.max(y) 
    )

    if soundJsonDict["percussion"]:
        sampleDict["pitch_keycenter"] = soundJsonDict["percussiveSampleIndex"]
        soundJsonDict["percussiveSampleIndex"] += 1

    if hasattr(sample, "start_loop") and soundJsonDict["loop"]:
        sampleDict.update(
            loop_start=sample.start_loop if sample.start_loop < sample.start else sample.start_loop - sample.start,
            loop_end=sample.end_loop - sample.start if sample.start_loop >= sample.start else sample.end_loop,
            loop=1,
            loop_mode="loop_continuous",
        )

    sampleDict["samplesLoadPoint"] = ""
    soundJsonDict["key2samples"][sampleDict["pitch_keycenter"]] += [{"sampleNo": len(soundJsonDict["samples"]), "pitchBend": 1, "keyTrigger": sampleDict["pitch_keycenter"]}]
    soundJsonDict["samples"] += [sampleDict]

if __name__ == "__main__":
    directory = sys.argv[1]
    masterjson= convertFile(infilename=directory, force=True) # convert everything in this dir
