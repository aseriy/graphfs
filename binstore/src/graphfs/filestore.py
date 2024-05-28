from neo4j import GraphDatabase
from pathlib import PurePath
import datetime
import json
import os
from graphfs.graphstore import GraphStore
import concurrent.futures


class FileStore():
  def __init__(self, creds):
      self.graph = \
          GraphDatabase.driver("bolt://" + creds['neo4j_url'] + ":7687",
                                  auth=(creds['neo4j_username'],
                                  creds['neo4j_password']))

      self.binstore = GraphStore(creds)
      


  def __del__(self):
      self.graph.close()



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



  def create_file(self, sha256: str, path: PurePath) -> str:
    file_node = None

    q, r = self.query_create_file(sha256, path)
    print("\n".join([q,r]))
    with self.graph.session() as s:
      result = s.run("\n".join([q, r]))
      file_node = result.single().get('fn').get('sha256')
      print(file_node)

    return file_node



    def delete_file(self, path: PurePath) -> None:
      

      return None



  def query_list_file(self, node_id: str):
    q = f"MATCH (f:Regular)-[r:REFERENCES]->(fn:FileNode) WHERE elementId(f)='{node_id}' RETURN f,r,fn"
    print("Cypher: ", q)

    listing = None
    f, r, fn = None, None, None

    with self.graph.session() as s:
      result = s.run(q)
      f_r_fn = result.single()
      f = f_r_fn.get('f')
      r = f_r_fn.get('r')
      fn = f_r_fn.get('fn')

    listing = {
      'path': None,
      'directory': None,
      'type': 'File',
      'basename': f.get('name'),
      'size': fn.get('size'),
      'time': str(fn.get('ctime')),
      'mime': fn.get('mime'),
      'sha256': fn.get('sha256')
    }

    return listing



  def list_identical_files(self, path: str):
    identical_files = []

    file_path = self.find_path(path)
    print(json.dumps(file_path, indent=2))
    file_id = file_path['path'][-1]

    q = f"""
            MATCH (f:Regular)-[:REFERENCES]->(fn:FileNode)<-[:REFERENCES]-(t:Regular)
            WHERE elementId(f)="{file_id}" AND f<>t
            WITH COLLECT(t) AS twins UNWIND twins as t
            MATCH p=shortestPath((r:Root)-[:HARD_LINK*]-(t))
            RETURN [n in nodes(p) | n.name] AS path ORDER BY path
        """

    print("Cypher: ", q)

    with self.graph.session() as s:
      result = s.run(q)
      for r in result:
        p = r.get('path')
        p.pop(0)
        identical_files.append(str(PurePath('/').joinpath(*p)))

      s.close()

      print(json.dumps(identical_files, indent=2))

    return identical_files



  def list_similar_files(self, path: str):
    similar_files = {}

    file_path = self.find_path(path)
    print(json.dumps(file_path, indent=2))
    file_id = file_path['path'][-1]

    q = f"""
        MATCH (f:Regular)-[:REFERENCES]->(fn:FileNode)
        WHERE elementId(f)="{file_id}"
        RETURN fn.sha256 AS fn
        """

    print("Cypher: ", q)

    with self.graph.session() as s:
      result = s.run(q)
      r = result.single()
      fn_sha256 = r.get('fn')
      s.close()

    similar_fns = self.binstore.find_similar_filenodes(fn_sha256)

    if len(similar_fns):
      q = f"""
          MATCH (f:Regular)-[:REFERENCES]->(fn:FileNode)
          WHERE fn.sha256 IN {similar_fns}
          WITH f, fn
          MATCH p=shortestPath((r:Root)-[:HARD_LINK*]-(f:Regular))
          RETURN fn.sha256 AS fn, [n in nodes(p) | n.name] AS path ORDER BY fn.sha256
          """

      print("Cypher: ", q)

      with self.graph.session() as s:
        result = s.run(q)
        for r in result:
          fn = r.get('fn')
          p = r.get('path')
          p.pop(0)
          
          if not fn in similar_files:
            similar_files[fn] = []
          
          similar_files[fn].append(str(PurePath('/').joinpath(*p)))

        s.close()

    print(json.dumps(similar_files, indent=2))

    return similar_files



  def query_list_directory(self, node_id: str):
    q = f"""MATCH (d) WHERE elementId(d)='{node_id}'
            OPTIONAL MATCH (d)<-[:HARD_LINK]-(f:FileSystem)
            OPTIONAL MATCH (p:FileSystem)<-[:HARD_LINK]-(d)
            RETURN p, d, collect(f) as children"""
    
    print("Cypher: ", q)

    listing = None
    parent, directory, children = None, None, None

    with self.graph.session() as s:
      result = s.run(q)
      p_d_ch = result.single()
      parent = p_d_ch.get('p')
      directory = p_d_ch.get('d')
      children = p_d_ch.get('children')
      s.close()


    listing = {
      "path": None,
      "directory": None,
      "type": "Directory",
      "basename": directory.get('name'),
      "size": 0
    }


    if len(children):
      listing['children'] = []

      just_file_children = []
      just_files = []

      # First let's grab just the directories
      for child in children:
        if 'Directory' in child.labels:
          listing['children'].append({
              "type": "Directory",
              "basename": child.get('name')
            }
          )
        
        else:
          just_file_children.append(child.element_id)


      cpu_cores = int(0.5 + 0.5 * os.cpu_count())
      print(f"Using {cpu_cores} threads...")

      with concurrent.futures.ThreadPoolExecutor(max_workers=cpu_cores) as executor:
        just_files = executor.map(self.query_list_file, just_file_children)
        executor.shutdown(wait=True)

      listing['children'].extend(list(just_files))

      # Sort children by name
      listing['children'] = sorted(listing['children'], key=lambda c: c['basename'])

      listing['size'] = len(children)


    return listing


  def find_path(self, path: PurePath):
    print("find_path: ", path)
    found_path = {
      "isDir": False
    }

    path_nodes = []
    path_match= [
      '(:Root)'
    ]
    path_return = []


    for i, p in enumerate(path.parts, start=1):
      node = None
      if len(path.parts) == i:
        node = 'f'
      else:
        node = f"d{i}"

      path_nodes.append(node)
      path_match.append(f"({node}:FileSystem {{name: \"{p}\"}})")
      path_return.append(f"elementId({node}) AS {node}")
    
    q = f"""MATCH {'<-[:HARD_LINK]-'.join(path_match)}
            RETURN {', '.join(path_return)},
            labels({path_nodes[-1]}) AS labels"""
    print("Cypher: ", q)
  
    with self.graph.session() as s:
      result = s.run(q)
      single = result.single()
      if 'Directory' in single.get('labels'):
        found_path['isDir'] = True

      found_path['path'] = []
      for p in path_nodes:
        found_path['path'].append(single.get(p))

      s.close()

    return found_path


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
      print("Cypher: ", q)
    
      with self.graph.session() as s:
        result = s.run(q)
        path_node = result.single()
        path_id = path_node.get('id')
        if 'Directory' in path_node.get('labels'):
          is_dir = True
        
    else:     # Root
      q = "MATCH (r:Root) RETURN elementId(r) as id"
      print("Cypher: ", q)

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

    if path is None:
      listing['path'] = '/'
      listing['directory'] = None
    else:
      listing['path'] = PurePath('/', path)
      listing['directory'] = listing['path'].parent
    
    return listing

  

  def list(self, path: PurePath = None):
    listing = self.query_list(path)
    return listing


