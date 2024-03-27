import time
import numpy as np
import json
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)

from util.neo4j_helpers import get_credentials
import os

creds = get_credentials(os.path.join(os.path.dirname(__file__), '../../../etc'), 'config.yml')
fmt = "\n=== {:30} ===\n"
collection = 'binstore'
similarity_threshold = 512


class VectorStore():
  def __init__(self, creds):
    print(fmt.format("start connecting to Milvus"))
    connections.connect("default", host=creds['milvus_url'], port="19530")

    fields = [
        FieldSchema(name="sha256", dtype=DataType.VARCHAR, is_primary=True, auto_id=False, max_length=64),
        FieldSchema(name="data", dtype=DataType.BINARY_VECTOR, dim=1024*8)
    ]

    schema = CollectionSchema(fields, "Binstore")

    print(fmt.format(f"Create collection {collection}"))
    self.collection = Collection(collection, schema, consistency_level="Strong")

    print(fmt.format("Start Creating index BIN_IVF_FLAT"))
    index = {
        "index_type": "BIN_IVF_FLAT",
        "metric_type": "HAMMING",
        "params": {"nlist": 128}
    }

    self.collection.create_index("data", index)


  def insert(self, entities):
    result = self.collection.insert(entities)
    self.collection.flush()
    return result


  def find_similar(self, sha256):
    similar_vector = None

    # Find the data identified by the sha256
    q_result = self.collection.query(
      expr = f"sha256 == '{sha256}'",
      output_fields = ["sha256", "data"]
    )

    # print(q_result, len(q_result))

    if len(q_result) > 0:
      vector_to_search = q_result[0]['data']

      s_results = self.collection.search(
        data = vector_to_search,
        anns_field = "data",
        param = {
          "metric_type": "HAMMING"
        },
        limit=1000
      )
      print("SIMILARITY SEARCH: ", s_results)

      if len(s_results) > 0:
        print(s_results[0].ids)
        print(s_results[0].distances)
        if len(s_results[0].ids) > 1:
          similar_vector = []
          # Skip the first element as it is the one we're processing here
          s_results[0].ids.pop(0)
          s_results[0].distances.pop(0)
          for (sha256, dist) in zip(s_results[0].ids, s_results[0].distances):
            if dist < similarity_threshold:
              similar_vector.append({
                'sha256':   sha256,
                'distance': dist
              })
              
          # print(json.dumps(similar_vector, indent=2))

    return similar_vector

        