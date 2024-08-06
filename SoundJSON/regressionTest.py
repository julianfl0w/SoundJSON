import sound_json
import json
import os
import numpy as np
testdirs = ["sf2_test", "sfz_test"]
result = {}
for testdir in testdirs:
    converted = sound_json.convertFile(testdir, compress = False)
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

audioData, sampleRate = sound_json.b642buffer(result["sfz_test/Harp.sfz"]["regions"][0]["audioData"])

