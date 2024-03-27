import argparse
import json
from graphfs.graphstore import GraphStore
from util.neo4j_helpers import get_credentials

creds = get_credentials('etc', 'config.yml')
bs = GraphStore(creds)


def find_similar(limit = None):
    done = False

    while done is False:
      # print("WHILE: ", done)
      # print("LIMIT: ", limit)

      candidate = bs.next_deltalize_candidate()
      print("Deltalize candidate: ", candidate)

      if limit is None:
        if candidate is None:
              done = True
      else:
          if candidate is None:
              done = True

      # print("IF: ", done)
      if done is False:
        similar = bs.find_similar_container(candidate)
        if similar is not None:
            container_similar = {
                'sha256': candidate,
                'similar': similar
            }
            print(json.dumps(container_similar, indent=2))
            meta, buf = bs.deltalize(similar['sha256'], candidate)
            print(len(buf), buf)

        else:
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

