#    Xiaomi logo.img Extractor
#    Copyright (C) <year>  <name of author>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

HEADER = b'LOGO!!!!'
BMP_HEADER = b'BM'

from struct import *

def check_header(b):
    (header,) = unpack("<8s", b[0x4000:0x4008])
    if header != HEADER:
        print("wrong header", header)
        raise ValueError("Wrong Header")

def get_offsets(b):
    img_offset = 0
    img_offsets = []
    cbyte = 0x4008

    while True:
        last_offset = img_offset
        (img_offset,) = unpack("<I", b[cbyte:cbyte+4])
        cbyte += 4
        if img_offset == 0:
            break
        else:
            if (img_offset + last_offset) * 0x1000 in img_offsets:
                # Sometimes they show up twice. Skip.
                continue
            img_offsets.append((img_offset + last_offset) * 0x1000)
    # The last one is the end of the file. Skip.
    img_offsets.pop()
    return img_offsets

def extract(f):
    binary = f.read()
    check_header(binary)

    img_offsets = get_offsets(binary)

    # Formatted as BMP. Detect file length
    img_cnt = 0
    outs = []
    for img_offset in img_offsets:
        img_cnt += 1
        (header, size) = unpack("<2sI", binary[img_offset:img_offset+6])
        if header != BMP_HEADER:
            print('corrupt bmp header skipping')
            continue
        outbuff = binary[img_offset:img_offset+size]
        outs.append(outbuff)
    return outs

def edit(orig_imgs, new_imgs):
    binary = bytearray(orig_imgs.read())
    check_header(binary)

    img_offsets = get_offsets(binary)

    if len(img_offsets) != len(new_imgs):
        raise ValueError("All images must be replaced")

    # Formatted as BMP. Detect file length
    img_cnt = 0
    lens = []
    for img_offset in img_offsets:
        (header, size) = unpack("<2sI", binary[img_offset:img_offset+6])
        if header != BMP_HEADER:
            print('corrupt bmp header skipping')
            continue
        if len(new_imgs[img_cnt]) > size:
            raise ValueError("Cannot make image larger")
        (header, size) = unpack("<2sI", new_imgs[img_cnt][:6])
        if header != BMP_HEADER:
            raise ValueError('cannot add corrupt bmp header')
        if size != len(new_imgs[img_cnt]):
            raise ValueError("Won't add image that lies about size, who knows what would happen")

        # Safety checks passed
        binary[img_offset:img_offset+size] = new_imgs[img_cnt]

        img_cnt += 1

    return binary
