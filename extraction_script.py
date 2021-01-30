from os import listdir
from io import BufferedReader
from googletrans import Translator
from shutil import copyfile
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
def findPointers(filename):
    pointers = []
    fbin = BufferedReader(open(filename,"rb")) #BufferedReader allows peeking ahead without moving the cursor
    fbin.read(4) #TODO check if 00000000
    textaddrbin = fbin.read(4)
    sizebin= fbin.read(4) #might be 4 bytes
    fbin.read(8)
    codeaddrbin = fbin.read(4)
    textaddr = int.from_bytes(textaddrbin,"little")
    codeaddr = int.from_bytes(codeaddrbin,"little")
    size = int.from_bytes(sizebin,"little")
    print("Start Text address is \\x{:x}, Start Code address is \\x{:x} and Size is {}".format(textaddr,codeaddr,size))

    while fbin.tell() < codeaddr:
        fbin.read(2)
    while fbin.tell() < textaddr:  #fbin.tell() returns cursor position. pretty neat, iterate pointer table region until you reach actual memory
        buffer = (fbin.read(1),fbin.read(1))
        peekresult = fbin.peek(8) # read 8 bytes ahead without moving the cursor
        #cursor = fbin.tell()            
        if (peekresult[0:1] == b'\x03' and peekresult[1:2] == b'\x01'):
            scripttype = buffer[1] + buffer[0] 
            bytescount = peekresult[3] * 256 + peekresult[2] #indexing a byte directly converts it into an int. need to slice it like this.
            offset = (peekresult[7] *256 + peekresult[6]) * 0x7fff + peekresult[5] * 256 + peekresult[4]
            #print("FOUND A POINTER in position {:X}! Type = {}  Size = {}  Offset = {}".format(fbin.tell(),scripttype.hex(),bytescount.hex(),offset.hex()))
            pointers.append((fbin.tell(), scripttype, bytescount, offset))
    fbin.close()
    return (pointers,textaddr, codeaddr, size)

def genText(pointers, filename, textaddr, codeaddr, size, translate=False):
    #ftxt = open(filename[:-4]+".txt","w", encoding="shiftjis")
    fjson = open(filename[:-4]+".json","w",encoding="shiftjis")
    contents = []
    fbin = open(filename,"rb")
    if translate:
        translator = Translator()
        print("Translating {}".format(filename))
        currentpointer = 0
        totalpointers = len(pointers)
    for pointer in pointers: 
        pointerDict = {}
        try:
            if CODEDICT[pointer[1]] == "INVALID":
                continue
            pointerDict["Type"] = CODEDICT[pointer[1]]
        except KeyError:
            pointerDict["Type"] = int.from_bytes(pointer[1],"little")
            #continue
        pointerDict["Size"]=pointer[2]
        pointerDict["Offset"]=pointer[3]
        pointerDict["Text Position"]=pointer[3] + textaddr
        pointerDict["Pointer Position"]=pointer[0]
        

        while fbin.tell() < pointer[3]+textaddr:
            fbin.read(1)
        pointercontents = fbin.read(pointer[2])
        decodedtext = pointercontents.decode("shiftjis")
        if translate:
            print("Translating {} of {}. {:.2}%".format(currentpointer,totalpointers,currentpointer/totalpointers*100))
            #ftxt.write(translator.translate(decodedtext,src="ja",dest="en").text)
            pointerDict["Translated Text"]=translator.translate(decodedtext,src="ja",dest="en").text
            currentpointer = currentpointer + 1
        pointerDict["Original Text"] = decodedtext
        pointerDict["New Text"] = ""   
        #ftxt.write("\n\n")
        contents.append(pointerDict)
    payload = {
        "Code Address":codeaddr,
        "Text Address":textaddr,
        "Original Text Block Size":size,
        "pointers":contents
    }
    json.dump(payload,fjson,ensure_ascii=False,indent=4)
    fjson.close()
    fbin.close()

def convertAllFiles():
    files = listdir()
    binfiles = []
    for file in files:
        if (file[-4:] == ".bin"):
            binfiles.append(file)
    for binfile in binfiles:
        #print("Found {} pointers".format(len(findPointers(binfile))))
        structs = findPointers(binfile) #pointer info and start of text address
        genText(structs[0], binfile, structs[1], structs[2], structs[3], False)
    print("Extraction Complete")

def insertNewText(jsonfilename):
    with open(jsonfilename,"r", encoding="shiftjis") as f:
        contents = json.load(f)
    binfile = jsonfilename[:-5]+".bin"
    copyfile(binfile, binfile+"~")
    endaddr = contents.get("Original Text Block Size") + contents.get("Text Address")
    fbintil = open(binfile+"~", "ab")
    total_offset = 0
    for pointer in contents.get("pointers"):
        newtext = pointer.get("New Text")
        newtextbin = bytearray(newtext, "shiftjis")
        newsize = len(newtextbin)
        fbintil.seek(endaddr + total_offset)
        fbintil.write(newtextbin)
        pointer["Size"] = newsize
        pointer["Text Position"] = endaddr + total_offset
        pointer["Offset"] = pointer["Text Position"] - contents.get("Text Address")
        total_offset += newsize
    contents["New Text Block Size"] = contents["Original Text Block Size"] + total_offset
    fbintil.close()
    with open(binfile + "~", 'rb+') as fbintil:
        fbintil.seek(8)
        fbintil.write(int2bytes(contents["New Text Block Size"]))
    with open(jsonfilename, "w",encoding="shiftjis") as f:
        json.dump(contents, f, ensure_ascii=False, indent = 4)
    return

def updatePointers(jsonfilename):
    with open(jsonfilename, "r",encoding="shiftjis") as json_file:
        contents = json.load(json_file)
    binfilename = jsonfilename[:-5]+".bin"
    fbintil = open(binfilename+"~","rb+")
    for pointer in contents["pointers"]:
        fbintil.seek(pointer["Pointer Position"])
        assert fbintil.read(2) == b'\x03\x01'
        fbintil.write(int2bytes(pointer["Size"]))
        fbintil.write(int2bytes(pointer["Offset"],4))
    return

def validatejson(jsonfilename):
    with open(jsonfilename, "r",encoding="shiftjis") as json_file:
        contents = json.load(json_file)
    offset = 0
    for pointer in contents["pointers"]:
        try:
            assert offset == pointer["Offset"]
        except:
            print("Validation filtered a Pointer in position {}".format(pointer["Pointer Position"]))
            del pointer
            continue
        offset = offset + pointer["Size"]
    with open(jsonfilename, "w",encoding="shiftjis") as f:
        json.dump(contents, f, ensure_ascii=False, indent = 4)
    print("Json Validated!")

convertAllFiles()
#insertNewText("101_1_1.json")
#updatePointers("101_1_1.json")  
validatejson("101_1_1.json")

    
        
