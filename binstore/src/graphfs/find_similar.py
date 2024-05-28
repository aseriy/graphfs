import argparse
import json
from graphfs.graphstore import GraphStore
from util.neo4j_helpers import get_credentials

creds = get_credentials('etc', 'config.yml')
bs = GraphStore(creds)


def find_similar(limit = None):
    done = False

    while done is False:
      candidate = bs.next_deltalize_candidate()
      print("Deltalize candidate: ", candidate)

      if limit is None:
        if candidate is None:
              done = True
      else:
          if candidate is None:
              done = True

      if done is False:

        # TODO: finding multiple pairs of similar containers can be done 
        #       in parallel.
        #       A list of unique pairs can be accumulated first.
        #       The list then is checked for recipricals.
        #       Finally, it's likely that deltalization can be done multi-threaded as well.
        similar = bs.find_similar_container(candidate)

        print("SIMILAR: ", json.dumps(similar, indent=2))
        similarity_found = False
        if similar is not None:
            for s in similar:
                # Sometimes, the similarity search may return a SHA256 and
                # there is no Container in the graph identified by it.
                # First, check SHA256 is valid.
                # If none of the search results are valid Containers, then
                # bail out.
                if bs.is_container(s['sha256']):
                    container_similar = {
                        'candidate': candidate,
                        'similar': s['sha256']
                    }
                    print("FOUND SIMILARITY: ", json.dumps(container_similar, indent=2))
                    meta, buf = bs.deltalize(s['sha256'], candidate)
                    print(len(buf), buf)

                    similarity_found = True
                    break

        if similar is None or similarity_found is False:
            print("MARKING AS SIMILARITY SEARCHED: ", candidate)
            bs.mark_similarity_searched(candidate)
      

      if limit is not None:
         limit -= 1
         if limit == 0:
             done = True          

    return None


#
# Main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog = __file__,
            description = "Examine containers for similarity and record mutations."
        )

    parser.add_argument("-l", "--limit", type=int, required=False,
                        help="Limit the number of containers to the specified limit. Default: all containers."
                    )

    args, unknown = parser.parse_known_args()

    proc_limit = args.limit

    find_similar(proc_limit)

    exit(0)

