from binstore import BinaryStore
import argparse
import magic
import asyncio
from aiohttp import web
import json

bs = None
favicon_buffer = None


def load_favicon():
    global favicon_buffer
    with open ('./favicon.ico', "rb") as file_fh:
        favicon_buffer = bytearray(file_fh.read())


@asyncio.coroutine
async def hello_world(request):
    print(request)
    json_resp = {"text": "Hello World!"}
    return web.Response(text=json.dumps(json_resp))


@asyncio.coroutine
async def get_favicon(request):
    print(request)
    return web.Response(
        content_type='image/x-icon',
        body=favicon_buffer
    )


@asyncio.coroutine
async def get_file(request):
    print(request)
    sha256 = request.match_info.get('sha256')

    # Check if a valid sha256
    if not bs.is_valid_hex(sha256):
        return web.HTTPNotFound()

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
                web.get('/favicon.ico', get_favicon),
                web.get('/{sha256}', get_file)
            ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument("--binstore", type=str,
                        required=True,
                        # default = conn['bin_store_dir'],
                        help="BinaryStore directory path")
    args, unknown = parser.parse_known_args()
    bs = BinaryStore(args.binstore)
    load_favicon()
    web.run_app(app)
