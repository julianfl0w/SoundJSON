import json
with open("Harp.json", 'r') as f:
    d = json.loads(f.read())
for k, v in d.items():
    for sample in v["samples"]:
        sample["audioData"] = sample["audioData"][:128]
    v["key2samples"] = v["key2samples"][20:25]
    v["samples"] = v["samples"][:4]
with open("Harp.json.dummy", 'w+') as f:
    f.write(json.dumps(d, indent=2))