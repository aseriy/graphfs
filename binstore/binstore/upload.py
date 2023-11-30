import argparse
import requests
import os
import pathlib
import json

BASEURL = 'http://localhost:8000/apis/filetree'



def upload_dir(dest, dir_path):
    SKIP_DIRS = ['.git']

    sources = ['/'.join(src.parts) for src in
        list(
            filter (
                lambda item: set(item.parts).isdisjoint(SKIP_DIRS),
                pathlib.Path(dir_path).rglob("*")
            )
        ) if src.is_file()
    ]
    # print(json.dumps(sources, indent=2))

    for f in sources:
        upload_file(dest, f)



def upload_file(dest, source):
    url = f"{BASEURL}/{dest}/{os.path.dirname(source)}"
    file_name = os.path.basename(source)
    print(file_name)
    with open(source, 'rb') as f:
        print(f)
        r = requests.post(url, files={'file': f})
        print(r)


#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Copy local files to the Binstore"
        )

    parser.add_argument("-d", "--dir", type=str, required=False,
                        help="Destination directory. Default: root"
                    )
    parser.add_argument("-s", "--source", type=str, required=True,
                        help="Source path. If Source is a directory, all files under it will be copied."
                    )

    args, unknown = parser.parse_known_args()

    dest_dir = args.dir
    src_path = args.source
    print(dest_dir)
    print(src_path)

    if os.path.isdir(src_path):
        upload_dir(dest_dir, src_path)

    if os.path.isfile(src_path):
        upload_file(dest_dir, src_path)

    exit(0)

