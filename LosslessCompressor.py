import tkinter as tk
import tkinter.filedialog
from time import sleep
from threading import Thread
import os, struct, heapq, time

old_pixels = [] #original image size
current_pixels = [] #current image so that brightness and scaler can both work at the same time
# to keep track of r,g,b enable/disable
r = True
g = True
b = True
file_type = b'CMPT365' #to check file types
image = None

def huffman_code(length_table):

    index = []
    huffman_codes = {}
    
    for ind, x in enumerate(length_table):
        if x > 0:
            i = (x, ind)
            index.append(i)
    
    if not index:
        # no pixel with any height
        return huffman_codes
    
    index.sort()
    c = 0
    prev = index[0][0]
    # shifting left for the code length difference

    for x, y in index:
        # shift if code length changes
        if x != prev:
            c = c << (x - prev)
            prev = x
         #put current huffman code to y
        huffman_codes[y] = (c, x)
        c = c + 1

    return huffman_codes

def huffman_tree(frequency_table):
    # build tree by combining two lowest frequency nodes until one node left
    heap_tree = []
    return_list = [0] * 256
    # if pixel frequency is more than 0, add it to the heap
    for x, y in enumerate(frequency_table):
        if y > 0:
            heapq.heappush(heap_tree, (y, x))
    
    if not heap_tree:
        # no pixel case
        return return_list
    
    if len(heap_tree) == 1:
        # one pixel type case
        x, y = heap_tree[0]
        return_list[y] = 1
        return return_list
    
    heapq.heapify(heap_tree)
    parent_nodes={}
    child_nodes={}
    next = 256 # to not mixup with 0-255 pixel values
    while (len(heap_tree) > 1):
        #pop the two lowest frequency nodes and create a parent node
        frequency1, node1 = heapq.heappop(heap_tree)
        frequency2, node2 = heapq.heappop(heap_tree)
        parent_node = next
        next = next + 1
        parent_nodes[node1] = parent_node
        parent_nodes[node2] = parent_node
        child_nodes[parent_node] = (node1, node2)
        heapq.heappush(heap_tree, (frequency1 + frequency2, parent_node))
    
    root_node = heap_tree[0][1]
    for x in range(256):
        #height would be the code length

        if frequency_table[x] > 0:
            curr_node = x
            height = 0
            #traverse heap
            while curr_node in parent_nodes:
                height = height + 1
                curr_node = parent_nodes[curr_node]
            return_list[x] = height
    return return_list

def pixel_frequency_table(data_bytes):
    # get the frequency of each pixel value in an image
    x = [0] * 256
    for pixel in data_bytes:
        x[pixel] += 1
    return x

def check_is_bmp(bmp_bytes):
    return bmp_bytes[:2]

def get_file_size(bmp_bytes):
    return int.from_bytes(bmp_bytes[2:6], 'little')

def get_width(bmp_bytes):
    return int.from_bytes(bmp_bytes[18:22], 'little')

def get_height(bmp_bytes):
    return int.from_bytes(bmp_bytes[22:26], 'little')

def get_bpp(bmp_bytes):
    return int.from_bytes(bmp_bytes[28:30], 'little')

def get_pixel_data(bmp_bytes):
    pixel_data_index = int.from_bytes(bmp_bytes[10:14], 'little')
    return bmp_bytes[pixel_data_index:]

def get_colour_table(bmp_bytes):
    colour_table_index = int.from_bytes(bmp_bytes[10:14], 'little')
    return bmp_bytes[54:colour_table_index]

def compress_bmp():
    #time compression
    start_time = time.time()
    try:
        file_path = file_path_entry.get()
        if not file_path:
            print("No file selected")
            check_label.config(text="No file selected")
            #stop time get ms
            end_time = time.time()
            return
        with open(file_path, "rb") as f:
            bmp_bytes = f.read()
    except Exception as e:
        print(f"BMP file not read {e}")
        check_label.config(text="BMP file not read")
        #stop time get ms
        end_time = time.time()
        return

    if (check_is_bmp(bmp_bytes) != b'BM'):
        print("Not a BMP file")
        check_label.config(text="This is not a BMP file, retry")
        #stop time get ms
        end_time = time.time()
        return
    
    #get all metadata
    o_size = get_file_size(bmp_bytes)
    w = get_width(bmp_bytes)
    h = get_height(bmp_bytes)
    bpp = get_bpp(bmp_bytes)
    pixel_data = get_pixel_data(bmp_bytes)
    colour_table = None
    if (bpp == 1 or bpp == 4 or bpp == 8):
        #no colour table if bpp is 24
        colour_table = get_colour_table(bmp_bytes)
    #get frequency table and huffman tree
    frequency_table = pixel_frequency_table(pixel_data)
    huff_tree = huffman_tree(frequency_table)

    newpath = file_path.rsplit('.', 1)[0] + '.cmpt365'
    #create .cmpt365 compressed file
    if (colour_table == None):

        new_bytes = file_type_creator(newpath, o_size,w, h, bpp, b'', pixel_data, huff_tree)
    else:
        new_bytes = file_type_creator(newpath, o_size,w, h, bpp, colour_table, pixel_data, huff_tree)
    
    #stop time get ms
    end_time = time.time()
    compression_time = (end_time - start_time) * 1000

    try:
        comp_size = os.path.getsize(newpath)
    except:
        comp_size = new_bytes
    
    comp_ratio = o_size / comp_size 
    
    check_label.config(text=f"Compression finished"
                       f"\nOriginal Size: {o_size} bytes"
                       f"\nCompressed Size: {comp_size} bytes"
                       f"\nCompression Ratio: {comp_ratio:.4f}"
                       f"\nTime: {compression_time:.2f} ms")

def huffman_encoding(data_bytes, huffman_codes):
    buffer = 0
    counter = 0
    output = bytearray()
    for data in data_bytes:
        # get the huffman code and length
        coding, length = huffman_codes[data]

        counter = counter + length
        buffer = (buffer << length) | coding
        # take a byte while buffer has 8 or more bits while keeping remaining bits
        while counter >= 8:

            x = counter - 8
            byte = (buffer >> x) & 0xFF
            output.append(byte)
            buffer = buffer & ((1<< x) - 1)
            counter = counter - 8
    
    if counter > 0:
        byte = (buffer << (8 - counter)) & 0xFF
        output.append(byte) #zero padding on right for last byte

    tot = 0
    value = [huffman_codes[y][1] for y in data_bytes]
    for x in value:
        tot = tot + x
    
    #get total bit length
    bitlength = 0
    for x in data_bytes:
        bitlength = bitlength + huffman_codes[x][1]
    return bytes(output), bitlength

def decompress():
    path = tk.filedialog.askopenfilename()
    if not path:
        return
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, path)
    try:
        metadata = read_special_file(path)
    except Exception:
        print("Not a .cmpt365 file")
        check_label.config(text="Not a .cmpt365 file")
        return
    #get compressed metadata
    lengths = metadata["lengths"]
    bitlength = metadata["bitlength"]
    compressed_bytes = metadata["encoded_bytes"]

    #decompress the huffman encoding and get original pixel bytes
    pixel_data = huffman_decoding(compressed_bytes, bitlength, lengths)
    
    w = metadata["width"]
    h = metadata["height"]
    bpp = metadata["bpp"]
    colour_table = metadata["colour_table"] if metadata["colour_table"] else None
    
    try:
        #display the image after decompressing
        img = display_compressed_image(pixel_data, colour_table, w, h, bpp)
    except Exception:
        print("Decompression failed")
        check_label.config(text="Decompression failed")
        return
    
    global image
    if image: #refresh
        image.destroy()
    image = tk.Label(root, image = img)
    image.image = img
    image.grid(row=3, column=1)

    check_label.config(text= f"Decompression complete!\n"
                       f'Decompressed Size: {metadata["original_file_size"]} bytes')


def huffman_decoding(encoded_bytes, bitlength, lengths):
    #huffman code from lengths
    huffman_codes = huffman_code(lengths)
    if not huffman_codes:
        return b''
    
    #(code, length) gets a symbol
    decoded={}
    for index, (c, l) in huffman_codes.items():
        decoded[(c, l)] = index

    output = bytearray()
    value = 0
    length = 0
    num_read = 0
    tot_bits = bitlength
    #go through every byte in the encoded bytes
    for x in encoded_bytes:
        for y in range(8):
            if num_read >= tot_bits:
                #break if the total bit length is reached
                break
            #Get most significant bit first
            b = (x >> (7 - y)) & 0x01
            value = (value << 1) | b
            num_read = num_read + 1
            length = length + 1
            index = (value, length)

            #check if it is valid
            if index in decoded:
                output.append(decoded[index])
                value = 0
                length = 0
            
        if num_read >= tot_bits:
            break
    return bytes(output)

def read_special_file(filepath, update_label=True):
    with open (filepath, "rb") as f:
        cmpt365_bytes = f.read()
    
    if (cmpt365_bytes[:7] != file_type):
        print("Not a CMPT365 file")
        if update_label:
            check_label.config(text="This is not a CMPT365 file, retry")
    else:
        print("This is a CMPT365 file")
        if update_label:
            check_label.config(text="CMPT365 file check successful")
    #read metadata
    original_file_size = int.from_bytes(cmpt365_bytes[7:11], 'little')

    w = int.from_bytes(cmpt365_bytes[11:15], 'little')
    h = int.from_bytes(cmpt365_bytes[15:19], 'little')
    bpp = int.from_bytes(cmpt365_bytes[19:21], 'little')
    colour_size = int.from_bytes(cmpt365_bytes[21:25], 'little')
    pixel_data_size = int.from_bytes(cmpt365_bytes[25:29], 'little')
   
    #get colour table
    colour_table = None
    if colour_size > 0:
        colour_table = cmpt365_bytes[29:29 + colour_size]
    
    byte_pos = 29 + colour_size
    pixel_data = cmpt365_bytes[byte_pos:byte_pos + pixel_data_size]
    
    lengths = []
 
    for i in range(256):
        lengths.append(cmpt365_bytes[byte_pos])
        byte_pos += 1

    #read bit length
    
    bitlength = int.from_bytes(cmpt365_bytes[byte_pos:byte_pos + 8], 'little')
    byte_pos += 8

    # read encoded bytes
    encoded_bytes = cmpt365_bytes[byte_pos:]

    return {
        "original_file_size": original_file_size,
        "width": w,
        "height": h,
        "bpp": bpp,
        "colour_table": colour_table,
        "pixel_data": pixel_data,
        "lengths": lengths,
        "bitlength": bitlength,
        "encoded_bytes": encoded_bytes
    }

def file_type_creator(filepath, original_file_size, w, h, bpp, colour_table, pixel_data, lengths):
    huffman_codes = huffman_code(lengths)
    size = 293
    #encode
    encoded_bytes, bitlength = huffman_encoding(pixel_data, huffman_codes)
    #write metadata for .CMPT365 file
    with open(filepath, "wb") as f:
        f.write(file_type) #.CMPT365 file 7 bytes
        f.write(struct.pack("<I", original_file_size)) #4 bytes
        f.write(struct.pack("<I", w)) #4 bytes
        f.write(struct.pack("<I", h)) #4 bytes
        f.write(struct.pack("<H", bpp)) #2 
        colour_size = 0
        if colour_table is not None:
            colour_size = len(colour_table)
        f.write(struct.pack("<I", colour_size))
        f.write(struct.pack("<I", len(pixel_data)))
        if colour_size:
            f.write(colour_table) 
        
        for x in lengths:
            f.write(struct.pack("<B", x)) #256 bytes
        
        f.write(struct.pack("<Q", bitlength)) #8 bytes
        f.write(encoded_bytes)
    
    return len(encoded_bytes) + size + colour_size
        


def display_compressed_image(pixel_data, colour_table, w, h, bpp):

    img = tk.PhotoImage(width=w, height=h)

    if bpp == 24:
        for y in range(h):
            
            # pad to 4-bytes, going from bottom to top
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y) 
            for x in range(w):
                #location of the pixel's first byte
                c = a + x * 3
                if c + 2 < len(pixel_data):
                    
                    r = pixel_data[c+2]
                    g = pixel_data[c+1]
                    b = pixel_data[c]
                else:
                    #prevent out of range indexing
                    continue

                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
           
    # for 8
    elif bpp == 8:
        #every pixel maps to one index
        for y in range(h):
           
            # pad to 4-bytes, going from bottom to top
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y)
            for x in range(w):
                c = a + x 
                colour_index = pixel_data[c]
                if colour_table and (colour_index*4) + 2 < len(colour_table):
                    # Every index is 4 bytes with reserved
                    r = colour_table[(colour_index*4)+2]
                    g = colour_table[(colour_index*4)+1]
                    b = colour_table[(colour_index*4)]
                else:
                    continue
                #print(colour)
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
    #for 4
    # two pixels per byte
    elif bpp == 4:
        for y in range(h):
           
            # padded, going from bottom to top
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y)
            for x in range(w):
                c = a + (x // 2) 
                if x % 2 != 0:
                    # lower part, four least significant bits
                    # 4 right values
                    colour_index = pixel_data[c] & 0x0F
                else:
                    # upper part four most significant bits
                    # 4 left values
                    # push values to the right and retrieve
                    colour_index = (pixel_data[c] >> 4) & 0x0F
                if colour_table and (colour_index*4) + 2 < len(colour_table):
                    r = colour_table[(colour_index*4)+2]
                    g = colour_table[(colour_index*4)+1]
                    b = colour_table[(colour_index*4)]
                else:
                    continue

                #print(colour)
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
    #for 1
    # 8 pixels for a byte
    elif bpp == 1:

        for y in range(h):
            
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y)
            for x in range(w):
                # byte index
                c = a + (x // 8)
                # bit index
                z = 7 - (x % 8)
                # get one bit for the pixel
                colour_index = (pixel_data[c] >>  z) & 0x01
                if colour_table and (colour_index*4) + 2 < len(colour_table):
                    r=colour_table[(colour_index*4)+2]
                    g=colour_table[(colour_index*4)+1]
                    b=colour_table[(colour_index*4)]
                else:
                    continue
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
    #make a deep copy
    #print(current_pixels)
    return img

def browse_file():
    filepath = tk.filedialog.askopenfilename()
    file_path_entry.delete(0, tk.END)
    file_path_entry.insert(0, filepath)

def display_header_metadata(s, w, h, bpp):
    size_label.config(text="File Size: " + str(s))
    width_label.config(text="Image Width: " + str(w))
    height_label.config(text="Image height: " + str(h))
    bpp_label.config(text="Bits Per Pixel: " + str(bpp))

def change_brightness(val):
    global current_pixels
    #print(current_pixels)
    # 50% is original 25% half as bright
    # factor is 0 - 2
    new_val = float(val) / 50
    #if 50% just keep the original picture
    if new_val == 1.0:
        return
    w = len(current_pixels[0])
    h = len(current_pixels)
    new_img = tk.PhotoImage(width=w, height=h)
    y_count = 0
    #iterate through current_pixels so that the size doesnt reset
    for y in (current_pixels):
        x_count = 0
        for x in y:
            if (new_val < 1.0): #make darker
                r = min(255, int(x[0] * new_val))
                g = min(255, int(x[1] * new_val))
                b = min(255, int(x[2] * new_val))
            else: #make brighter
                r = min(255, int(x[0] * new_val + (new_val-1)*128))
                g = min(255, int(x[1] * new_val + (new_val-1)*128))
                b = min(255, int(x[2] * new_val + (new_val-1)*128))
            
            new_img.put(f"#{r:02x}{g:02x}{b:02x}", (x_count, y_count))
            x_count+=1
        y_count+=1
    
    image.config(image="")
    image.image= None
    image.configure(image=new_img)
    image.image = new_img

def change_size(val):
    global current_pixels, old_pixels
    #print(old_pixels)
    current_pixels.clear() #do not add to the original picture, change it
    new_val = float(val) / 50
    #50% original, 25% is half the size
    # factor is 0 - 2
    #if 50% just return original
    if new_val == 1.0:
        return
    #print(old_pixels)
    w = len(old_pixels[0]) * new_val
    h = len(old_pixels) * new_val
    #if 0% image disappears
    if (w == 0 or h == 0):
        image.config(image="")
        image.image= None
        return

    ratio_w = len(old_pixels[0]) / w
    ratio_h = len(old_pixels) / h
    new_img = tk.PhotoImage(width=int(w), height=int(h))
    
    for y in range(int(h)):
        row=[]
        for x in range(int(w)):
            #using pixel aggregation and flooring them with int
            r = old_pixels[int(y*ratio_h)][int(x*ratio_w)][0]
            g = old_pixels[int(y*ratio_h)][int(x*ratio_w)][1]
            b = old_pixels[int(y*ratio_h)][int(x*ratio_w)][2]
            row.append((r, g, b))
            new_img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
        current_pixels.append(row)
    
    image.config(image="")
    image.image= None
    image.configure(image=new_img)
    image.image = new_img
    brightness_slider.set(50)

def display_image(file_path, pixel_data, colour_table, w, h, bpp):
    global current_pixels
    img = tk.PhotoImage(width=w, height=h)
    old_pixels.clear()
    # calculate if bpp is 24
    #3 bytes per pixel
    if bpp == 24:
        for y in range(h):
            row=[]
            # pad to 4-bytes, going from bottom to top
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y) 
            for x in range(w):
                #location of the pixel's first byte
                c = a + x * 3
                
                r = pixel_data[c+2]
                g = pixel_data[c+1]
                b = pixel_data[c]
                row.append((r, g, b))
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
            old_pixels.append(row)
    # for 8
    elif bpp == 8:
        #every pixel maps to one index
        for y in range(h):
            row=[]
            # pad to 4-bytes, going from bottom to top
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y)
            for x in range(w):
                c = a + x 
                colour_index = pixel_data[c]
                
                # Every index is 4 bytes with reserved
                r = colour_table[(colour_index*4)+2]
                g = colour_table[(colour_index*4)+1]
                b = colour_table[(colour_index*4)]
                
                row.append((r, g, b))
                #print(colour)
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
            old_pixels.append(row)
    #for 4
    # two pixels per byte
    elif bpp == 4:
        for y in range(h):
            row =[]
            # padded, going from bottom to top
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y)
            for x in range(w):
                c = a + (x // 2) 
                
                if x % 2 != 0:
                    # lower part, four least significant bits
                    # 4 right values
                    colour_index = pixel_data[c] & 0x0F

                else:
                    # upper part four most significant bits
                    # 4 left values
                    # push values to the right and retrieve
                    colour_index = (pixel_data[c] >> 4) & 0x0F
                
                
                r = colour_table[(colour_index*4)+2]
                g = colour_table[(colour_index*4)+1]
                b = colour_table[(colour_index*4)]
                
                row.append((r, g, b))
                #print(colour)
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
            old_pixels.append(row)

    #for 1
    # 8 pixels for a byte
    elif bpp == 1:

        for y in range(h):
            row=[]
            a = (((bpp * w + 31) // 32) * 4) * (h - 1 - y)
            for x in range(w):
                # byte index
                c = a + (x // 8)
                # bit index
                z = 7 - (x % 8)
                
                # get one bit for the pixel
                colour_index = (pixel_data[c] >>  z) & 0x01
                
                r=colour_table[(colour_index*4)+2]
                g=colour_table[(colour_index*4)+1]
                b=colour_table[(colour_index*4)]
                
                row.append((r, g, b))
                img.put(f"#{r:02x}{g:02x}{b:02x}", (x, y))
            old_pixels.append(row)

    #make a deep copy
    current_pixels = [[pixel for pixel in row] for row in old_pixels]
    #print(current_pixels)
    return img
                

def rgb_toggle():
    
    global current_pixels, r, g, b, image
    if not current_pixels:
        # if current pixels is empty
        return
    
    w= len(current_pixels[0])
    h = len(current_pixels)
    new_img = tk.PhotoImage(width=w, height=h)
    for y in range(h):
        for x in range(w):
            # retrieve r,g,b tuple
            rgb= current_pixels[y][x]
            
            if (r): 
                #enable r
                new_r = rgb[0]
            else:
                #disable r
                new_r=0
            if (g):
                #enable g
                new_g = rgb[1]
            else:
                #disable g
                new_g=0
            if (b):
                #enable b
                new_b = rgb[2]
            else:
                #disable g
                new_b = 0
            new_img.put(f"#{new_r:02x}{new_g:02x}{new_b:02x}", (x, y))
    image.config(image="")
    image.image = None
    image.configure(image = new_img)
    image.image = new_img
    brightness_slider.set(50)

def r_toggle():
    global r
    r = not r
    rgb_toggle()

def g_toggle():
    global g
    g = not g
    rgb_toggle()

def b_toggle():
    global b
    b = not b
    rgb_toggle()

def get_metadata():
    global image, old_pixels, current_pixels
    file_path = file_path_entry.get()
    print(file_path)
    with open(file_path, "rb") as f:
        bmp_bytes = f.read()

    if (check_is_bmp(bmp_bytes) != b'BM'):
        print("Not a BMP file")
        check_label.config(text="This is not a BMF file, retry")
        return #so it does not crash
    else:
        print("This is a BMF file")
        check_label.config(text="BMF file check successful")
    old_pixels.clear()
    current_pixels.clear()
    brightness_slider.set(50)
    #remove old image overlap
    try:
        if image:
            image.destroy()
    except NameError:
        pass
    file_size = get_file_size(bmp_bytes)
    file_width = get_width(bmp_bytes)
    file_height = get_height(bmp_bytes)
    file_bpp = get_bpp(bmp_bytes)
    pixel_data = get_pixel_data(bmp_bytes)
    colour_table = None
    display_header_metadata(file_size, file_width, file_height, file_bpp)

    if (file_bpp in [1, 4, 8, 16, 24]):
        pixel_data=get_pixel_data(bmp_bytes)
    else:
        print("Error: bpp not valid")

    if (file_bpp in [1, 4, 8]):
        colour_table=get_colour_table(bmp_bytes)
    img=display_image(file_path, pixel_data, colour_table, file_width, file_height, file_bpp)
    # img=tk.PhotoImage(file=file_path)
    image=tk.Label(root, image=img)
    image.image=img
    image.grid(row=3, column=1)
    


root = tk.Tk()
#metadata
tk.Label(root, text="File Path").grid(row=0, column=0)
check_label=tk.Label(root, text="")
check_label.grid(row=8, column=0)
tk.Label(root, text="Header Metadata:").grid(row=3, column=0)
size_label=tk.Label(root, text="File Size: ")
size_label.grid(row=4, column=0)
width_label=tk.Label(root, text="Image Width: ")
width_label.grid(row=5, column=0)
height_label=tk.Label(root, text="Image height: ")
height_label.grid(row=6, column=0)
bpp_label=tk.Label(root, text="Bits Per Pixel: ")
bpp_label.grid(row=7, column=0)

#sliders
brightness_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, label="Brightness", command=change_brightness)
brightness_slider.grid(row=9, column=7)
brightness_slider.set(50)
scale_slider = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, label="Size Scaler", command=change_size)
scale_slider.grid(row=9, column=8)
scale_slider.set(50)
file_path_entry = tk.Entry(root, width=80)
file_path_entry.grid(row=0, column=1)

#buttons
tk.Button(root, text="Browse", command=browse_file).grid(row=1, column=0)
tk.Button(root, text="Get Metadata", command=get_metadata).grid(row=1, column=1)
r_butt = tk.Button(root, text="Enable/Disable R", command=r_toggle)
g_butt = tk.Button(root, text="Enable/Disable G", command=g_toggle)
b_butt = tk.Button(root, text="Enable/Disable B", command=b_toggle)

tk.Button(root, text="Compress (huffmann)", command=compress_bmp).grid(row=13, column=0)
tk.Button(root, text="Decompress", command=decompress).grid(row=14, column=0)
r_butt.grid(row=10, column = 0)
g_butt.grid(row=11, column=0)
b_butt.grid(row=12, column=0)

root.mainloop()
