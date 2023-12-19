import argparse
import json
from binstore import BinaryStore
from util.neo4j_helpers import get_credentials

creds = get_credentials('etc', 'config.yml')
bs = BinaryStore(creds)


def deltalize(c1, c2, file_out):
    meta, buf = bs.deltalize(c1, c2)
    print(json.dumps(meta, indent=2))
    print(buf)
    print(len(buf))


#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Calculate binary delta between two containers"
        )

    parser.add_argument("-i", "--input", type=str, required=True,
                        help="Initial container's SHA256"
                    )
    parser.add_argument("-o", "--output", type=str, required=True,
                        help="Resulting container's SHA256"
                    )
    parser.add_argument("-d", "--delta", type=str, required=False,
                        help="Binary delta output file path"
                    )

    args, unknown = parser.parse_known_args()

    sha256_from = args.input
    sha256_to = args.output
    delta_file = args.delta
    print(sha256_from)
    print(sha256_to)
    print(delta_file)


    deltalize(sha256_from, sha256_to, delta_file)

    exit(0)

