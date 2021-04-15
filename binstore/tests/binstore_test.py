import pytest
from binstore import BinaryStore
import numpy as np
import os


bin_store_dir = os.path.expanduser('~/Data/test')
file_to_store = os.path.expanduser('~/Download/jdk-8u231-linux-x64.tar.gz')
bs = BinaryStore(bin_store_dir)


class TestBinaryStore:

    def test_valid_hex(self):
        assert bs.is_valid_hex('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')

    def test_invalid_hex(self):
        assert not bs.is_valid_hex('asdfghjklqwertyuasdfghjklqwertyuasdfghjklqwertyuasdfghjklqwertyu')

    def test_real_file_signature(self):
        signature = bs.put_file(file_to_store)
        assert bs.is_valid_hex(signature)

    def test_get(self):
        assert bs.get(bs.put_file(file_to_store)) \
            == os.path.join(bin_store_dir, "a011/584a/2c93/78bf/70c6/903e/f5fb/f101/b30b/0893/7441/dc2e/c679/32fb/3620/b2cf")

    def test_store_buffer(self):
        buffer = np.array([0,1,2,3,4,5,6,7,8,9,10])
        signature = bs.put_buffer(buffer)
        assert signature == '2121328acdf4592d1d9250e74871207361b39ce2382e60fc303f79a02e5399e6'
