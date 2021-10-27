#!/usr/bin/env python
# 
# Script used to parse the user input yaml file and query 
# the MySQL DB to dump the data in yaml format for the 
# user selected servers.
# Version: 1.0
#
import yaml
import sys
import argparse
import re
from mysql.connector import connect, Error

# Dictionary to store the keys and values fetched from different tables of 
# mule database
classified_data = {}
DEFAULT_INPUT_FILE="configs/user_input.yml"
DEFAULT_OUTPUT_FILE="configs/serverdb.yml"

#
# gencfg help
#
def gencfg_help():
    print("""
          Generate yaml template to provision IP fabric devices and Contrail Cloud
          -h: help
          -i: input yaml file (optional, default file is configs/user_input.yml)
          -o: output yaml file (optional, default file is configs/serverdb.yml)
          Syntax: ./gencfg.py -i <input yaml file> -o <output yaml file>
""")
    gencfg_exit()

#
# Function used to cleanup and any resources and exit
#
def gencfg_exit():
    sys.exit()

#
# Function to connect to the mule database and return the 
# db connection object
#
def gencfg_database_connect(user_input):
    try:
        connection = connect(
            host=user_input['mysql_server'],
            user=user_input['mysql_user'],
            password=user_input['mysql_pass'],
            database=user_input['mysql_database']
            )
        return connection
    except Error as error:
        print(f"gencfg_database_connect error: {error}")
        gencfg_help()


#
# Function used to shortlist/select the servers from serverDB, based on 
# user input
#
def gencfg_get_serverlist(user_input):
    serverlist = []

    # Loop through all the servers in serverDB to select the user 
    # selected servers
    for item in user_input:
        #print(f"input :{item}, item Type:{type(item)}")
        # Loop through all the servers from the user provided server list
        #for user_selected_server in user_server_list:
        # Check for a match 
        if (item == "jumphost") or (item == "controlhost") or \
           (item == "kernelcompute") or (item == "storage") or \
           (item == "dpdkcompute"):
            # Key Match Found, append value to serverlist
            serverlist = serverlist + user_input[item]

    # Return the selected or shortlisted servers    
    return serverlist

#
# Function used to generate unique vlan id for CC deployment dynamically 
# and update the classified_data dictionary
#
def generate_vlan_id(user_input):
    # Generate unique VLAN ID for external, internal, 
    # storage, storage_mgmt and tenant network for CC deployment.
    vlan_keys = ['native_vlan', 'external', 'internal', 'storage', 'storage_mgmt', 'tenant']
    vlan_values = []

    delimiter = re.compile(r"[.-/]")

    # Parse the "additional1" address from jumphost to generate unique vlan ID for this CC deployment
    octets = delimiter.split(classified_data['jumphost'][0]['additional1'])
    print(f"octets: {octets}")

    start, end = octets[3].split('-')
    for id in range(int(start), int(end)+1):
        vlan_values.append(id)

    # Parse the "additional1" address from controlhost to generate unique vlan ID for this CC deployment
    octets = delimiter.split(classified_data['controlhost'][0]['additional1'])
    print(f"octets: {octets}")

    start, end = octets[3].split('-')
    for id in range(int(start), int(end)+1):
        vlan_values.append(id)

    vlan_cc = dict(zip(vlan_keys, vlan_values))

    print(f"vlan_cc: {vlan_cc}")

    #classified_data['vlan_cc'] = user_input['vlan_cc']
    classified_data['vlan_cc'] = vlan_cc

#
# Function used to generate unique AE interface name for CC deployment dynamically 
# and update the classified_data dictionary
#
def generate_ae_interface(user_input):
    # Need to write logic to generate unique AE interface name for CC deployment
    # Note: For now, using the hardcoded value from user_input file
    #classified_data['ae_cc'] = user_input['ae_cc']
    pass

#
# Function used to update classified_data dictionary with contrail cloud activation
# key, organization and satellite details
#
def update_global_config(user_input):
    # Need to write logic to generate unique AE interface name for CC deployment
    # Note: For now, using the hardcoded value from user_input file
    classified_data['global_config'] = user_input['global_config']


#
# Function to fetch the column name (key) as list for the given table
#
def get_table_key_list(db_cursor, db_name, table_name, ):
    table_keys = []
    # Prepare the mysql query to fetch the key
    table_column_str = "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='{}' AND TABLE_NAME='{}'"
    get_table_column = table_column_str.format(db_name, table_name)
        
    # Query mule database
    db_cursor.execute(get_table_column)
    columns = db_cursor.fetchall()

    # print("dbs: {}, Type: {}" .format(dbs, type(dbs)))
    # Column fetched from mule DB, strip the additional characters and append each 
    # column name  to a list
    for column in columns:
        #print("column: {}, Type: {}" .format(column, type(column)) )
        table_keys.append(str(column).strip("(),'"))

    # print("table_keys: {}, Type: {}" .format(table_keys, type(table_keys)))
    # return the table key list
    return table_keys

#
# Function to fetch the Node Type (jumphost or control or compute or storage) 
# based on the server or hostname
#
def get_nodetype(hostname, user_input):
    if hostname in user_input['jumphost']:
        return "jumphost"
    elif hostname in user_input['controlhost']:
        return "controlhost"
    elif hostname in user_input['kernelcompute']:
        return "kernelcompute"
    elif hostname in user_input['dpdkcompute']:
        return "dpdkcompute"
    elif hostname in user_input['storage']:
        return "storage"
    else:
        return None

#
# Function to classify the raw data w.r.t. Node Type and store them in a
# global dictionary classified_data
#
def gencfg_classify_raw_data(table_keys, table_values, user_input):

    classified_list = []
    classified_dict = {}
 
    # Fetch the nodetype based on the server name, nodetype will be used as the key 
    # for the dicttionary
    hostname = table_values[table_keys.index('id')]
    key = get_nodetype(hostname, user_input)
    
    # Convert the row and column into a dictionary
    row_as_dict = dict(zip(table_keys, table_values))

    # If the dictionary is empty, insert row_as_dict (value) to 
    # classified_data directly with nodetype as key
    if not classified_data:
        classified_list.append(row_as_dict)
        classified_data[key] = classified_list
    # If the dictionary is not empty, but key is not found in classified_data,
    # then create a dictionary with row_as_dict (value) and nodetype as key.
    # Update classified_data with the newly created dictionary 
    elif key not in classified_data:
        classified_list.append(row_as_dict)
        classified_dict[key] = classified_list
        classified_data.update(classified_dict)
    # If the dictionalry is not empty, but key is found in classified_data,
    # then update the existing dictionary
    elif key in classified_data:
        classified_list = classified_data[key]
        
        # Each key will have a list of dictionaries, loop through the list
        # to find the right dictionary and update the same
        for index in range(len(classified_list)):
            if classified_list[index]['id'] == hostname:
                # If the dictionary is found, update and break
                classified_list[index].update(row_as_dict)
                entry_found = True
                break
            else:
                # If the dictionary is not found, mark entry not 
                # found
                entry_found = False

        # If the dictionary not found, then append the dictionary
        # in the existing list and update the classified_data with the 
        # updated data
        if not entry_found:
            classified_list.append(row_as_dict)
            classified_data[key] = classified_list
    else:
        return



#
# Function to fetch the required data from MySQL DB and 
# classify the input data appropriately
#
def gencfg_main_module(param):

    # Load the user config/input file
    with open(param.input_file) as ui_fd:
        user_input = yaml.load(ui_fd)
    
    # print("user_input: {}" .format(user_input))
    # Get the list of servers user selected to provision Contrail Cloud
    server_list = gencfg_get_serverlist(user_input)
    server_list_str = str(server_list).strip('[]')

    # print("server_list: {}, Type: {}" .format(server_list, type(server_list)))
    # Create a database connection
    db_connection = gencfg_database_connect(user_input)
    db_cursor = db_connection.cursor()

    # The data from mule database is split in 3 different tables, for CC deployment
    # classifying the raw data and merge the table data w.r.t node type (jumphost, 
    # controlhost, compute, storage, etc.,)
    for table in user_input['mysql_tables']:
        # Fetch the keys/column for the selected table
        table_keys = get_table_key_list(db_cursor, user_input['mysql_database'], table)

        #print("table_keys: {}, Type: {}" .format(table_keys, type(table_keys)))
        db_format_str = "SELECT * FROM {} WHERE id IN ({})"
        db_query = db_format_str.format(table, server_list_str)
        
        # print("db_query: {}" .format(db_query))
        # Query mule database to dump the rows/values of the selected table 
        db_cursor.execute(db_query)

        for db in db_cursor:
            # print("db:{}, Type:{}".format(list(db), type(list(db))))
            # Rows fetched from mule DB are in tuple format, covert them to list 
            # and form a dictionary, row -> key and column -> values
            table_values = list(db)

            # Classify the raw data from mule and store it in a dictionary
            gencfg_classify_raw_data(table_keys, table_values, user_input)

    # Close db connection
    db_connection.close()

    # Generate unique vlan id for contrail cloud deployment
    generate_vlan_id(user_input)

    # Generate unique AE interface name for contrail cloud deployment
    generate_ae_interface(user_input)

    # Update global config
    update_global_config(user_input)

    return

#
# Function to write the classified data in yaml template 
#
def gencfg_generate_yaml_template(user_input):
    # After classifying the data from all 3 tables, 
    # write the classified data in a yaml file which will be used for provisioning
    # IP fabric and generate contrail cloud templates
    with open(user_input.output_file, 'w+') as fd:
	    out = yaml.dump(classified_data, fd)



#                                                                                 
# contrail cloud input handler to parse the input parameters and
# store them appropriately                                                                  
# 
def gencfg_input_handler():

    parser = argparse.ArgumentParser(prog='gencfg.py',
                                     usage='%(prog)s [options] path to config file',
                                     description='Fetch data to Provision Contrail Cloud',
                                     epilog='Happy Provisioning ! :-)')

    parser.add_argument('-i', '--input_file', dest='input_file', default=DEFAULT_INPUT_FILE,
                        help='Provide input config file'
                        )
    parser.add_argument('-o', '--output_file', dest='output_file', default=DEFAULT_OUTPUT_FILE,
                    help='Provide input config file'
                    )
    return parser


#
# main function
#
if __name__ == "__main__":
    # Input handler to parse the arguments
    user_input = gencfg_input_handler().parse_args()
    
    # Call the main module to fetch data and classify
    gencfg_main_module(user_input)

    # Generate yaml template using classified data
    gencfg_generate_yaml_template(user_input)

    # Cleanup or exit
    gencfg_exit()
