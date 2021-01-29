from os import listdir
from io import BufferedReader

"""Important xxxx opcodes
0x003C = dialog text
0x003E = speaker name
0x0039 = choice
0x0046 = chapter name"""

CODEDICT={b"\x00\x3c":"Dialog",b"\x00\x3e":"Speaker",b"\x00\x39":"Choice",b"\x00\x46":"Chapter name",}
def findPointers(filename):
    #files = listdir()
    pointers = []
    """ for file in files:
        if (file[-4:] == ".bin"):
            binfiles.append(file) """
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
        cursor = fbin.tell()            
        if (peekresult[0:1] == b'\x03' and peekresult[1:2] == b'\x01'):
            scripttype = buffer[1] + buffer[0] 
            bytescount = peekresult[3:4] + peekresult[2:3] #indexing a byte directly converts it into an int. need to slice it like this.
            offset = peekresult[7:8] + peekresult[6:7] + peekresult[5:6] + peekresult[4:5]
            print("FOUND A POINTER in position {:X}! Type = {}  Size = {}  Offset = {}".format(fbin.tell(),scripttype.hex(),bytescount.hex(),offset.hex()))
            pointers.append((fbin.tell(), scripttype, bytescount, offset))
    fbin.close()
    return (pointers,textaddr)

def genText(pointers,filename,textaddr):
    ftxt = open(filename[:-4]+".txt","w", encoding="shiftjis")
    fbin = open(filename,"rb")
    for pointer in pointers: 
        print(pointer)
        try:
            ftxt.write("Type: {}\n".format(CODEDICT[pointer[1]]))
        except KeyError:
            #ftxt.write("Type: {}\n".format(pointer[1]))  #these are unknown pointer types, enable them if you want
            continue
        ftxt.write("Size: {}\n".format(int.from_bytes(pointer[2],"big")))  
        print("Size: {}".format(int.from_bytes(pointer[2],"big")))  
        ftxt.write("Offset: {}\n".format(pointer[3].hex()))

        ftxt.write("Text Position: {:x}\n".format((int.from_bytes(pointer[3],"big")+textaddr)))
        ftxt.write("Pointer Position: {}\n".format(pointer[0]))
        print(int.from_bytes(pointer[3],"big")+textaddr)
        print(fbin.tell())    
        while fbin.tell() < int.from_bytes(pointer[3],"big")+textaddr:
            fbin.read(1)
        print(fbin.tell())    
        pointercontents = fbin.read(int.from_bytes(pointer[2],"big"))
        #print(pointercontents)
        ftxt.write(pointercontents.decode("shiftjis"))
        ftxt.write("\n\n")
        break
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
        genText(structs[0], binfile, structs[1])
    print("Extraction Complete")

convertAllFiles()    

    
        
