import argparse
from binstore import BinaryStore
from neo4j import GraphDatabase
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name
import magic


creds = None

def file_put(conn, bin_store_dir, file_to_store):
    bs = BinaryStore(conn, bin_store_dir)
    signature = bs.put_file(file_to_store)
    print (file_to_store, signature)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--binstore", type=str,
                        required=True,
                        # default = conn['bin_store_dir'],
                        help="BinaryStore directory path")


    args, files_to_store = parser.parse_known_args()

    creds = get_credentials('etc', 'config.yml')

    m = magic.Magic(mime=True)
    for f in files_to_store:
        print (m.from_file(f))
        file_put(conn, args.binstore, f)
