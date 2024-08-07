import sound_json
import json
import os
import numpy as np
testdirs = ["sf2_test", "sfz_test"]
testdirs = ["sf2_test"]
result = {}
for testdir in testdirs:
    converted = sound_json.convertFile(testdir, compress = True)
    result.update(converted)

for k, v in result.items():
    outFilename = os.path.join(*v["path"]) + ".json"
    directory = os.path.dirname(outFilename)
    os.makedirs(directory, exist_ok=True)
    with open(outFilename, 'w+') as f:
        f.write(json.dumps({k:v}, indent=2))

retdict = {}
for k, v in result.items():
    if "success" in v.keys():
        retdict[k] = v["success"]
print("result")
print(json.dumps(retdict, indent=2))

def testRegions():
    for instname, inst in result.items():
        regions = inst["key2samples"]

        regions = regions[60]

        for region in regions:
            print(region)
            samples = inst["samples"]
            thisSample = samples[region["sampleNo"]]
            print(thisSample["gain"])
            audioData, sampleRate = sound_json.b642buffer(thisSample["audioData"])
            print(np.std(audioData))
            print(np.max(audioData))
