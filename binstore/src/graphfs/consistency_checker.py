import argparse
import requests
import os
import pathlib
import json
from util.neo4j_helpers import get_credentials
from graphfs.graphstore import GraphStore

# CONSISTENCY CHECKER
# From time to time, it is necessary to verify that all standard size containers
# in the graph have the vector counterparts in the vector DB.



#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Consistency checker"
        )

    # parser.add_argument("-b", "--batch_size", type=int, required=False, default=10,
    #                     help=""
    #                 )
    # parser.add_argument("-s", "--source", type=bool, required=false,
    #                     help="Source path. If Source is a directory, all files under it will be copied."
    #                 )

    args, unknown = parser.parse_known_args()

    # dest_dir = args.dir
    # src_path = args.source
    # print(dest_dir)
    # print(src_path)

    creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')
    bs = GraphStore(creds)

    containers = bs.list_vectors()
    print(json.dumps(containers, indent=2))

    container_nodes = [sha256 for sha256 in containers.keys() if 'graph' in containers[sha256]]
    print("GRAPH:  ", len(container_nodes))    
    vector_keys = [sha256 for sha256 in containers.keys() if 'vector' in containers[sha256]]
    print("VECTOR: ", len(vector_keys))

    graph_only = [sha256 for sha256 in containers.keys() \
                    if 'graph' in containers[sha256] and \
                        not 'vector' in containers[sha256] \
                ]
    vector_only = [sha256 for sha256 in containers.keys() \
                    if not 'graph' in containers[sha256] and \
                        'vector' in containers[sha256] \
                ]
    print("GRAPH ONLY:   ", json.dumps(graph_only, indent=2)) 
    print("VECTOR ONLY:  ", json.dumps(vector_only, indent=2))    

    if len(vector_only):
        bs.delete_vectors(vector_only)

    exit(0)

