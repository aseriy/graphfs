    # from flask import Flask, request
    # from flask_restful import Resource, Api
from binstore import BinaryStore

bin_store_dir = 'binstore'

from aiohttp import web
import json

bs = BinaryStore(bin_store_dir)

async def hello_world(request):
    json_resp = {"text": "Hello World!"}
    return web.Response(text=json.dumps(json_resp))


async def get_image(request):
    sha256 = request.match_info.get('sha256')
    img_path = bs.get(sha256)
    img_data = None
    with open (img_path, "rb") as img_fh:
        img_data = bytearray(img_fh.read())
    return web.Response(
        content_type="image/jpeg",
        body=img_data
    )


app = web.Application()
app.add_routes([web.get('/', hello_world),
                web.get('/{sha256}', get_image)])


if __name__ == '__main__':
    web.run_app(app)
