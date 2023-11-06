import yaml, argparse
from neo4j import GraphDatabase
from pathlib import Path

import logging



# Returns a dictionary with k/v pairs necessary to instantiate a driver object for Neo4j, and a reference to the bin_store path
def get_credentials(dir_name, config_file):

    path = Path.home().joinpath( f'{dir_name}' , f'{config_file}')
    with path.open(mode='r') as ymlfile:
        cfg = yaml.safe_load(ymlfile)

    env = cfg['environments']['DEV']
    bin_store_dir = env['BINSTORE']['path']
    neo4j_url, neo4j_username, neo4j_password = cfg['local_url'], env['NEO4J']['username'], env['NEO4J']['password']
    conn = {'neo4j_url': neo4j_url, 'neo4j_username': neo4j_username, 'neo4j_password': neo4j_password, 'bin_store_dir': bin_store_dir}

    return conn


# Returns a Result object containing a list of IDs for the provided label
def get_node_ids_by_label_name(driver, label_name):

    with driver.session() as s:
        q = ("MATCH (n:{label_name}) "
            "WHERE SIZE(LABELS(n)) = 1 "
            "RETURN COLLECT(id(n))"
        ).format(label_name=label_name)
        result = s.run(q)
        r = result.peek()
        s.close()

    return r


# Returns a Result object containing a Record with the node matching the provided id
def get_node_by_id(driver, node_id):

    with driver.session() as s:
        q = ("MATCH (n) "
            "WHERE id(n) = $id "
            "RETURN n"
        )
        result = s.run(q, id=node_id)
        s.close()

    return result


# Returns a Result object containing a Record with the relationship matching the provided id
def get_relationship_by_id(driver, relationship_id):

    with driver.session() as s:
        q = ("MATCH ()-[r]-() "
            "WHERE id(r) = $id "
            "RETURN r"
        )
        result = s.run(q, id=relationship_id)
        s.close()

    return result


# Returns a Result object containing a Record with the value of a node property matching the provided node_id and property_name
def get_node_property_by_id(driver, node_id, property_name):

    with driver.session() as s:
        q = ("MATCH (n) "
            "WHERE id(n) = $id "
            "RETURN n.{prop}"
        ).format(prop=property_name)
        result = s.run(q, id=node_id)
        s.close()

    return result


# Updates the properties of a node matching the provided node_id with the provided props
# Key/values in props that already exist on the node will be updated, new properties will be added, other existing properties will be LEFT UNTOUCHED
# Returns a Result object containing a Record with the value of the updated node matching the provided id
def update_node_by_id(driver, node_id, props):

    with driver.session() as s:
        q = ("MATCH (n) "
	    "WHERE id(n) = $id "
            "SET n += $props "
            "RETURN n"
        )
        result = s.run(q, {'id': node_id, 'props': props})
        s.close()

    return result


# Updates the properties of a node matching the provided node_id with the provided props
# Key/values in props that already exist on the node will be updated, new properties will be added, other existing properties will be DELETED
# Returns a Result object containing a Record with the value of the updated node matching the provided id
def remove_node_metadata_by_id(driver, node_id, props):

    with driver.session() as s:
        q = ("MATCH (n) "
			"WHERE id(n) = $id "
            "SET n = $props "
            "RETURN n"
        )
        result = s.run(q, {'id': node_id, 'props': props})
        s.close()

    return result
