import argparse
import json
import os
from graphfs.graphstore import GraphStore
from util.neo4j_helpers import get_credentials



#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Find and memorialize FileNodes similarities."
        )

    parser.add_argument("-b", "--batch_size", type=int, required=False, default=1000,
                        help="Number of nodes to process in one batch. Default: 100"
                    )
    parser.add_argument("-n", "--batch_num", type=int, required=False, default=0,
                        help="Number of batches to run. Default: 0 - process all nodes."
                    )

    args, unknown = parser.parse_known_args()

    batch_size = args.batch_size
    batch_num = args.batch_num
    until_done = False if (batch_num > 0) else True
    print("Batch size: ", batch_size)
    print("Number of batches: ", batch_num)
    print("Until done: ", until_done)

    creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')
    bs = GraphStore(creds)

    nodes_done = batch_size
    
    if until_done:
        while nodes_done > 0:
            nodes_done = bs.housekeep_filenode_similarity(batch_size)

    else:
        while nodes_done > 0 and batch_num > 0:
            nodes_done = bs.housekeep_filenode_similarity(batch_size)
            batch_num -= 1

    exit(0)

