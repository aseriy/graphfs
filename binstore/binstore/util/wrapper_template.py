from neo4j import GraphDatabase
import yaml
import argparse
import hashlib
import os
import logging
from age_and_emotion import age_and_emotion
from etl.binstore import BinaryStore
from neo4j_helpers import get_credentials, get_node_property_by_id, get_node_ids_by_label_name, update_node_by_id

# logging.basicConfig(filename='wrapper_test_debug.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)

conn = get_credentials('etc', 'config.yml')

def update_graph(conn, node_id):

	# Create a driver object
	driver = GraphDatabase.driver("bolt://" + conn['neo4j_url'] + ":7687", auth=(conn['neo4j_username'], conn['neo4j_password']))


	###
	# YOUR CODE HERE
	###

	driver.close()
	return result


#######################################################################################################################


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("--neo4j_url", type = str,
                        required = False,
                        default = conn['neo4j_url'],
                        help = "Neo4j host url")
    parser.add_argument("--username", type = str,
                        required = False,
                        default = conn['neo4j_username'],
                        help = "Neo4j username")
    parser.add_argument("--password", type = str,
                        required = False,
                        default = conn['neo4j_password'],
                        help = "Neo4j password")
    parser.add_argument("--binstore", type = str,
                        required = False,
                        default = conn['bin_store_dir'],
                        help = "Path to the binstore")
    parser.add_argument("--node_id", type = int,
                        required = False,
                        help = "The Node ID to be processed")

    args, unknown = parser.parse_known_args()


	##################################################################################################################

	if args.node_id:
		node_id = args.node_id
		update_graph(conn, node_id)

	else:
		driver = GraphDatabase.driver("bolt://" + conn['neo4j_url'] + ":7687", auth=(conn['neo4j_username'], conn['neo4j_password']))

		###
		label_name = 'YOUR LABEL NAME HERE'
		###

		nodes = get_node_ids_by_label_name(driver, label_name).value()
		driver.close()
		for node_id in nodes:
			result = update_graph(conn, node_id)
			print(result.single())
