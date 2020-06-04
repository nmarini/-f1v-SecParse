import csv 
import pprint 
import pathlib 
import collections
import xml.etree.ElementTree as ET

# Define Current Working Directory:
sec_directory = pathlib.Path.cwd().joinpath("sec10-K")

# Define the file path.
file_htm = sec_directory.joinpath('a201910-k.htm').resolve()
file_cal = sec_directory.joinpath('avb-20191231_cal.xml').resolve()
file_lab = sec_directory.joinpath('avb-20191231_def.xml').resolve()
file_def = sec_directory.joinpath('avb-20191231_def.xml').resolve()

# Initalize storage units, one will be the master list, one will store all the values, and one will store all GAAP info.
storage_list = []
storage_values = {}
storage_gaap = {}

# Create a named tuple
FilingTuple = collections.namedtuple('FilingTuple',['file_path','namespace_element','namespace_label'])

# Initalize my list of named tuples, I plan to parse.
files_list = [
    FilingTuple(file_cal, r'{http://www.xbrl.org/2003/linkbase}calculationLink', 'calculation'), 
    FilingTuple(file_def, r'{http://www.xbrl.org/2003/linkbase}definitionLink','definition'), 
    FilingTuple(file_lab, r'{http://www.xbrl.org/2003/linkbase}labelLink','label')
    ]

# Labels come in two forms, those I want and those I don't want.
avoids = ['linkbase','roleRef']
parse = ['label','labelLink','labelArc','loc','definitionLink','definitionArc','calculationArc']

# part of the process is matching up keys, to do that we will store some keys as we parse them.
lab_list = set()
cal_list = set()

# loop through each file.
for file in files_list:

    # Parse the tree by passing through the file.
    tree = ET.parse(file.file_path)

    # Grab all the namespace elements we want.
    elements = tree.findall(file.namespace_element)

    # Loop throught each element that was found.
    for element in elements:

        # if the element has childrent we need to loop through those.
        for child_element in element.iter():

            # split the label to remove the namespace component, this will return a list.
            element_split_label = child_element.tag.split('}')

            # The first element is the namespace, and the second element is a label.
            namespace = element_split_label[0]
            label = element_split_label[1]

            # if it's a label we want then continue.
            if label in parse:

                # define the item type label
                element_type_label = file.namespace_label + '_' + label
                
                # initalize a smaller dictionary that will house all the content from that element.
                dict_storage = {}
                dict_storage['item_type'] = element_type_label

                # grab the attribute keys
                cal_keys = child_element.keys()

                # for each key.
                for key in cal_keys:

                    # parse if needed.
                    if '}' in key:

                        # add the new key to the dictionary and grab the old value.
                        new_key = key.split('}')[1]
                        dict_storage[new_key] = child_element.attrib[key]

                    else:
                        # grab the value.
                        dict_storage[key] = child_element.attrib[key]

                    

                # At this stage I need to create my master list of IDs which is very important to program. I only want unique values.
                # I'm still experimenting with this one but I find `Label` XML file provides the best results.

                # IDs that work for the if statement below: 
                # calculation_loc
                # definition_loc

                # not sure if I should use both definition_loc and calucation_loc or only one 
                if element_type_label == 'definition_loc':
                    
                    # Grab the Old Label ID for example, `lab_us-gaap_AllocatedShareBasedCompensationExpense_E5D37E400FB5193199CFCB477063C5EB`
                    key_store = dict_storage['label']

                    # Create the Master Key, now it's this: `us-gaap_AllocatedShareBasedCompensationExpense_E5D37E400FB5193199CFCB477063C5EB`
                    master_key = key_store.replace('lab_','')

                    # Split the Key, now it's this: ['us-gaap', 'AllocatedShareBasedCompensationExpense', 'E5D37E400FB5193199CFCB477063C5EB']
                    label_split = master_key.split('_')

                    # Create the GAAP ID, now it's this: 'us-gaap:AllocatedShareBasedCompensationExpense'
                    gaap_id = label_split[1] + ':' + label_split[2]

                    # One Dictionary contains only the values from the XML Files.
                    storage_values[master_key] = {} 
                    storage_values[master_key]['label_id'] = key_store
                    storage_values[master_key]['location_id'] = key_store.replace('lab_','loc_')
                    storage_values[master_key]['us_gaap_id'] = gaap_id
                    storage_values[master_key]['us_gaap_value'] = None
                    storage_values[master_key][element_type_label] = dict_storage 

                    # The other dicitonary will only contain the values related to GAAP Metrics.
                    storage_gaap[gaap_id] = {}
                    storage_gaap[gaap_id]['id'] = gaap_id
                    storage_gaap[gaap_id]['master_id'] = master_key

                # add to dictionary.
                storage_list.append([file.namespace_label, dict_storage])