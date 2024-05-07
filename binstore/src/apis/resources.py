from util.neo4j_helpers import get_credentials
from graphfs.filestore import FileStore
from graphfs.graphstore import GraphStore


creds = get_credentials('../etc', 'config.yml')
graphStore = GraphStore(creds)
fileStore = FileStore(creds)
