from os import listdir
from io import BufferedReader
from pygoogletranslation import Translator

"""Important xxxx opcodes
0x003C = dialog text
0x003E = speaker name
0x0039 = choice
0x0046 = chapter name"""

CODEDICT={b"\x00\x3c":"Dialog",b"\x00\x3e":"Speaker",b"\x00\x39":"Choice",b"\x00\x46":"Chapter name",}
def findPointers(filename):
    pointers = []
    fbin = BufferedReader(open(filename,"rb")) #BufferedReader allows peeking ahead without moving the cursor
    fbin.read(4) #TODO check if 00000000
    textaddrbin = fbin.read(4)
    sizebin = fbin.read(4) #might be 4 bytes
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
        peekresult = fbin.peek(8) # read 4 bytes ahead without moving the cursor
        #cursor = fbin.tell()            
        if (peekresult[0:1] == b'\x03' and peekresult[1:2] == b'\x01'):
            scripttype = buffer[1] + buffer[0] 
            bytescount = peekresult[3] * 256 + peekresult[2] #indexing a byte directly converts it into an int. need to slice it like this.
            offset = (peekresult[7] *256 + peekresult[6]) * 0x7fff + peekresult[5] * 256 + peekresult[4]
            #print("FOUND A POINTER in position {:X}! Type = {}  Size = {}  Offset = {}".format(fbin.tell(),scripttype.hex(),bytescount.hex(),offset.hex()))
            pointers.append((fbin.tell(), scripttype, bytescount, offset))
    fbin.close()
    return (pointers,textaddr)

def genText(pointers,filename,textaddr,translate=False):
    ftxt = open(filename[:-4]+".txt","w", encoding="shiftjis")
    fbin = open(filename,"rb")
    if translate:
        translator = Translator()
        fbin = open(filename,"rb")
        japanesetext = []

        for pointer in pointers: 
            try:  
                CODEDICT[pointer[1]]
            except KeyError:
                continue
            while fbin.tell() < pointer[3]+textaddr:
                fbin.read(1)
            pointercontents = fbin.read(pointer[2])
            japanesetext.append(pointercontents.decode("shiftjis"))
        translated = translator.translate(japanesetext[0:1],src="ja",dest="en")
    for pointer in pointers: 
        try:
            ftxt.write("Type: {}\n".format(CODEDICT[pointer[1]]))
        except KeyError:
            #ftxt.write("Type: {}\n".format(pointer[1]))  #these are unknown pointer types, enable them if you want
            continue
        ftxt.write("Size: {}\n".format(pointer[2]))  
        ftxt.write("Offset: {:x}\n".format(pointer[3]))
        ftxt.write("Text Position: {:x}\n".format(pointer[3]+textaddr))
        ftxt.write("Pointer Position: {:x}\n".format(pointer[0]))   
        if translate:
            translation = translated.pop[0]
            ftxt.write("{}\n{}\n".format(translation["origin"],translation["text"]))
        else:
            while fbin.tell() < pointer[3]+textaddr:
                fbin.read(1)
            pointercontents = fbin.read(pointer[2])
            ftxt.write(pointercontents.decode("shiftjis"))
            ftxt.write("\n\n")
    ftxt.close()
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
        genText(structs[0], binfile, structs[1],True)
    print("Extraction Complete")

convertAllFiles()    

    
        
