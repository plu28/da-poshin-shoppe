import sqlalchemy
import json

def row_to_json(row):
    row_dict = {key: value for key, value in row._mapping.items()}
    return json.dumps(row_dict)

def rows_to_json(rows):
    json_list = ["["]
    for row in rows:
        json_list.append(f"{row_to_json(row)}")
        json_list.append(",")
    json_list.pop()
    json_list.append("]")
    return json.loads(''.join(json_list))
