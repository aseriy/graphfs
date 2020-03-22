from binstore import BinaryStore
import click
import numpy as np


@click.command()
@click.argument('bin_store_dir')
@click.argument('file_to_store')
def main(bin_store_dir, file_to_store):
    bs = BinaryStore(bin_store_dir)
    signature = bs.put_file(file_to_store)
    print (file_to_store, signature)
    print(bs.get(signature))
    buffer = np.array([0,1,2,3,4,5,6,7,8,9,10])
    signature = bs.put_buffer(buffer)
    print (signature)


if __name__ == "__main__":
    main()
