import argparse
import requests
import os
import pathlib
import json
from util.neo4j_helpers import get_credentials


creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')
BASEURL = "http://{}:{}/apis/filestore".format(creds['graphfs_host'], creds['graphfs_port'])



def upload_dir(dest, dir_path):
    dir_prefix = os.path.dirname(dir_path)
    dir_name = os.path.basename(dir_path)

    src_dirs = list(set(
        [str(src) for src in
            list(pathlib.Path(dir_path).rglob("*"))
            if os.path.isdir(src)
        ]
    ))

    src_files = [str(src) for src in
        list(pathlib.Path(dir_path).rglob("*"))
        if os.path.isfile(src)
    ]

    src_dirs.sort()
    for d in src_dirs:
        dest_dir = os.path.join(
            dest,
            pathlib.PurePath(d).relative_to(dir_prefix)
        )
        print(dest_dir)
        create_directory(dest_dir)


    src_files.sort()
    for f in src_files:
        dest_dir = os.path.join(
            dest,
            os.path.dirname(pathlib.PurePath(f).relative_to(dir_prefix))
        )
        dest_file = f
        print("Copy file: ", dest_file)
        print("To dir:    ", dest_file)
        upload_file(dest_dir, dest_file)



def create_directory(path):
    url = f"{BASEURL}/{path}"
    print("url: ", url)
    r = requests.post(url)
    print(r)


def upload_file(dest, source):
    file_name = os.path.basename(source)

    url = BASEURL
    if dest is not None:
        url = f"{BASEURL}/{dest}"

    print("url: ", url)
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

