import pytest
from binstore import BinaryStore
import os
import numpy as np
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name
from itertools import combinations



creds = get_credentials('etc', 'config.yml')

# file_to_store = os.path.expanduser('~/Download/jdk-8u231-linux-x64.tar.gz')
test_blobs_dir = 'testdata'
bs = BinaryStore(creds)



class TestBinaryStore:
    @pytest.fixture(scope="class")
    def load_graph(self, wipe_out):
        for f in sorted(os.listdir(test_blobs_dir)):
            sum = bs.put_file(os.path.join(test_blobs_dir,f))
            print(sum, os.path.basename(f))


    @pytest.fixture(scope="class")
    def wipe_out(self):
        print(bs.wipe_out())


    def test_valid_hex(self):
        assert bs.is_valid_hex('0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef')

    def test_invalid_hex(self):
        assert not bs.is_valid_hex('asdfghjklqwertyuasdfghjklqwertyuasdfghjklqwertyuasdfghjklqwertyu')


    def test_store_buffer(self):
        buffer = np.array([0,1,2,3,4,5,6,7,8,9,10])
        signature = bs.put_file_node(buffer)
        assert \
            signature == '2121328acdf4592d1d9250e74871207361b39ce2382e60fc303f79a02e5399e6' and \
            1 == len(bs.list_file_nodes().get('nodes'))


    def test_put_file(self):
        file_to_store = os.path.join(test_blobs_dir, '000000')
        sum = bs.put_file(file_to_store)
        assert '962cf3c071da5682136d2dfa17a9f3421c8df620e0591e43e4a338d09c59b28e' == sum


    def test_list_file_nodes(self, wipe_out, load_graph):
        json_resp = bs.list_file_nodes()
        assert 126 == len(json_resp['nodes'])

    def test_real_file_signature(self, load_graph):
        signature = bs.put_file(file_to_store)
        print(signature)
        assert bs.is_valid_hex(signature)

    def test_get(self, load_graph):
        file_meta = bs.get(bs.put_file(file_to_store))
        assert file_meta['store'] \
            == "a011/584a/2c93/78bf/70c6/903e/f5fb/f101/b30b/0893/7441/dc2e/c679/32fb/3620/b2cf"

    def test_get_meta(self, load_graph):
        print (bs.get_meta('a99419c2f09c1a47cb053bb927756f9c27e3889be5b6c9e559f0f3606c9d2623'))


    def test_containerize_node_1(self, load_graph):
        # testdata/blobs/000072 (11K)
        node_sha256 = 'fac71a62bc0d85bd5d11c2ad6137a12d5bdc326eda227f64d5092a4a05f5186b'
        node = bs.containerize_node(node_sha256)
        actual = bs.get_meta(node.get('sha256')).get('containers')
        assert 11 == actual



    def test_containerize_node_2(self, load_graph):
        # testdata/blobs/000000 (58K)
        node_sha256 = 'c9ef76eef21fcd1531f5800e7646e15053b12cb152403472b7d44a073a0eaec7'
        node = bs.containerize_node(node_sha256)
        actual = bs.get_meta(node.get('sha256')).get('containers')
        assert 58 == actual


    def test_containerize_node_3(self, load_graph):
        # testdata/blobs/000002 (414K)
        node_sha256 = 'a99419c2f09c1a47cb053bb927756f9c27e3889be5b6c9e559f0f3606c9d2623'
        node = bs.containerize_node(node_sha256)
        actual = bs.get_meta(node.get('sha256')).get('containers')
        assert 414 == actual


    def test_cache_file_node(self, load_graph):
        node_sha256 = 'fac71a62bc0d85bd5d11c2ad6137a12d5bdc326eda227f64d5092a4a05f5186b'
        node = bs.containerize_node(node_sha256)
        node = bs.cache_file_node(node_sha256)
        print(bs.hex_to_path(node_sha256))


    def test_housekeep_containerize_dry(self, load_graph):
        assert 126 == len(bs.housekeep_containerize())

    def test_housekeep_containerize_1(self, load_graph):
        assert 1 == len(bs.housekeep_containerize(1))

    def test_housekeep_containerize_all(self, load_graph):
        bs.housekeep_containerize(-1)



    # def test_qualify_container_delta(self):
    #     c_list = (
    #         "a304aa8bba0aa9fccb6c82568e07c101d533faf2ec5c525a9403dbb9d912e0a0",
    #         "9af169284e5191928423c1f23946f3512238b205c670d886fa64a622b06671d7",
    #         "2246016971b057f0f587d220e9be6c2d013bdeb7f28f86d93b1dd95adf48188f",
    #         "6ec87382dd072f44850c3084b4228e6529cd361f8363e30004a7a66f6fd014c3",
    #         "29b85d66a3fa084ff08722a0ee78c41bcdfb99b996cecb6bd547b2dd0a45f924",
    #         "7253f30a018deb7c81ff098d239ccd05cdcab0759cef102b8a9e3a0a64441418"
    #     )
    #     for c in combinations(c_list, 2):
    #         print(c[0], c[1])
    #         bs.qualify_container_delta(c[0], c[1])



    # def test_qualify_container_delta_1(self):
    #     c1 = "d2750f3dc96e337e58951205471f27c417825d6ef8986baf4970028fc06ce5d3"
    #     c2 = "a6b25afc4a25595bc8fda2307896dee9f8dc7523d28b607d2b949195418a21f2"
    #     print(bs.qualify_container_delta(c1, c2))




    # def test_deltalize_container(self):
    #     print(bs.deltalize_container("ada0280da9ffaf9da0212cb56411677bc9bb8469e8305fcd76525e4a4b779624"))



    # def test_housekeep_deltalize_dry(self):
    #     print(bs.housekeep_deltalize())


    # def test_housekeep_deltalize_one(self):
    #     print(bs.housekeep_deltalize(1))


    # def test_housekeep_deltalize_ten(self):
    #     print(bs.housekeep_deltalize(10))


    # TODO: Test of containers of zero bytes or very few bytes that may result in 
    # the ratio where division by zero may need to be handled.
