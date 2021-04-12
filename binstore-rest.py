    # from flask import Flask, request
    # from flask_restful import Resource, Api
from binstore import BinaryStore

bin_store_dir = 'binstore'

    # app = Flask(__name__)
    # api = Api(app)
    #
    # class HelloWorld(Resource):
    #     def get(self):
    #         return {"text": "Hellow World!"}
    #
    #
    # class Blob(Resource):
    #     def __init__(self):
    #         self.bs = BinaryStore(bin_store_dir)
    #
    #     def get(self, sha256):
    #         json_resp = {
    #             "sha256": sha256,
    #             "valid": self.bs.is_valid_hex(sha256)
    #         }
    #         return json_resp
    #
    #
    # api.add_resource(HelloWorld, '/')
    # api.add_resource(Blob, '/<string:sha256>')
    #
    #
    # if __name__ == '__main__':
    #     app.run(host='172.28.128.11', debug=True)
    #


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
