import json

# This is purely for debugging
# We can use it if we ever need to write to a file 

def write_json_to_file(file_name, data, mode='w'):
    with open(file_name, mode) as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)
