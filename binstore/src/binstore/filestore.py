from neo4j import GraphDatabase
from pathlib import PurePath
import datetime


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
    print("query_make_dir: path: ", path)
    print("query_make_dir: path.parts: ", path.parts)
    parts = path.parts

    q_lines = [
      "MERGE (d0:FileSystem:Root)"
    ]

    path_last_part = 'd0'
    part_list = [path_last_part]


    for i, d in enumerate(parts, start=1):
       q_lines.append(f"MERGE ({path_last_part})<-[:HARD_LINK]-(d{i}:FileSystem:Directory {{name:\"{d}\"}})")
       path_last_part = f"d{i}"
       part_list.append(path_last_part)
    
    q = "\n".join(q_lines)
    r = f"RETURN {','.join(part_list)}"

    return q, r
  

  def make_dir(self, path: PurePath):
    q, r = self.query_make_dir(path)

    with self.graph.session() as s:
      result = s.run("\n".join([q, r]))
      print(result)

    return None


  def query_create_file(self, sha256: str, path: PurePath):
    q, r = self.query_make_dir(path.parent)
    print("q: ", q)
    print("r: ", r)
    
    print("parts: ", path.parts, len(path.parts))
    n = len(path.parts)-1
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


  def query_list_file(self, node_id: str):
    q = f"MATCH (f:Regular)-[r:REFERENCES]->(fn:FileNode) WHERE elementId(f)='{node_id}' RETURN f,r,fn"

    listing = None
    f, r, fn = None, None, None

    with self.graph.session() as s:
      result = s.run(q)
      f_r_fn = result.single()
      f = f_r_fn.get('f')
      r = f_r_fn.get('r')
      fn = f_r_fn.get('fn')

    listing = {
      'type': 'File',
      'name': f.get('name'),
      'size': fn.get('size'),
      'time': str(fn.get('ctime')),
      'mime': fn.get('mime'),
      'sha256': fn.get('sha256')
    }

    return listing



  def query_list_directory(self, node_id: str):
    q = f"""MATCH (d) WHERE elementId(d)='{node_id}'
            OPTIONAL MATCH (d)<-[:HARD_LINK]-(f:FileSystem)
            OPTIONAL MATCH (p:FileSystem)<-[:HARD_LINK]-(d)
            RETURN p, d, collect(f) as children"""
    
    print("Query: ", q)

    listing = None
    parent, directory, children = None, None, None

    with self.graph.session() as s:
      result = s.run(q)
      p_d_ch = result.single()
      parent = p_d_ch.get('p')
      directory = p_d_ch.get('d')
      children = p_d_ch.get('children')

    listing = {}

    print("Parent: ", parent)           
    if parent is not None:
      listing['parent'] = parent.get('name')
    else:
      listing['parent'] = '/'


    listing['name'] = directory.get('name')
    listing['size'] = 2


    if len(children):
      listing['children'] = []
      for child in children:
        if 'Directory' in child.labels:
          listing['children'].append(self.query_list_directory(child.element_id))

        else:
          listing['children'].append(self.query_list_file(child.element_id))

      listing['size'] += len(children)


    return listing



  def query_list(self, path: PurePath = None):
    is_dir = False
    path_id = None

    if path is not None:
      path_list = [
        '(:Root)'
      ]

      for i, p in enumerate(path.parts, start=1):
        leaf = 'f' if len(path.parts) == i else ''
        path_list.append(f"({leaf}:FileSystem {{name: \"{p}\"}})")
      
      q = f"MATCH {'<-[:HARD_LINK]-'.join(path_list)} RETURN elementId(f) as id, labels(f) AS labels"
      print("Query: ", q)
    
      with self.graph.session() as s:
        result = s.run(q)
        path_node = result.single()
        path_id = path_node.get('id')
        if 'Directory' in path_node.get('labels'):
          is_dir = True
        
    else:     # Root
      q = "MATCH (r:Root) RETURN elementId(r) as id"
      print("Query: ", q)

      with self.graph.session() as s:
        result = s.run(q)
        path_node = result.single()
        path_id = path_node.get('id')
        is_dir = True



    print("path_id: ", path_id)
    print("is_dir: ", is_dir)
    listing = None

    if is_dir:
      listing = self.query_list_directory(path_id)

    else:
      listing = self.query_list_file(path_id)

    
    return listing

  

  def list(self, path: PurePath = None):
    listing = self.query_list(path)
    return listing
