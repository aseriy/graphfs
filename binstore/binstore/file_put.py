from binstore import BinaryStore
import argparse
import magic


def file_put(bin_store_dir, file_to_store):
    bs = BinaryStore(bin_store_dir)
    signature = bs.put_file(file_to_store)
    print (file_to_store, signature)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--binstore", type=str,
                        required=True,
                        # default = conn['bin_store_dir'],
                        help="BinaryStore directory path")


    args, files_to_store = parser.parse_known_args()
    m = magic.Magic(mime=True)
    for f in files_to_store:
        print (m.from_file(f))
        file_put(args.binstore, f)
