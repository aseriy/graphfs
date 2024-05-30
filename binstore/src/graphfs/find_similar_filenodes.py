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
            description = "Find FileNode(s) similar to the one specified."
        )

    parser.add_argument("-s", "--sha256", type=str, required=True,
                        help="SHA256 of a FileNode"
                    )

    args, unknown = parser.parse_known_args()

    fn_sha256 = args.sha256
    print(f"FileNode: {fn_sha256}")

    creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')
    bs = GraphStore(creds)

    bs.find_similar_filenodes(fn_sha256)

    exit(0)

