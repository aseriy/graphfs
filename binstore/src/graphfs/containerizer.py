import argparse
import requests
import os
import pathlib
import json
from util.neo4j_helpers import get_credentials
from graphfs.graphstore import GraphStore

# SCRUBBER
# At the moment, there is one scrubbing task.
# When a FileNode is created, a new Container is created and holds the entire content of the FileNode.
# Shortly after that, if the Container size exceed the standard chunk size, another process will chunk up
# this container, creating 2 or more Containers that are attached to the FileNode in the correct order.
# The original Container is detached from the FileNode and thus becomes orphan.
# We don't want to remove this Container right away in case we need to re-assemble it. In the future,
# there will be a retention time property in the Container that will determine how long to keep it around
# after it's accessed last. After the retention time is up, the Container needs to be deleted (graph node
# plus the cached content file).
# This utility (for now) simply looks for the Containers that exceed the chunk size and aren't attached
# to any FileNodes, and deletes it.



#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Containerize FileNodes"
        )

    parser.add_argument("-b", "--batch_size", type=int, required=False, default=1000,
                        help="Number of nodes to containerize in one batch. Default: 1000"
                    )
    parser.add_argument("-n", "--batch_num", type=int, required=False, default=0,
                        help="Number of batches to run. Default: 0 - containerize all nodes."
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
            nodes_done = bs.housekeep_containerize(batch_size)

    else:
        while nodes_done > 0 and batch_num > 0:
            nodes_done = bs.housekeep_containerize(batch_size)
            batch_num -= 1

    exit(0)

