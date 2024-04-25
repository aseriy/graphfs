import sys
import os
import shutil
import json
import dumper
dumper.max_depth = 10
import hashlib
import re
import magic
from neo4j import GraphDatabase
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name
import detools
import io
from graphfs.vectorstore import VectorStore


store_perma_dir = 'perma'
store_cache_dir = 'cache'

# This is temporarily here, should be moved to a config file at some point
# store container size set to 1k
container_size = 1024
container_chunking_batch_size = 1024
DEFAULT_BATCH_SIZE = 5000


class GraphStore():
    def __init__(self, creds):
        self.validator = re.compile('[0-9a-f]+')
        bin_store_dir = creds['bin_store_dir']
        self.bin_store_perma_dir = os.path.join(bin_store_dir, store_perma_dir)
        self.bin_store_cache_dir = os.path.join(bin_store_dir, store_cache_dir)
        self.graph = \
            GraphDatabase.driver(
                "bolt://" + creds['neo4j_url'] + ":7687",
                auth=(creds['neo4j_username'], creds['neo4j_password']),
                max_connection_lifetime = 60 * 5,
                liveness_check_timeout = 60.0,
                max_connection_pool_size = 60
            )
        print("DRIVER: ", self.graph._pool.pool_config)
        
        self.vs = VectorStore(creds)



    def __del__(self):
        self.graph.close()



    def is_valid_hex(self, sum):
        retval = True

        if len(sum) == 64:
            m = self.validator.match(sum)
            s,l =  m.span()
            if not (s == 0 and l == 64):
                retval = False
        else:
            retval = False

        return retval


    def hex_to_path(self, sum):
        chunks, chunk_size = len(sum), 4
        store_path_list = [sum[i:i+chunk_size] for i in range(0, chunks, chunk_size)]
        store_path = os.path.join(*store_path_list)
        return store_path


    # def path_to_hex(self, path):
    #     return ('').join(path.split('binstore')[1].split('/')[1:])


    # THIS IS DANGEROUS!!!
    # WIPES OUT THE ENTIRE GRAPH
    # USE WITH EXTREME CAUTION
    def wipe_out(self, delete_batch_size = DEFAULT_BATCH_SIZE):
        total_deleted = 0
        delete_count = delete_batch_size

        while delete_count > 0:
            with self.graph.session() as s:
                q = '''
                    MATCH (n) WITH n LIMIT $delete_batch_size DETACH DELETE n RETURN COUNT(*) AS delete_count
                    '''

                print(q)

                result = s.run(q, delete_batch_size = delete_batch_size)
                result = [r for r in result]
                delete_count = result[0].get("delete_count")
                print(delete_count)
                total_deleted += delete_count
                s.close()


        return total_deleted


    def is_filenode(self, sha256):
        valid = False

        with self.graph.session() as s:
            q = f'''
                MATCH (fn:FileNode {{sha256: "{sha256}"}})
                RETURN fn
                '''
                
            result = s.run(q)
            if result.single() is not None:
                valid = True
            s.close()

        return valid



    def is_container(self, sha256):
        valid = False

        with self.graph.session() as s:
            q = f'''
                MATCH (c:Container {{sha256: "{sha256}"}})
                RETURN c
                '''
                
            result = s.run(q)
            if result.single() is not None:
                valid = True
            s.close()

        return valid



    def list_vectors(self):
        container_list = {}

        with self.graph.session() as s:
            q = f'''
                MATCH (c:Container) WHERE c.size={container_size}
                RETURN c ORDER BY c.sha256
                '''
                
            result = s.run(q)

            for r in result:
                container = r.get("c")
                container_list[container.get('sha256')] = {
                    "size":     container.get('size'),
                    "graph": True
                }

            s.close()


        vectors = self.vs.list()
        for v in vectors:
            if not v in container_list:
                container_list[v] = {}
            
            container_list[v]["vector"] = True

        return container_list


    def delete_vectors(self, vector_list):
        self.vs.delete(vector_list)
        return None



    # TODO: DO NOT ATTEMPT TO CONTAINERIZE ZERO-BYTE NODES
    # TODO: The bigger question here is, should there even be a Container for a ZERO byte FileNode
    #       and if so, how to reflect this in the graph schema.
    def containerize_node(self, node_sum):
        ret_node = None

        # Split the buffer into chunks
        # Create a separate container for each chunk
        cache_path = os.path.join(self.bin_store_cache_dir, self.hex_to_path(node_sum))
        fileR = open(cache_path, "rb")

        container_list = []

        c_idx = 0
        buf = fileR.read(container_size)
        while buf:
            # Open a temporary file and write a chunk of bytes
            container_sum, container_path = self.buffer_to_path(buf)
            perma_path = os.path.join(self.bin_store_perma_dir, container_path)
            if not os.path.exists(perma_path):
                perma_dir = os.path.dirname(perma_path)
                # perma_file = os.path.basename(perma_path)
                try:
                    os.makedirs(perma_dir)
                except OSError:
                    if not os.path.isdir(perma_dir):
                        raise
            
                # TODO: instead of saving each Chunk/Container to a file,
                #       save just the last one if it's less than a Chunk size.
                #       The rest will reside in the vector DB.
                #       In the future, we need to shift from file store to MinIO;
                #       this way all data is shared as we scale up.
                with open(perma_path, "wb") as f:
                    print(perma_path)
                    f.write(buf)
                    f.close()


            container_list.append({
                'idx': c_idx,
                'sha256': container_sum,
                'size': len(buf),
                'data': buf
            })
            c_idx += 1

            buf = fileR.read(container_size)

        fileR.close()


        # Save all {container_size} data chunks into the vector DB
        size_list = [c['size'] for c in container_list]
        sha256_list = [c['sha256'] for c in container_list]
        data_list = [c['data'] for c in container_list]

        if size_list[-1] < container_size:
            sha256_list.pop()
            data_list.pop()


        batch_list = []            
        while len(sha256_list) > 0:
            batch = [
                sha256_list[:container_chunking_batch_size],
                data_list[:container_chunking_batch_size]
            ]
            batch_list.append(batch)
            del sha256_list[:container_chunking_batch_size]
            del data_list[:container_chunking_batch_size]

        for batch in batch_list:
            insert_result = self.vs.add(batch)
            print("Vectors saved: ", insert_result)


        # TODO: to be deleted
        # if len(sha256_list) > 0:
        #     entities = [
        #         sha256_list,
        #         data_list
        #     ]
        #     # TODO: temporarily disabled
        #     insert_result = self.vs.insert(entities)
        #     print("Vectors saved: ", insert_result)


        batch_list = []            
        while len(container_list) > 0:
            batch = container_list[:container_chunking_batch_size]
            batch_list.append(batch)
            del container_list[:container_chunking_batch_size]

        q = f'''
            MATCH (fn:FileNode {{sha256: "{node_sum}"}})-[r:STORED_IN {{idx: 0}}]->(c:Container)
            DELETE r
            RETURN fn, c
            '''
        print(q)

        with self.graph.session() as s:
            result = s.run(q)
            s.close()

        print("batch_list: ", len(batch_list))
        idx = 0
        for batch in batch_list:
            q = f'''
                MATCH (n:FileNode {{sha256: "{node_sum}"}})
                WITH n, $container_list AS container_list
                UNWIND container_list AS cl
                MERGE (c:Container {{sha256: cl.sha256}})
                ON CREATE SET c.ctime = datetime(), c.size = cl.size
                MERGE (n)-[:STORED_IN {{idx: cl.idx}}]->(c)
                RETURN n
                '''
            print(q)
            with self.graph.session() as s:
                result = s.run(q, container_list = batch)
                print(result)
                s.close()            


        return ret_node


    #
    # Given a node sha256, assemble the file from the corresponding containers
    # and put into the cache directory.
    #
    def cache_file_node(self, node_sum):
        node_meta = self.get_meta(node_sum)
        containers = node_meta.get('containers')

        cache_path = os.path.join(self.bin_store_cache_dir, self.hex_to_path(node_sum))
        if not os.path.exists(cache_path):
            cache_dir = os.path.dirname(cache_path)
            cache_file = os.path.basename(cache_path)
            try:
                os.makedirs(cache_dir)
            except OSError:
                if not os.path.isdir(cache_dir):
                    raise

        with open(cache_path, "wb") as cache_file:

            for c_sum in containers:
                container_file = open(os.path.join(self.bin_store_perma_dir, self.hex_to_path(c_sum)), "rb")
                data = container_file.read()
                cache_file.write(data)
                container_file.close()

            cache_file.close()

        return node_sum


    def buffer_to_path(self, buf):
        dig = hashlib.sha256()
        dig.update(buf)
        sum = dig.hexdigest()
        return (sum, self.hex_to_path(sum))


    # TODO: Handle Zero-bytes files
    #
    def put_file_node(self, data):
        sum, data_path = self.buffer_to_path(data)

        # Check if a FileNode with the same SHA256 already exists
        if self.is_filenode(sum):
            print(f"FileNode exists: {sum}")
            return sum

        cache_path = os.path.join(self.bin_store_cache_dir, data_path)
        if not os.path.exists(cache_path):
            cache_dir = os.path.dirname(cache_path)
            cache_file = os.path.basename(cache_path)
            try:
                os.makedirs(cache_dir)
            except OSError:
                if not os.path.isdir(cache_dir):
                    raise

            with open(cache_path, "wb") as f:
                f.write(data)


        m = magic.Magic(mime=True)
        mp = m.from_file(cache_path)

        # Create / update the FileNode in the graph
        with self.graph.session() as s:
            q = '''
                MERGE (fn:FileNode {sha256: $sha256})
                MERGE (sc:Container {sha256: $sha256})
                MERGE (fn)-[:STORED_IN {idx: 0}]->(sc)
                SET fn.mime = $mp,
                fn.ctime = datetime(),
                fn.mtime = fn.ctime,
                fn.atime = fn.ctime,
                fn.cache = $cache,
                fn.size = $size,
                sc.size = $size
                RETURN fn
                '''
            result = s.run(q, sha256 = sum, mp = mp, cache = data_path, size = len(data))
            print (result.peek())
            s.close()

        # TODO: temporarily disabled
        # print(f"Containerizing new FileNode: {sum}")
        # containerize_result = self.containerize_node(sum)
        # print("Result: ", containerize_result)

        return sum



    def put_file(self, src_path):
        blob = None

        with open(src_path, "rb") as f:
            blob = f.read()

        return self.put_file_node(blob)



    def get(self, signature):
        meta = self.get_meta(signature)

        # Check if the node is cached, and if not,
        # re-assemble it from its containers


        cache_path = self.hex_to_path(signature)
        meta['store'] = cache_path

        # Update atime of the node
        with self.graph.session() as s:
            q = '''
                MERGE (fn:FileNode {sha256: $sha256})
                SET fn.atime = datetime()
                RETURN fn
                '''
            result = s.run(q, sha256 = signature)

        return meta



    def get_meta(self, signature):
        meta = {}

        with self.graph.session() as s:
            q = '''
                MATCH (n:FileNode {sha256: $sha256})-[r:STORED_IN]->(c:Container)
                WITH n,r,c ORDER BY r.idx
                RETURN n, COLLECT(c) AS c
                '''
            result = s.run(q, sha256 = signature)
            print (result.peek())
            r = result.single()
            if r is not None:
                n = r.get('n')
                containers = r.get('c')
                meta['node'] = n.get('sha256')
                meta['size'] = n.get('size')
                meta['mime'] = n.get('mime')
                meta['containers'] = len(containers)
                # TODO: ctime, mtime, atime

            s.close()

        return meta
 

    def get_node_containers(self, signature):
        json_out = []

        with self.graph.session() as s:
            q = '''
                MATCH (n:FileNode {sha256: $sha256})-[r:STORED_IN]->(c:Container)
                WITH n,r,c
                RETURN r.idx as i, c
                ORDER BY r.idx
                '''
            result = s.run(q, sha256 = signature)
            for r in result:
                print(r.get('i'), r.get('c'))
                idx = r.get('i')
                container = r.get('c')

                similar = None

                if container.get('size') == container_size:
                    similar = self.vs.find_similar(container.get('sha256'))

                container_json = {
                    'pos':      idx,
                    'sha256':   container.get('sha256'),
                    'size':     container.get('size')
                }

                if similar is not None:
                    container_json['similar'] = similar

                json_out.append(container_json)


            s.close()

        return json_out
 


    def find_similar_container(self, sha256):
        similar = self.vs.find_similar(sha256)
        return similar



    def next_deltalize_candidate(self):
        candidate = None
        
        with self.graph.session() as s:
            q = '''
                MATCH (c:Container)
                WHERE c.size = $container_size
                AND c.simsearch IS NULL
                AND NOT (c)-[:SIMILAR_TO]-(:Container)
                RETURN c LIMIT 1
                '''
            
            result = s.run(q, container_size = container_size)
            r = result.single()
            if r is not None:
                candidate = r.get('c').get('sha256')
            s.close()

        return candidate





    def mark_similarity_searched(self, container):
        candidate = None
        
        with self.graph.session() as s:
            q = '''
                MATCH (c:Container {sha256: $sha256})
                SET c.simsearch = datetime()
                RETURN c
                '''
            
            result = s.run(q, sha256 = container)
            r = result.single()
            if r is not None:
                candidate = r.get('c').get('sha256')
            s.close()

        return candidate





    def housekeep_deltalize(self, count = 0):
        candidates = []

        with self.graph.session() as s:
            q = '''
                MATCH (c:Container) WHERE c.size<=$container_size AND c.deltalized IS NULL
                RETURN c.sha256 AS c
                '''
            
            print(q)
            result = s.run(q, container_size = container_size)
            candidates = [r.get('c') for r in result]
            s.close()
        
        # if we're in a dry run, we're done.
        # Otherwise, (re-)containerize each node
        if count > 0:
            candidates = candidates[:count]
        
        if count > 0 or count == -1:
            for c in candidates:
                print("Deltalizing {}".format(c))
                self.deltalize_container(c)


        return candidates




    def list_files(self):
        nl = []

        with self.graph.session() as s:
            q = '''
                MATCH (n:FileNode)
                RETURN n
                '''
            result = s.run(q)
            for r in result:
                nl.append(r.get('n').get('sha256'))

            s.close()

        return {'files': nl}


    def deltalize_container(self, container_sig):
        # Check if the FileNode has been deltalized already.
        # If so, return without doing anything.
        previously_deltalized = False
        with self.graph.session() as s:
            q = '''
                MATCH (c1:Container {sha256: $sha256}) WHERE c1.deltalized
                RETURN c1
                '''

            print(q)
            result = s.run(q, sha256 = container_sig)
            if result.peek() is not None:
                previously_deltalized = True

            s.close()

        if previously_deltalized:
            return True


        processed_count = DEFAULT_BATCH_SIZE

        while processed_count > 0:
            mutations = []
            no_mutations = []

            with self.graph.session() as s:
                q = '''
                    MATCH (c1:Container {sha256: $sha256})
                    MATCH (c2:Container) WHERE c2.sha256 <> $sha256 AND
                    c2.size<=$container_size AND c1<>c2 AND 
                    NOT ((c1)-[:MUTATED]->(c2) OR c2.delta_progress IS NOT NULL)
                    WITH c1.sha256 AS c1, c2.sha256 AS c2 LIMIT $limit
                    RETURN c1, COLLECT(c2) AS c2, COUNT(c2) AS n
                    '''

                print(q)
                result = s.run(q, sha256 = container_sig, container_size = container_size, limit = DEFAULT_BATCH_SIZE)
                if result.peek() is not None:
                    r = result.single()
                    if r.get("n") > 0:
                        c1 = r.get("c1")
                        c2_list = r.get("c2")
                        processed_count = r.get("n")
                        print (processed_count)
                        for c2 in c2_list:
                            print(c1, c2)
                            delta_bytes = self.qualify_container_delta(c1, c2)
                            if delta_bytes is None:
                                no_mutations.append({\
                                    "sha256": c2
                                })
                            else:
                                mutations.append({ \
                                    "sha256": c2,
                                    "delta": delta_bytes
                                })
                else:
                    processed_count = 0

                s.close()
                return


            if len(mutations):
                with self.graph.session() as s:
                    q = '''
                        MATCH (c1:Container {sha256: $sha256})
                        WITH c1, $mutations AS mutations
                        UNWIND mutations AS mutation
                        MATCH (c2:Container {sha256: mutation.sha256})
                        MERGE (c1)-[m:MUTATED]->(c2)
                        SET m.delta = mutation.delta
                        RETURN m
                        '''
                    
                    print(q)
                    result = s.run(q, sha256 = container_sig, mutations = mutations)
                    print (result.peek())
                    # r = result.single()

            if len(no_mutations):
                with self.graph.session() as s:
                    q = '''
                        WITH $no_mutations AS no_mutations
                        UNWIND no_mutations AS no_mutation
                        MATCH (c2:Container {sha256: no_mutation.sha256})
                        SET c2.delta_progress = $sha256
                        RETURN c2
                        '''
                    
                    print(q)
                    result = s.run(q, sha256 = container_sig, no_mutations = no_mutations)
                    print (result.peek())
                    # r = result.single()


        # If no more mutation pairs left, mark the Container node as "deltalized"
        with self.graph.session() as s:
            q = '''
                MATCH (c1:Container {sha256: $sha256})
                MATCH (c2:Container) WHERE c2.delta_progress IS NOT NULL
                SET c1.deltalized = TRUE,
                c2.delta_grpgress = NULL
                RETURN c1, c2
                '''

            print(q)
            result = s.run(q, sha256 = container_sig)
            print(result.peek())
            s.close()


        return True


    def deltalize(self, c1, c2, max_patch_to_ratio = None):
        # max_patch_to_ratio = 0.1
        buffer = None

        c1_path = os.path.join(self.bin_store_perma_dir, self.hex_to_path(c1))
        c2_path = os.path.join(self.bin_store_perma_dir, self.hex_to_path(c2))
        print(c1_path)
        print(c2_path)

        fc1 = open(c1_path, 'rb')
        fc2 = open(c2_path, 'rb')

        fdelta = io.BufferedRandom(io.BytesIO())
        detools.create_patch(
                        fc1, fc2, fdelta,
                        'none',             # compression
                        'hdiffpatch',       # patch_type
                        'hdiffpatch'            # algorithm
                    )
        
        fdelta.seek(0)
        delta_info = detools.patch_info(fdelta)
        print(delta_info)
        # (patch_size, compression, compression_info, dfpatch_size, data_format, dfpatch_info, to_size, \
        #     diff_sizes, extra_sizes, adjustment_sizes, number_of_size_bytes) = delta_info[1]
        
        # if to_size > 0:
        #     if  max_patch_to_ratio is None or patch_size / to_size <= max_patch_to_ratio:
        fdelta.seek(0)
        buffer = fdelta.read()


        # Connect the two Container nodes
        with self.graph.session() as s:
            q = '''
                MATCH (c1:Container {sha256: $c1})
                MATCH (c2:Container {sha256: $c2})
                MERGE (c1)-[s:SIMILAR_TO]->(c2)
                SET s.delta = $delta, s.ctime = datetime()
                RETURN c1, s, c2
                '''

            print(q)
            result = s.run(q, c1 = c1, c2 = c2, delta = buffer)
            print(result.peek())
            s.close()


        return None, buffer



    # count zero means dry run, just return the list of candidates
    # if count is greater than zero, containerize and return list of
    # processed nodes.
    def housekeep_containerize(self, batch_size=1000):
        total_containerized = 0

        last_batch_size = batch_size

        if last_batch_size > 0:
            with self.graph.session() as s:
                q = f'''
                    MATCH (fn:FileNode)-[:STORED_IN {{idx:0}}]->(c:Container) WHERE c.size > {container_size}
                    RETURN DISTINCT fn.sha256 as fn LIMIT {batch_size}
                    '''
                    
                print(q)
                result = s.run(q)
                print(result)
                to_containerize_list = result.fetch(batch_size)
                last_batch_size = len(to_containerize_list)

                for r in to_containerize_list:
                    fn = r.get("fn")
                    print(f"Containerizing FileNode: {fn}")
                    self.containerize_node(fn)

                print(last_batch_size)
                total_containerized += last_batch_size
                s.close()


        self.vs.flush()

        print("TOTAL CONTAINERIZED: ", total_containerized)

        return total_containerized



    def scrub(self, batch_size=1000):
        total_deleted = 0

        last_batch_size = batch_size

        while last_batch_size > 0:
            with self.graph.session() as s:
                q = f'''
                    MATCH (c:Container) WHERE NOT (c)<-[:STORED_IN]-(:FileNode)
                    RETURN c LIMIT {batch_size}
                    '''

                print(q)
                result = s.run(q)
                to_delete_list = result.fetch(batch_size)
                last_batch_size = len(to_delete_list)

                if last_batch_size > 0:

                    for r in to_delete_list:
                        container = r.get("c")
                        sha256 = container.get("sha256")

                        q = f'''
                            MATCH (c:Container {{sha256: "{sha256}"}})
                            DELETE c
                            '''

                        delete_result = s.run(q)
                        cache_path = os.path.join(self.bin_store_cache_dir, self.hex_to_path(sha256))
                        if os.path.exists(cache_path):
                            print("Deleting cached container: ", cache_path)
                            os.remove(cache_path)
                        else:
                            print("No file found: ", cache_path)

                print(last_batch_size)
                total_deleted += last_batch_size
                s.close()

        print("TOTAL DELETED: ", total_deleted)

        return None
    


    def stats_basic(self):
        stats_json = None

        with self.graph.session() as s:
            q = '''
                MATCH (d:Directory) WITH COUNT(d) AS Directories
                MATCH (f:Regular) WITH Directories, COUNT(f) AS Files
                MATCH (fn:FileNode)
                RETURN Directories, Files, COUNT(fn) AS FileNodes, SUM(fn.size) AS Size
                '''
            result = s.run(q)
            stats = result.peek()
            s.close()

            stats_json = {
                "directories": stats.get('Directories'),
                "files": stats.get('Files'),
                "filenodes": stats.get('FileNodes'),
                "size": stats.get('Size')
            }

        return stats_json

