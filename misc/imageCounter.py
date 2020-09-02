'''
Script used to count number of images in a proprietary video file
'''
import struct
import binascii
import re
import math
import os
import sys
import argparse

PATH = "/home/ubuntu/file.*"

def run(args.path):
    with open(args.path, 'rb') as f:
        content = f.read()
    #print(content)    

    hexContent= binascii.hexlify(content)
    hexToStrContent= str(hexContent)

    print(hexToStrContent.count('0x*'))

def main():
    parser = argparse.ArgumentParser(description='Count number of images in a proprietary video file')
    parser.add_argument('-r', '--root_dir', default=os.path.join(os.environ['HOME'], 'Videos'), help='root directory')
    parser.add_argument('-p', '--path', help='video path')
    args = parser.parse_args()
    run(args)

if __name__ == "__main__":
    main()
