import sqlite3
import json
import networkx as nx

# connection to the database
DATABASE = 'PhysAI.db'

def process_graph(json_graph, id, name, eq):
    result = {'nodes':{},'edges':{}}
    result['nodes']["0"] = {
        'type': 'SKILL',
        'skillID': id,
        'skillName': str(name),
        'skillEQ': str(eq),
        'xpos': 2,
        'ypos': 2
    }
    edgeID = 1
    for node in json_graph['nodes']:
        if json_graph['nodes'][node]['type'] == 'V':
            result['nodes'][str(node)] = json_graph['nodes'][node]
            result['nodes'][str(node)]['skillVarLink'] = int(node)
            result['nodes'][str(node)]['xpos'] = edgeID
            result['nodes'][str(node)]['ypos'] = 1
            result['edges'][str(edgeID)] = {
                "origin": int(node),
                "target": 0,
                "weight": 2
            }
            edgeID += 1
    return str(result).replace("'", '"').replace('False', 'false').replace('True','true').replace('u"', '"')

def convertSkillGraph(id):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM SKILLS WHERE ID = {};".format(id))
        result = list(cursor.fetchone())
        # parse new graph
        graph = process_graph(json.loads(result[2]), id, result[1], result[4])
        # print(graph)
        # write new graph to DB
        cursor.execute("DELETE FROM SKILLS WHERE ID = {};".format(id))
        query = """ INSERT INTO SKILLS (ID, NAME, GRAPH, FRONT_GRAPH, EQUATION) VALUES (?, ?, ?, ?, ?) """
        data_tuple = (result[0],result[1],result[2],graph,result[4])
        print(data_tuple)
        cursor.execute(query, data_tuple)
        conn.commit()
        print("ok")
        cursor.close()
        conn.close()
    except:
        print('problem!!')

for i in range(1,8):
    convertSkillGraph(i)
