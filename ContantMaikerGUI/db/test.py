import sqlite3
import networkx as nx

def convertToBinaryData(filename):
    #Convert digital data to binary format
    G = nx.read_graphml(filename)
    result = {'nodes':{},'edges':{}}
    for i in G.nodes():
        result['nodes'][i] = G.nodes[i]
        result['nodes'][i]['xpos'] = int(G.nodes[i]['xpos'])
        result['nodes'][i]['ypos'] = int(G.nodes[i]['ypos'])
        result['nodes'][i]['type'] = str(G.nodes[i]['type'])
        if 'ExpectedParsing' in G.nodes[i]:
            result['nodes'][i]['ExpectedParsing'] = str(G.nodes[i]['ExpectedParsing'])
        if 'ExpectedValue' in G.nodes[i]:
            result['nodes'][i]['ExpectedValue'] = str(G.nodes[i]['ExpectedValue'])
        if 'SY_Var' in G.nodes[i]:
            result['nodes'][i]['varName'] = str(G.nodes[i]['SY_Var'])
            del result['nodes'][i]['SY_Var']
        if 'value' in G.nodes[i]:
            result['nodes'][i]['value'] = float(G.nodes[i]['value'])
        if 'power' in G.nodes[i]:
            result['nodes'][i]['power'] = int(G.nodes[i]['power'])
        if 'unit' in G.nodes[i]:
            result['nodes'][i]['unit'] = str(G.nodes[i]['unit'])
    edgeID = 1
    for i in G.in_edges():
        result['edges'][str(edgeID)] = G.edges[i]
        result['edges'][str(edgeID)]['origin'] = int(i[0])
        result['edges'][str(edgeID)]['target'] = int(i[1])
        edgeID += 1
    print(str(result))
    return str(result).replace("'", '"').replace('False', 'false').replace('True','true')

def insertBLOB(id):
    try:
        ##############################
        conn = sqlite3.connect('PhysAIold.db')
        cursor = conn.cursor()
        cursor.execute(""" SELECT * FROM PROBLEMS WHERE ID = {}; """.format(id))
        a = list(cursor.fetchone())
        text = a[1]
        graph_path = a[3]
        bundle_id = int(a[4] != 'Introduction')+1
        cursor.close()
        conn.close()
        ################################
        conn = sqlite3.connect('PhysAI.db')
        cursor = conn.cursor()
        query = """ INSERT INTO PROBLEM (ID, BUNDLE_ID, TEXT, GRAPH) VALUES (?, ?, ?, ?)"""
        graph = convertToBinaryData(graph_path)
        data_tuple = (id,bundle_id,text,graph)
        print(data_tuple)
        cursor.execute(query, data_tuple)
        conn.commit()
        print("ok")
        cursor.close()
        conn.close()
    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)
    finally:
        if (conn):
            conn.close()
            print("the sqlite connection is closed")

def insertBLOB2(id):
    try:
        ##############################
        conn = sqlite3.connect('PhysAIold.db')
        cursor = conn.cursor()
        cursor.execute(""" SELECT * FROM SKILLS WHERE ID = {}; """.format(id))
        a = list(cursor.fetchone())
        text = a[1]
        graph_path = a[2]
        cursor.close()
        conn.close()
        ################################
        conn = sqlite3.connect('PhysAI.db')
        cursor = conn.cursor()
        query = """ INSERT INTO SKILLS (ID, NAME, GRAPH) VALUES (?, ?, ?)"""
        graph = convertToBinaryData(graph_path)
        data_tuple = (id,text,graph)
        print(data_tuple)
        cursor.execute(query, data_tuple)
        conn.commit()
        print("ok")
        cursor.close()
        conn.close()
    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)
    finally:
        if (conn):
            conn.close()
            print("the sqlite connection is closed")

for i in range(1,42):
    insertBLOB(i)

for i in range(1,8):
    insertBLOB2(i)
