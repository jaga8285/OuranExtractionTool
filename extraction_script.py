from collections import deque
from os import listdir
def extract():
    files = listdir()
    print(files)
    binfiles = []
    for file in files:
        if (file[-4:] == ".bin"):
            binfiles.append(file)
            
    for file in binfiles:
        fbin = open(file,"rb")
        ftxt = open(file[:-4]+".txt","w", encoding="shiftjis")
        fbin.read(4) #TODO check if 00000000
        startaddrbin = fbin.read(4)
        sizebin = fbin.read(2)
        startaddr = int.from_bytes(startaddrbin,"little")
        size = int.from_bytes(sizebin,"little")
        print("Start address is {} and Size is {}".format(startaddr,size))
        fbin.read(2) #TODO check if 0000
        fbin.read(20) #???? and a bunch of 0s
        buffer = deque(fbin.read(4))
        cursor = 26
        pointers_found = 0
        while cursor < startaddr*2:     
            buffer.append(fbin.read(1))     
            buffer.append(fbin.read(1))
            cursor=cursor+2
            #print("Position:{} Buffer is".format(cursor))
            #print(buffer)
            if (buffer[0] == b'\x04' and buffer[1] == b'\x01' and buffer[4] == b'\x03' and buffer[5] == b'\x01'):
                scripttype = buffer[3] + buffer[2]
                cursor=cursor+2  
                buffer.append(fbin.read(1))     
                buffer.append(fbin.read(1))     
                buffer.append(fbin.read(1))     
                buffer.append(fbin.read(1))
                bytescount = buffer[7] + buffer[6]
                cursor=cursor+2
                offset = buffer[9] + buffer[8]
                cursor=cursor+2
                #print("FOUND A POINTER in position {:d}! Type = {}  Size = {}  Offset = {}".format(cursor,scripttype.hex(),bytescount.hex(),offset.hex()))
                pointers_found = pointers_found +1
                buffer.popleft()
                buffer.popleft()
                buffer.popleft()
                buffer.popleft()
            buffer.popleft()
            buffer.popleft()
        print(scripttype)
        print(bytescount)
        print(offset)
        print(int.from_bytes(scripttype,"big"))
    return pointers_found
    
print("Found {} pointers".format(extract()))

    
        
