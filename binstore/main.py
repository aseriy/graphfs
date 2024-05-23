from src.apis import apis
# from src.prisma import prisma
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend


app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.include_router(apis, prefix="/apis")

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())


# @app.on_event("shutdown")
# async def shutdown():
#     await prisma.disconnect()


@app.get("/")
def read_root():
    return {"version": "1.0.0"}

