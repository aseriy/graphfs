import argparse
from binstore import BinaryStore
from neo4j import GraphDatabase
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name


creds = None

def deltalize(creds, batchsize):
    bs = BinaryStore(creds)

    x = -1
    if batchsize > 0:
        x = batchsize
    else:
        x = -1

    print(bs.housekeep_deltalize(x))



if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--batchsize", type=int,
                        required=False,
                        default = 0,
                        help="Number of containers to deltalize.")

    args, unknown = parser.parse_known_args()

    creds = get_credentials('etc', 'config.yml')
    print(args.batchsize)

    deltalize(creds, args.batchsize)
