from binstore import BinaryStore
import argparse, sys, os
import magic
from aiohttp import web
import json
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name


bs = None
favicon_buffer = None


def load_favicon():
    global favicon_buffer
    with open (os.path.join(os.path.dirname(sys.argv[0]), './favicon.ico'), "rb") as file_fh:
        favicon_buffer = bytearray(file_fh.read())


async def hello_world(request):
    print(request)
    json_resp = {"text": "Hello World!"}
    return web.Response(text=json.dumps(json_resp))


async def get_favicon(request):
    print(request)
    return web.Response(
        content_type='image/x-icon',
        body=favicon_buffer
    )


async def get_node_list(request):
    print(request)
    json_resp = bs.list_file_nodes()
    return web.Response(text=json.dumps(json_resp, indent=2))


async def get_node_meta(request):
    print(request)
    sha256 = request.match_info.get('sha256')
    json_resp = bs.get_meta(sha256)
    return web.Response(text=json.dumps(json_resp, indent=2))



async def get_file_node(request):
    print(request)

    sha256 = request.match_info.get('sha256')

    # Check if a valid sha256
    if not bs.is_valid_hex(sha256):
        return web.HTTPNotFound()

    file_data = None
    node_mime, node_cache_path = bs.get(sha256)
    with open (node_data_path, "rb") as file_fh:
        file_data = bytearray(file_fh.read())

    return web.Response(
        content_type=node_mime,
        body=file_data
    )


app = web.Application()
app.add_routes([web.get('/', hello_world),
                web.get('/favicon.ico', get_favicon),
                web.get('/nodes', get_node_list),
                web.get('/nodes/{sha256}/meta', get_node_meta),
                web.get('/nodes/{sha256}', get_file_node)
            ])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    # parser.add_argument("--binstore", type=str,
    #                     required=False,
    #                     # default = conn['bin_store_dir'],
    #                     help="BinaryStore directory path")
    args, unknown = parser.parse_known_args()
    creds = get_credentials('etc', 'config.yml')
    print(args, unknown)
    print(creds)

    bs = BinaryStore(creds)
    load_favicon()
    web.run_app(app)
