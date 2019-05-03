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
import sys

def extract(f):
    binary = f.read()
    (header,) = unpack("<8s", binary[0x4000:0x4008])
    if header != HEADER:
        print("wrong header", header)
        sys.exit(1)

    img_offset = 0
    img_offsets = []
    cbyte = 0x4008

    while True:
        last_offset = img_offset
        (img_offset,) = unpack("<I", binary[cbyte:cbyte+4])
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
