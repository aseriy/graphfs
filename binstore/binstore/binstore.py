import sys
import os
import shutil
import dumper
dumper.max_depth = 10
import hashlib
import re
import magic
from neo4j import GraphDatabase
from util.neo4j_helpers import get_credentials, get_node_ids_by_label_name
import detools
import io


store_perma_dir = 'perma'
store_cache_dir = 'cache'

# This is temporarily here, should be moved to a config file at some point
# store container size set to 1k
container_size = 1024
DEFAULT_BATCH_SIZE = 5000


#
# CREATE INDEX IF NOT EXISTS FOR (n:FileNode) ON (n.sha256)
# CREATE INDEX ON:Container(sha256)
# CREATE INDEX ON:Container(sha256)
# CREATE INDEX ON:MUTATED(patch_to_ratio)
# CREATE INDEX ON:MUTATED(diff_extra_ratio)
# CREATE INDEX ON:MUTATED(size_data_ratio)
#

class BinaryStore():
    def __init__(self, creds):
        self.validator = re.compile('[0-9a-f]+')
        bin_store_dir = creds['bin_store_dir']
        self.bin_store_perma_dir = os.path.join(bin_store_dir, store_perma_dir)
        self.bin_store_cache_dir = os.path.join(bin_store_dir, store_cache_dir)
        self.graph = \
            GraphDatabase.driver("bolt://" + creds['neo4j_url'] + ":7687",
                                    auth=(creds['neo4j_username'],
                                    creds['neo4j_password']))


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


    # TODO: DO NOT ATTEPT TO CONTAINERIZE ZERO-BYTE NODES
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
                perma_file = os.path.basename(perma_path)
                try:
                    os.makedirs(perma_dir)
                except OSError:
                    if not os.path.isdir(perma_dir):
                        raise

            with open(perma_path, "wb") as f:
                print(perma_path)
                f.write(buf)
                f.close()

            container_list.append({'idx': c_idx, 'sha256': container_sum, 'size': len(buf)})
            c_idx += 1

            buf = fileR.read(container_size)

        fileR.close()

        with self.graph.session() as s:
            q = '''
                MATCH (n:FileNode {sha256: $sha256})-[r:STORED_IN]->(c:Container)
                DELETE r
                WITH n, $container_list AS container_list
                UNWIND container_list AS cl
                MERGE (c:Container {sha256: cl.sha256})
                SET c.ctime = datetime(), c.size = cl.size
                MERGE (n)-[:STORED_IN {idx: cl.idx}]->(c)
                RETURN n
                '''

            print(q)

            result = s.run(q, sha256 = node_sum, container_list = container_list)
            print (result.peek())
            ret_node = result.single().get('n')
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

        # Create / update the File node in the graph
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

        # TODO: Update atime of the node

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
                # meta['containers'] = [c.get('sha256') for c in containers]
                meta['containers'] = len(containers)

            s.close()

        return meta
 

    # count zero means dry run, just return the list of candidates
    # if count is greater than zero, containerize and return list of
    # processed nodes.
    def housekeep_containerize(self, count = 0):
        candidates = []

        with self.graph.session() as s:
            q = '''
                MATCH (n:FileNode)-[:STORED_IN]->(c:Container) WHERE c.size > $container_size
                RETURN DISTINCT n
                '''
                
            result = s.run(q, container_size = container_size)
            candidates = [r.get('n').get('sha256') for r in result]
            s.close()

        
        # if we're in a dry run, we're done.
        # Otherwise, (re-)containerize each node
        if count > 0:
            candidates = candidates[:count]
        
        if count > 0 or count == -1:
            for c in candidates:
                print("Containerizing {}".format(c))
                self.containerize_node(c)


        return candidates


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


    
    def qualify_container_delta(self, c1, c2):
        max_patch_to_ratio = 0.1
        buffer = None

        c1_path = os.path.join(self.bin_store_perma_dir, self.hex_to_path(c1))
        c2_path = os.path.join(self.bin_store_perma_dir, self.hex_to_path(c2))
        # print(c1_path)
        # print(c2_path)

        fc1 = open(c1_path, 'rb')
        fc2 = open(c2_path, 'rb')

        fdelta = io.BufferedRandom(io.BytesIO())
        detools.create_patch(fc1, fc2, fdelta)
        fdelta.seek(0)
        delta_info = detools.patch_info(fdelta)
        # print(delta_info)
        # ('sequential', (1044, 'lzma', None, 0, None, None, 1024, [0, 9, 26, 10], [46, 0, 1, 932], [939, 1, 0, -159], 15.0))
        (patch_size, compression, compression_info, dfpatch_size, data_format, dfpatch_info, to_size, \
            diff_sizes, extra_sizes, adjustment_sizes, number_of_size_bytes) = delta_info[1]

        if to_size > 0 and patch_size / to_size <= max_patch_to_ratio:
            fdelta.seek(0)
            buffer = fdelta.read()

        return buffer


# ('sequential', (
# patch_size            1044                    Patch size:         1.02 KiB
# compression           'lzma'
# compression_info      None
# dfpatch_size          0
# data_format           None
# dfpatch_info          None 
# to_size               1024                    To size:            1 KiB
# diff_sizes            [0, 9, 26, 10]
# extra_sizes           [46, 0, 1, 932]
# adjustment_sizes      [939, 1, 0, -159]
# number_of_size_bytes  15.0


# Patch/to ratio:     (patch_size / to_size) (lower is better)
# Diff/extra ratio:   (number_of_diff_bytes / number_of_extra_bytes) (higher is better)
# Size/data ratio:    (number_of_size_bytes / number_of_data_bytes) (lower is better)

#     number_of_diff_bytes = sum(diff_sizes)
#     number_of_extra_bytes = sum(extra_sizes)
#     number_of_data_bytes = (number_of_diff_bytes + number_of_extra_bytes)
#     size_data_ratio = _format_ratio(number_of_size_bytes, number_of_data_bytes)
#     patch_to_ratio = _format_ratio(patch_size, to_size)
#     diff_extra_ratio = _format_ratio(number_of_diff_bytes, number_of_extra_bytes)
#     compression = _format_compression(compression, compression_info)
