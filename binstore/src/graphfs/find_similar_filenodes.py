import argparse
import json
import os
from graphfs.graphstore import GraphStore
from graphfs.filestore import FileStore
from util.neo4j_helpers import get_credentials
from pathlib import PurePath


#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = os.path.basename(__file__),
            description = "Find FileNode(s) similar to the one specified."
        )

    input_param = parser.add_mutually_exclusive_group(required=True)

    input_param.add_argument("-s", "--sha256", type=str,
                             help="FileNode sha256"
                            )
    input_param.add_argument("-p", "--path", type=str,
                            help="File path"
                            )

    args, unknown = parser.parse_known_args()

    fn_sha256 = args.sha256
    print(f"FileNode: {fn_sha256}")
    f_path = args.path
    print(f"Path: {f_path}")

    creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')

    if f_path is not None:
        fs = FileStore(creds)
        fn_sha256 = fs.list_similar_files(f_path)

    else:
        bs = GraphStore(creds)
        bs.find_similar_filenodes(fn_sha256)


    exit(0)

