from os import listdir
from io import BufferedReader
from googletrans import Translator
import json

"""Important xxxx opcodes
0x003C = dialog text
0x003E = speaker name
0x0039 = choice
0x0046 = chapter name"""


CODEDICT={b"\x00\x3c":"Dialog",b"\x00\x3e":"Speaker",b"\x00\x39":"Choice",b"\x00\x46":"Chapter name",b"\x01\x04":"INVALID",}
def int2bytes(num,size = 2):
    result = bytearray(size)
    if size >2:
        lastbytes = num // 0x7fff
        result[2] = lastbytes % 256
        result[3] = lastbytes // 256
    num = num % 0x7fff
    result[0] = num % 256
    result[1] = num // 256
    return result

def copyfile(f1, f2):
    fp1 = open(f1, "rb")
    fp2 = open(f2, "wb")
    fp2.write(fp1.read())


def findPointers(filename):
    pointers = []
    fbin = open(filename+".bin","rb")
    fbin.read(4) #TODO check if 00000000
    textaddrbin = fbin.read(4)
    sizebin= fbin.read(4) #might be 4 bytes
    fbin.read(8)
    codeaddrbin = fbin.read(4)
    textaddr = int.from_bytes(textaddrbin,"little")
    codeaddr = int.from_bytes(codeaddrbin,"little")
    size = int.from_bytes(sizebin,"little")
    #print("Start Text address is \\x{:x}, Start Code address is \\x{:x} and Size is {}".format(textaddr,codeaddr,size))

    while fbin.tell() < codeaddr:
        fbin.read(2)
    while fbin.tell() < textaddr:  #fbin.tell() returns cursor position. pretty neat, iterate pointer table region until you reach actual memory
        buffer = (fbin.read(1),fbin.read(1))
        peekresult = fbin.read(8) # read 8 bytes ahead without moving the cursor
        fbin.seek(-8, 1)
        #cursor = fbin.tell()            
        if (peekresult[0:1] == b'\x03' and peekresult[1:2] == b'\x01'):
            scripttype = buffer[1] + buffer[0] 
            bytescount = peekresult[3] * 256 + peekresult[2] #indexing a byte directly converts it into an int. need to slice it like this.
            offset = (peekresult[7] *256 + peekresult[6]) * 0x7fff + peekresult[5] * 256 + peekresult[4]
            #print("FOUND A POINTER in position {:X}! Type = {}  Size = {}  Offset = {}".format(fbin.tell(),scripttype.hex(),bytescount.hex(),offset.hex()))
            pointer = {
                "Type":"",
                "Size":bytescount,
                "Offset":offset,
                "Text Position": offset + textaddr,
                "Pointer Position": fbin.tell()
            }            
            try:
                pointer["Type"] = CODEDICT[scripttype]
            except KeyError:
                pointer["Type"] = int.from_bytes(scripttype,"little")
            #continue
            pointers.append(pointer)
    fbin.close()
    fjson = open(filename+".json","w",encoding="shiftjis")
    payload = {
        "Code Address":codeaddr,
        "Text Address":textaddr,
        "Original Text Block Size":size,
        "pointers":pointers
    }
    json.dump(payload,fjson,ensure_ascii=False,indent=4)
    fjson.close()

def readPointers(filename,translate=False):
    with open(filename+".json","r", encoding="shiftjis") as f:
        contents = json.load(f)
    fbin = open(filename+".bin","rb")
    if translate:
        translator = Translator()
        print("Translating {}".format(filename))
        currentpointer = 0
        totalpointers = len(contents["pointers"]) #used for loading screen
    for pointer in contents["pointers"]: 
        #if (pointer["Type"] not in CODEDICT.values()):
            #continue
        fbin.seek(pointer["Text Position"])
        pointercontents = fbin.read(pointer["Size"])
        decodedtext = pointercontents.decode("shiftjis")
        if translate:
            print("Translating {} of {}. {:.2}%".format(currentpointer,totalpointers,currentpointer/totalpointers*100))
            pointer["Translated Text"]=translator.translate(decodedtext,src="ja",dest="en").text
            currentpointer = currentpointer + 1
        pointer["Original Text"] = decodedtext
        pointer["New Text"] = ""   
    fjson = open(filename+".json","w",encoding="shiftjis")
    json.dump(contents,fjson,ensure_ascii=False,indent=4)
    fjson.close()
    fbin.close()

def extractAllFiles():
    files = listdir()
    foundfiles = []
    for f in files:
        if (f[-4:] == ".bin"):
            foundfiles.append(f[:-4])
    for idx, f in enumerate(foundfiles):
        findPointers(f) #pointer info and start of text address
        validatejson(f)
        readPointers(f, False)
        print("File {} of {} extracted".format(idx+1, len(foundfiles))) 
    print("Extraction Complete")

def alterText(filename):
    with open(filename + ".json","r", encoding="shiftjis") as f:
        contents = json.load(f)
    binfilename = filename+ ".bin"
    copyfile(binfilename, binfilename+"~")
    total_offset = 0
    previous_size = 0
    fbintil = open(filename + ".bin" + "~","rb+")
    fbintil.seek(contents["Text Address"])
    for pointer in contents["pointers"]:
        newtext = pointer["New Text"]
        if newtext == "":
            newtext = pointer["Original Text"]
        newtextbin = bytearray(newtext, "shiftjis")
        newsize = len(newtextbin)
        fbintil.write(newtextbin)
        pointer["Size"] =  newsize
        pointer["Offset"] = total_offset + previous_size
        pointer["Text Position"] = contents["Text Address"] + total_offset + previous_size
        total_offset += previous_size
        previous_size = newsize
    contents["New Text Block Size"] = total_offset + newsize
    fbintil.close()
    with open(binfilename + "~", 'rb+') as fbintil:
        fbintil.seek(8)
        fbintil.write(int2bytes(contents["New Text Block Size"]))
    with open(filename + ".json", "w",encoding="shiftjis") as f:
        json.dump(contents, f, ensure_ascii=False, indent = 4)
    return

def updatePointers(filename):
    with open(filename+".json", "r",encoding="shiftjis") as json_file:
        contents = json.load(json_file)
    fbintil = open(filename + ".bin" + "~","rb+")
    for pointer in contents["pointers"]:
        fbintil.seek(pointer["Pointer Position"])
        assert fbintil.read(2) == b'\x03\x01'
        fbintil.write(int2bytes(pointer["Size"]))
        fbintil.write(int2bytes(pointer["Offset"],4))
    return

def validatejson(filename):
    with open(filename+".json", "r",encoding="shiftjis") as json_file:
        contents = json.load(json_file)
    offset = 0
    filteredPointers = []
    for pointer in contents["pointers"]:
        try:
            assert offset == pointer["Offset"]
        except:
            print("Validation filtered a Pointer in position {}".format(pointer["Pointer Position"]))
            continue
        filteredPointers.append(pointer)
        offset = offset + pointer["Size"]
    contents["pointers"] = filteredPointers
    with open(filename+".json", "w",encoding="shiftjis") as f:
        json.dump(contents, f, ensure_ascii=False, indent = 4)
    print("Json Validated!")

def insertAllFiles():
    files = listdir()
    foundfiles = []
    for f in files:
        if (f[-4:] == ".bin"):
            foundfiles.append(f[:-4])
    for idx, f in enumerate(foundfiles):
        alterText(f)
        updatePointers(f) 
        print("File {} of {} patched".format(idx+1, len(foundfiles))) 
    print("Patching Complete")


def main():
    choice = ""
    while choice != "ea" and choice != "pa" and choice != "e" and choice != "p":
        choice = input("Extract all/Patch all/Extract one/Patch one (ea/pa/e/p)")
    if choice == "ea":
        extractAllFiles()
        return 1
    elif choice == "pa":
        insertAllFiles()
        return 1
    elif choice == "e":
        f = input("Filename:")
        findPointers(f)
        validatejson(f)
        readPointers(f, False)
        return 1
    elif choice == "p":
        f = input("Filename:")
        alterText(f)
        updatePointers(f) 
        return 1
    return 0

main()     
