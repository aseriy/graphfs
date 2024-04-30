import time
import numpy as np
import json
from pymilvus import (
    connections,
    utility,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility
)
from pymilvus.client.types import ExceptionsMessage, LoadState

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

    if not self.collection.has_index(index_name="graphfs"):
      print(fmt.format("Start Creating index BIN_IVF_FLAT"))
      index = {
          "index_type": "BIN_IVF_FLAT",
          "metric_type": "HAMMING",
          "params": {"nlist": 2896}
      }
      self.collection.create_index("data", index, index_name="graphfs")

    if utility.load_state(collection) == LoadState.NotLoad:
      print(f"Loading collection {collection}...")
      self.collection.load()
      utility.wait_for_loading_complete(collection)

    # Compact small segments
    print(fmt.format(f"Compacting collection {collection}"))
    # self.collection.compact()
    # self.collection.wait_for_compaction_completed()

    # Display collection stats
    print(json.dumps(self.stats(), indent=2))
  
    if self.is_index_in_progress():
      utility.wait_for_index_building_complete(collection)
  
    # print(utility.index_building_progress(collection))
    # print(json.dumps(self.stats(), indent=2))



  def is_index_in_progress(self):
    indexing_in_progress = False

    entities = self.collection.num_entities
    print("Entities: ", entities)

    segments = utility.get_query_segment_info(collection)
    print("Number of Segments: ", len(segments))

    status = utility.index_building_progress(collection)
    print("Indexing Status: ", json.dumps(status, indent=2))
    # pending = status['pending_index_rows']
    # if pending > 0:
    #   indexing_in_progress = True

    return indexing_in_progress



  def stats(self):
    stats = {
      "description": self.collection.describe(),
      "entities": self.collection.num_entities,
      "indexing": utility.index_building_progress(collection)
    }

    # indexes = self.collection.indexes
    # for idx in indexes:
    #   print(idx)

    # partitions = self.collection.partitions
    # for p in partitions:
    #   print(p)

    return stats



  def list(self):
    vector_list = []

    # Create a query iterator
    iterator = self.collection.query_iterator(
        batch_size=1000,
        # limit=5,
        expr="",
        output_fields=["sha256"]
    )
    print(iterator)
    result = iterator.next()
    while result:
      for r in result:
        vector_list.append(r["sha256"])
      result = iterator.next()

    return vector_list


  def add(self, entities):
    result = self.collection.upsert(entities)

    if self.is_index_in_progress():
      self.collection.flush()
      print("Waiting for indexing to complete...")
      utility.wait_for_index_building_complete(collection)

    return result



  def flush(self):
    self.collection.flush()
    # self.collection.compact()



  def delete(self, entities):
    expr = f"sha256 in {json.dumps(entities)}"
    result = self.collection.delete(expr)
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
      # print("SIMILARITY SEARCH: ", s_results)

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

          if len(similar_vector) < 1:
            similar_vector = None

    return similar_vector

        