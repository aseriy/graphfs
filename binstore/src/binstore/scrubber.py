import argparse
import requests
import os
import pathlib
import json
from util.neo4j_helpers import get_credentials


# creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')
# bs = BinaryStore(creds)

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
    print(os.sys.path)
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Scrub the system."
        )

    # # parser.add_argument("-b", "--batch_size", type=int, required=False, default=10,
    # #                     help=""
    # #                 )
    # # parser.add_argument("-s", "--source", type=str, required=True,
    # #                     help="Source path. If Source is a directory, all files under it will be copied."
    # #                 )

    # # args, unknown = parser.parse_known_args()

    # dest_dir = args.dir
    # src_path = args.source
    # print(dest_dir)
    # print(src_path)

    # bs.scrub()

    exit(0)

