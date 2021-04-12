import sys
import os
import shutil
import click
import dumper
dumper.max_depth = 10
import hashlib
import re


class BinaryStore():
    def __init__(self, bin_store_dir):
        self.bin_store_dir = bin_store_dir
        self.validator = re.compile('[0-9a-f]+')

    def is_valid_hex(self, sum):
        retval = True

        if len(sum) == 64:
            m = self.validator.match(sum)
            s,l =  m.span()
            if not (s == 0 and l == 64):
                retval = False
        else:
            retval = False

        return retval

    def hex_to_path(self, sum):
        chunks, chunk_size = len(sum), 4
        store_path_list = [sum[i:i+chunk_size] for i in range(0, chunks, chunk_size)]
        store_path = os.path.join(self.bin_store_dir, *store_path_list)
        return store_path


    def path_to_hex(self, path):
        return ('').join(path.split('binstore')[1].split('/')[1:])


    def buffer_to_path(self, buf):
        dig = hashlib.sha256()
        dig.update(buf)
        sum = dig.hexdigest()
        return (sum, self.hex_to_path(sum))


    def put_buffer(self, data):
        sum, store_path = self.buffer_to_path(data)
        print(store_path)
        if not os.path.exists(store_path):
            store_dir = os.path.dirname(store_path)
            store_file = os.path.basename(store_path)
            # print (store_dir, store_file)
            try:
                os.makedirs(store_dir)
            except OSError:
                if not os.path.isdir(store_dir):
                    raise
        with open(store_path, "wb") as f:
            f.write(data)

        return sum


    def put_file(self, src_path):
        blob = None

        with open(src_path, "rb") as f:
            blob = f.read()

        sum, store_path = self.buffer_to_path(blob)
        if not os.path.exists(store_path):
            store_dir = os.path.dirname(store_path)
            store_file = os.path.basename(store_path)
            # print (store_dir, store_file)
            try:
                os.makedirs(store_dir)
            except OSError:
                if not os.path.isdir(store_dir):
                    raise

            shutil.copy(src_path, store_path)

        return sum



    def get(self, signature):
        return self.hex_to_path(signature)
