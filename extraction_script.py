from os import listdir
from io import BufferedReader
def extract():
    files = listdir()
    binfiles = []
    for file in files:
        if (file[-4:] == ".bin"):
            binfiles.append(file)
            
    for file in binfiles:
        fbin = BufferedReader(open(file,"rb")) #BufferedReader allows peeking ahead without moving the cursor
        ftxt = open(file[:-4]+".txt","w", encoding="shiftjis")
        fbin.read(4) #TODO check if 00000000
        textaddrbin = fbin.read(4)
        sizebin = fbin.read(4) #might be 4 bytes
        fbin.read(8)
        codeaddrbin = fbin.read(4)
        textaddr = int.from_bytes(textaddrbin,"little")
        codeaddr = int.from_bytes(codeaddrbin,"little")
        size = int.from_bytes(sizebin,"little")
        print("Start Text address is \\x{:x}, Start Code address is \\x{:x} and Size is {}".format(textaddr,codeaddr,size))

        pointers_found = 0
        while fbin.tell() < codeaddr:
            fbin.read(2)
        while fbin.tell() < textaddr:  #fbin.tell() returns cursor position. pretty neat, iterate pointer table region until you reach actual memory
            buffer = (fbin.read(1),fbin.read(1))
            peekresult = fbin.peek(4) # read 4 bytes ahead without moving the cursor            
            #if (buffer[0] == b'\x04' and buffer[1] == b'\x01' and buffer[4] == b'\x03' and buffer[5] == b'\x01'):
            if (peekresult[0:1] == b'\x03' and peekresult[1:2] == b'\x01'):
                scripttype = buffer[1] + buffer[0] 
                bytescount = peekresult[3:4] + peekresult[2:3] #indexing a byte directly converts it into an int. need to slice it like this.
                offset = peekresult[7:8] + peekresult[6:7] + peekresult[5:6] + peekresult[4:5]
                print("FOUND A POINTER in position {:x}! Type = {}  Size = {}  Offset = {}".format(fbin.tell(),scripttype.hex(),bytescount.hex(),offset.hex()))
                pointers_found = pointers_found +1
    return pointers_found
    
print("Found {} pointers".format(extract()))

    
        
