from neo4j import GraphDatabase
from pathlib import PurePath


class FileStore():
  def __init__(self, creds):
      # bin_store_dir = creds['bin_store_dir']
      # self.bin_store_perma_dir = os.path.join(bin_store_dir, store_perma_dir)
      # self.bin_store_cache_dir = os.path.join(bin_store_dir, store_cache_dir)
      self.graph = \
          GraphDatabase.driver("bolt://" + creds['neo4j_url'] + ":7687",
                                  auth=(creds['neo4j_username'],
                                  creds['neo4j_password']))


  def query_make_dir(self, path: PurePath):
    print(path)
    parts = path.parts

    q_lines = [
      "MERGE (r:FileSystem:Root)"
    ]

    path_last_part = 'r'

    for i, d in enumerate(parts, start=0):
       q_lines.append(f"MERGE ({path_last_part})<-[:HARD_LINK]-(d{i}:FileSystem:Directory {{name:\"{d}\"}})")
       path_last_part = f"d{i}"
    
    # q_lines.append("MERGE (r)<-[:HARD_LINK]-(d0)")

    # parts = parts[:-1]
    # for i, d in enumerate(parts, start=0):
    #    q_lines.append(f"MERGE (d{i})<-[:HARD_LINK]-(d{i+1})")

    part_list = ','.join([f"d{i}" for i in range(len(path.parts))])
    # part_list = f"r, {part_list}"

    q = "\n".join(q_lines)
    r = f"RETURN {part_list}"

    return q, r
  

  def make_dir(self, path: PurePath):
    q, r = self.query_make_dir(path)

    with self.graph.session() as s:
      result = s.run("\n".join([q, r]))
      print(result)

    return None


  def query_create_file(self, sha256: str, path: PurePath):
    q, r = self.query_make_dir(path.parent)
    
    n = len(path.parts)-2
    q = f"MATCH (fn:FileNode {{sha256: \"{sha256}\"}})\n" + q
    q += f"\nMERGE (fn)<-[:REFERENCES]-(f:FileSystem:Regular {{name: \"{path.name}\"}})-[:HARD_LINK]->(d{n})"
    r += ",f,fn"

    return q, r



  def create_file(self, sha256: str, path: PurePath):
    file_node = None
    q, r = self.query_create_file(sha256, path)
    print("\n".join([q,r]))
    with self.graph.session() as s:
      result = s.run("\n".join([q, r]))
      file_node = result.single().get('fn').get('sha256')

    return file_node

