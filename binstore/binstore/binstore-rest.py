from binstore import BinaryStore
import argparse
import magic
from aiohttp import web
import json

bs = None

async def hello_world(request):
    json_resp = {"text": "Hello World!"}
    return web.Response(text=json.dumps(json_resp))


async def get_file(request):
    sha256 = request.match_info.get('sha256')
    file_path = bs.get(sha256)
    file_data = None
    with open (file_path, "rb") as file_fh:
        file_data = bytearray(file_fh.read())

    m = magic.Magic(mime=True)
    mp = m.from_file(file_path)
    return web.Response(
        content_type=mp,
        body=file_data
    )


app = web.Application()
app.add_routes([web.get('/', hello_world),
                web.get('/{sha256}', get_file)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--binstore", type=str,
                        required=True,
                        # default = conn['bin_store_dir'],
                        help="BinaryStore directory path")
    args, unknown = parser.parse_known_args()
    bs = BinaryStore(args.binstore)

    web.run_app(app)
