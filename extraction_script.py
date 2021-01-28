from collections import deque
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
        startaddrbin = fbin.read(4)
        sizebin = fbin.read(2)
        startaddr = int.from_bytes(startaddrbin,"little")
        size = int.from_bytes(sizebin,"little")
        print("Start address is {} and Size is {}".format(startaddr,size))
        fbin.read(2) #TODO check if 0000
        fbin.read(20) #???? and a bunch of 0s
        buffer = deque(fbin.read(4),6) #Bytes are being pushed into a dequeue and iterated along the code. The queue is at most 6 bytes long, whenever a bit is pushed to the right, a byte must be popped from the left.
        pointers_found = 0
        while fbin.tell() < startaddr:  #fbin.tell() returns cursor position. pretty neat, iterate pointer table region until you reach actual memory
            buffer.append(fbin.read(1))     
            buffer.append(fbin.read(1))
            #print("Position:{} Buffer is".format(fbin.tell()))
            #print(buffer)
            if (buffer[0] == b'\x04' and buffer[1] == b'\x01' and buffer[4] == b'\x03' and buffer[5] == b'\x01'):
                scripttype = buffer[3] + buffer[2] 
                peekresult = fbin.peek(4) # read 4 bytes ahead without moving the cursor
                bytescount = peekresult[1:2] + peekresult[0:1] #indexing a byte directly converts it into an int. need to slice it like this.
                offset = peekresult[3:4] + peekresult[2:3]
                print("FOUND A POINTER in position {:d}! Type = {}  Size = {}  Offset = {}".format(fbin.tell(),scripttype.hex(),bytescount.hex(),offset.hex()))
                pointers_found = pointers_found +1
            buffer.popleft()
            buffer.popleft()
    return pointers_found
    
print("Found {} pointers".format(extract()))

    
        
