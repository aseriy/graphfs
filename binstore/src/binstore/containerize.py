import argparse
from binstore import BinaryStore
from neo4j import GraphDatabase
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name
import magic
import json


creds = None

def containerize(creds, node_sha256):
    bs = BinaryStore(creds)

    node = bs.containerize_node(node_sha256)
    meta = bs.get_meta(node.get('sha256'))
    print(json.dumps(meta, indent=2))



if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    args, unknown = parser.parse_known_args()
    creds = get_credentials('etc', 'config.yml')
    print(args, unknown)
    print(creds)

    for sum in unknown:
        containerize(creds, sum)