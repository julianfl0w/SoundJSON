import json
import os
def toDict(directory):
    retdict = {}
    length = 0

    for file in os.listdir(directory):
        fullfilename = os.path.join(directory, file)
        print(fullfilename)
        if os.path.isdir(fullfilename):
            l, fileresult = toDict(fullfilename)
            length += l
            if not length:
                continue
            retdict[file] = fileresult
        else:
            length += 1
            retdict[file[:-4]] = "/" + fullfilename
    return length, retdict

length, dd = toDict("samples")
dirdict = json.dumps(dd, indent=2)
with open("sitemap.json", 'w+') as f:
    f.write(dirdict)