#!/usr/bin/python3
import yaml
import argparse
import shutil

def main(neo4j_url, neo4j_username, neo4j_password, binstore_path):
    d = {
      "environments": {
        "DEV": {
          "BINSTORE": {
            'path': binstore_path
          },
          "NEO4J": {
            "username": neo4j_username,
            "password": neo4j_password
          }
        }
      },
      "local_url": neo4j_url
    }


    f=open('/home/vagrant/etc/config.yml','w')
    f.write(yaml.dump(d))
    f.close

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--neo4j_url", type = str,
                        required = True,
                        help = "Neo4j host url")
    parser.add_argument("--username", type = str,
                        required = False,
                        default = "neo4j",
                        help = "Neo4j username")
    parser.add_argument("--password", type = str,
                        required = False,
                        default = "capgemini",
                        help = "Neo4j password")
    parser.add_argument("--binstore", type = str,
                        required = False,
                        default = "/home/vagrant/data/binstore",
                        help = "Path to the binstore")


    args, unknown = parser.parse_known_args()
    
    binstore_path = args.binstore
    neo4j_username = args.username
    neo4j_password = args.password
    neo4j_url = args.neo4j_url
    
    main(neo4j_url, neo4j_username, neo4j_password, binstore_path)
    quit()
