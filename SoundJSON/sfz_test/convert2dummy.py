import json
with open("Harp.json", 'r') as f:
    d = json.loads(f.read())
for k, v in d.items():
    for region in v["regions"]:
        region["audioData"] = region["audioData"][:128]

with open("Harp.json.dummy", 'w+') as f:
    f.write(json.dumps(d, indent=2))