# Library for float division
from __future__ import division
# OS path library
import os
# Regular expression library
import re
# Library used for scientific calculations (wolfram alpha in python)
import sympy as sy
# Library used for numeric transformation (sorting)
import numpy as np
# Library used for unit interconversions
import pint
# Library for graphs
import networkx as nx
# Library that allowed to make deepcopies
from copy import deepcopy



class GraphSolver():
    # Initialization of the graph either through the
    # name of the model or though the saved object
    def __init__(self, Name = None, Graph = None,
                 Model = None, Trace = False,
                 Debug = False, Illustrate = False):
        # create a registry object for calculations with units
        self.ureg = pint.UnitRegistry()
        # if both model name and graph object given return an exception
        if Model and Graph:
            raise Exception('Please, initialyse the model either \
                             with existing graph or with a template model!')
        # if neither model name nor a graph object given return an exception
        elif not Model and not Graph:
            raise Exception('Please, initialyse the model either \
                             with existing graph or with a template model!')
        # initialyse model with its name
        elif Model:
            self.Path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', Model + '.graphml')
            self.G = nx.read_graphml(self.Path)
            self.G = self.PrepareGAfterImport(self.G)
        # initialyse model with premade object
        elif Graph:
            self.G = Graph
            self.G = self.PrepareGAfterImport(self.G)
        # add a name to the graphsover object
        if Name:
            self.G.graph['name'] = Name
        # set the global variables according to the input
        self.Initialysed_G_eq = False
        if Illustrate:
            self.Illustrate = 1
        else: self.Illustrate = False
        self.Trace = Trace
        self.Debug = Debug
        self.SymmetryCount = 0
        self.FusionCount = 0



    def Check(self):
        # Find all variables and equations to be Found
        VariablesToBeFound = {}
        EquationsToBeParsed = {}
        Message = ''
        for i in self.G.nodes():
            if 'ExpectedValue' in self.G.nodes[i]:
                VariablesToBeFound[i] = self.G.nodes[i]['ExpectedValue']
            if 'ExpectedParsing' in self.G.nodes[i]:
                EquationsToBeParsed[i] = self.G.nodes[i]['ExpectedParsing']

        SolvedCorrect = True

        for i in VariablesToBeFound.keys():
            result = self.Interactive_Solving_Hidden(i)
            print(result)
            if result != float(VariablesToBeFound[i]):
                SolvedCorrect = False
                print(result)
                sentence = str(self.G.nodes[i]['SY_Var']) + \
                            '=' + str(result) + str(self.G.nodes[i]['unit'])
                Message += sentence
            else:
                sentence = str(self.G.nodes[i]['SY_Var']) + \
                            ' = ' + str(result*self.G.nodes[i]['unit'])
                Message += sentence +'\n'

        for i in EquationsToBeParsed.keys():
            parsing = str(self.Parse_Eq(i)[0])
            if parsing != EquationsToBeParsed[i]:
                SolvedCorrect = False
                print(parsing)
                sentence = 'Now equation reads: ' + parsing + \
                               '\nIt should be: ' + EquationsToBeParsed[i]

                Message += sentence +'\n'
            else:
                sentence = 'Equation reads: ' + parsing
                Message += sentence

        return Message, SolvedCorrect



    # Return the list of physical quantities representing graph variables
    def PhysRead(self):
        Container = {}
        for i in self.G.nodes(data = 'type'):
            if i[1] == 'V':
                VariableName = str(self.G.nodes[i[0]]['SY_Var'])
                VariableUnit = str(self.G.nodes[i[0]]['PQ'])
                Container[VariableName] = VariableUnit
        return Container



    def preparePG(self, Node, Graph):
        for i in Graph.predecessors(Node):
            if Graph.nodes[i]['type'] == 'PEI':
                for j in Graph.predecessors(i):
                    powerNode = j
                    PEINode = i

            else:
                Graph.nodes[Node]['base'] = i
        Graph.nodes[Node]['power'] = powerNode
        Graph.add_edge(powerNode,Node)
        Graph.edges[powerNode,Node]['weight'] = Graph.edges[powerNode,PEINode]['weight'] * \
                                         Graph.edges[PEINode,Node]['weight']
        Graph.remove_node(PEINode)
        return Graph


    # Prepare the graph after import from graphml
    def PrepareGAfterImport(self, Graph):
        # PowerGates to be corrected
        PGcontainer = []
        # Remaping to change node names from str to int
        Remaping = {}
        for i in range(len(Graph)):
            Remaping[str(i)] = i
        Graph = nx.relabel_nodes(Graph, Remaping)
        # Add the default atributes to the variable and switch nodes and
        # functionalyse the string atributes such as unit and SY_Var
        for i in Graph.nodes(data = 'type'):
            if i[1] == 'PG':
                PGcontainer.append(i[0])
            if i[1] == 'V':
                if ('known' in Graph.nodes[i[0]]) and Graph.nodes[i[0]]['known']:
                    value = float(Graph.nodes[i[0]]['value'])
                    Graph.nodes[i[0]]['value'] = value
                else:
                    Graph.nodes[i[0]]['known'] = False
                unit_text = Graph.nodes[i[0]]['unit']
                Graph.nodes[i[0]]['unit'] = 1*self.ureg[unit_text]
                SY_Var_text = Graph.nodes[i[0]]['SY_Var']
                Graph.nodes[i[0]]['SY_Var'] = sy.Symbol(SY_Var_text)
            if i[1] == 'SWITCH':
                Graph.nodes[i[0]]['EnableNodes'] = []
        # Fill the EnableNodes attribute list of the switch nodes by
        # collecting the edges with switch attribute mark
        for (i,j) in Graph.edges():
            if 'Switch' in Graph.edges[i,j]:
                Weight = Graph.edges[i,j]['weight']
                tupel = (i,j,Weight)
                Switch = Graph.edges[i,j]['Switch']
                Graph.nodes[Switch]['EnableNodes'].append(tupel)
        # Deactivate switched edges
        for i in Graph.nodes(data = 'type'):
            if i[1] == 'SWITCH':
                for j in Graph.nodes[i[0]]['EnableNodes']:
                    Graph.remove_edge(j[0],j[1])
        for i in PGcontainer:
            Graph = self.preparePG(i, Graph)
        return Graph



    # Initialization of G_eq():
    def Make_G_Eq(self):
        self.G_eq = nx.Graph()
        # Add all of the nodes
        for i in self.G.nodes(data = 'type'):
            if (i[1] == 'E') or ((i[1] == 'V') and not self.G.nodes[i[0]]['known']):
                self.G_eq.add_node(i[0], type = i[1])
        # Add the edges
        for i in self.G_eq.nodes(data = 'type'):
            if i[1] == 'V':
                Eq_List = self.Get_Connected_Eq(i[0],
                                                i[0],
                                                Ignore_List=[],
                                                Eq_List=[])
                for j in Eq_List:
                    self.G_eq.add_edge(i[0],j)


    # Fusion base funcitonality (not for user)
    def Fusion_Base(self, VarNode1, VarNode2, Factor):
        # Switching on the edges if the switch is trigered by the first node
        if 'EnableSwitch' in self.G.nodes[VarNode1]:
            SwitchNode = self.G.nodes[VarNode1]['EnableSwitch']
            if self.G.nodes[SwitchNode]['Enabled'] == False:
                self.G.nodes[SwitchNode]['Enabled'] = True
                self.G.add_weighted_edges_from(self.G.nodes[SwitchNode]['EnableNodes'])
                if self.Debug:
                    print('SWITCH GATE triggered during variable fusion.', \
                          'Swithing on the following edges:', \
                          self.G.nodes[SwitchNode]['EnableNodes'])
        # Switching on the edges if the switch is trigered by the second node
        if 'EnableSwitch' in self.G.nodes[VarNode2]:
            SwitchNode = self.G.nodes[VarNode2]['EnableSwitch']
            if self.G.nodes[SwitchNode]['Enabled'] == False:
                self.G.nodes[SwitchNode]['Enabled'] = True
                self.G.add_weighted_edges_from(self.G.nodes[SwitchNode]['EnableNodes'])
                if self.Debug:
                    print('SWITCH GATE triggered during variable fusion.', \
                          'Swithing on the following edges:', \
                          self.G.nodes[SwitchNode]['EnableNodes'])
        # If both variables are known and their values do not match
        # then raise an exception
        elif self.G.nodes[VarNode1]['known'] and \
             self.G.nodes[VarNode2]['known'] and \
            (self.G.nodes[VarNode1]['value'] != self.G.nodes[VarNode2]['value']):
            raise Exception('Fused variables',
                            self.G.nodes[VarNode1]['SY_Var'],'and',
                            self.G.nodes[VarNode1]['SY_Var'], \
                            'are both known and their values',
                            self.G.nodes[VarNode1]['value'],'and', \
                            self.G.nodes[VarNode2]['value'],'do not match!')
        # Link all of the nodes that were connected to the VarNode2
        # (variable from model 2) to VarNode1 (variable from model 1)
        for i in self.G.out_edges(VarNode2, data='weight'):
            self.G.add_weighted_edges_from([(VarNode1, i[1], i[2]*Factor)])
            # Relink the power gate (base or power) if the variable
            # is linked to PG
            if self.G.nodes[i[1]]['type'] == 'PG':
                if self.G.nodes[i[1]]['base'] == i[0]:
                    self.G.nodes[i[1]]['base'] = VarNode1
                if self.G.nodes[i[1]]['power'] == i[0]:
                    self.G.nodes[i[1]]['power'] = VarNode1
        # If variable 2 is known
        if self.G.nodes[VarNode2]['known']:
            # If variable 1 is not known then copy to this variable
            # value from variable 2
            if not self.G.nodes[VarNode1]['known']:
                self.G.nodes[VarNode1]['known'] = True
                self.G.nodes[VarNode1]['value'] = self.G.nodes[VarNode2]['value'] * Factor
                self.G.nodes[VarNode1]['SymbRepr'] = self.G.nodes[VarNode2]['SymbRepr']
            # If both variables are known and their values
            # do not match then raise an exception
            elif self.G.nodes[VarNode1]['value'] != self.G.nodes[VarNode2]['value']:
                raise Exception('Fused variables',
                                self.G.nodes[VarNode1]['SY_Var'],'and',
                                self.G.nodes[VarNode1]['SY_Var'],
                                'are both known and their values',
                                self.G.nodes[VarNode1]['value'],'and',
                                self.G.nodes[VarNode2]['value'],
                                'do not match!')
        # Delete all edges pointing to the fused variable
        EdgeList = []
        for i in self.G.out_edges(VarNode2):
            EdgeList.append(i[1])
        for i in EdgeList:
            self.G.remove_edge(VarNode2,i)
        # Create a fusion equation that leads to the fusion variable
        self.FusionCount += 1
        EqName = 'FE-' + str(self.FusionCount)
        self.G.add_node(EqName, type='E', main=VarNode1)
        self.G.add_weighted_edges_from([(VarNode1,EqName,Factor),
                                        (VarNode2,EqName,-1)])
        # Update G_eq
        self.Make_G_Eq()
        self.Check_For_Symmetry(VarNode1)



    # Fusion of two variables inside of the model
    def Fusion(self, VarName1, VarName2, Factor = 1):
        # Get the adress of both variables
        VarNode1 = self.Find_Node_By_Var_Name(VarName1)
        VarNode2 = self.Find_Node_By_Var_Name(VarName2)
        # Trigger the exception if some variables not found
        if not VarNode1:
            raise Exception('Variable', VarName1,
                            'not found during fusion!')
        if not VarNode2:
            raise Exception('Variable', VarName2,
                            'not found during fusion!')
        if self.Debug:
            print('Fusion of those two nodes:', \
                   VarNode1, VarNode2, \
                   'with factor of', Factor)
        # Path fusion to the base function
        self.Fusion_Base(VarNode1, VarNode2, Factor)



    #Find the node by name
    def Find_Node_By_Var_Name(self, VarName):
        VarNode = None
        # Iterate through the variables to find the variable with particular name
        for (i, j) in self.G.nodes(data='type'):
            if (VarNode == None) and \
               (j == 'V') and \
               (self.G.nodes[i]['SY_Var'].name == VarName):
                VarNode = i
        return VarNode



    # Evaluation of the node
    def Evaluate(self, NodeNum, Ignore_List = []):
        # Parse the equation and evaluate it
        Value = self.Parse_Eq(NodeNum, Ignore_List)[0]
        # If equation can be evaluated to integer then return true
        if isinstance(Value, int):
            return Value, True
        else:
            return Value, False



    # RECURRENT FUNCTION!
    # Check for the zero equation (equation with only one branch)
    # The idea is to represent equation as 0 = (a1^p1)*(a2^p2)*(a3^p3)...
    # In case if the whole equaiton is determined and
    # only one power value is positive then the base corresponding to
    # the positive power must be 0
    # a and p values with be stored in the list of tupels [(a1,p1),...]
    # called Multiplication_List
    def Zero_Equation(self, Start, NodeNum, Ignore_List = [],
                      Multiplication_List = [], Power = 1):
        AllowedTypes = ['MG','ABS','SIN','COS']
        Ignore_List.append(NodeNum)
        Determined = True
        # If 0 = a ^ b, then evaluate b and add it to the multiplication list
        if self.G.nodes[NodeNum]['type'] == 'PG':
            if not (self.G.nodes[NodeNum]['base'] in Ignore_List):
                LocalPower = self.Evaluate(self.G.nodes[NodeNum]['power'],
                                           Ignore_List = [NodeNum])
                if LocalPower[1]:
                    PowerEdge = self.G.edges[self.G.nodes[NodeNum]['power'],NodeNum]
                    TruePower = LocalPower[0] * PowerEdge['weight']
                    Multiplication_List = self.Zero_Equation(Start,
                                                             self.G.nodes[NodeNum]['base'],
                                                             Ignore_List,
                                                             Multiplication_List,
                                                             Power*TruePower)
                else: Determined = False
        elif self.G.nodes[NodeNum]['type'] in AllowedTypes:
            for i in self.G.predecessors(NodeNum):
                if not i in Ignore_List:
                    Multiplication_List = self.Zero_Equation(Start, i,
                                                             Ignore_List,
                                                             Multiplication_List,
                                                             Power)
        elif (self.G.nodes[NodeNum]['type'] == 'V') and \
             (self.G.nodes[NodeNum]['known'] == False):
            Multiplication_List.append([NodeNum, Power])
        if (NodeNum == Start) and Determined:
            Order = 0
            ZeroNode = 0
            for i in Multiplication_List:
                if i[1]>0:
                    Order += 1
                    ZeroNode = i[0]
            if Order == 1:
                if self.Debug:
                    print('Set the node', ZeroNode, \
                          'to 0 due to the zero equaiton', Start)
                self.Update_Var_Solution(ZeroNode, 0, 0)
        return Multiplication_List



    # Looping through the nodes to trigger the zero_import
    # function upon imported zero variables.
    def Zero_Import_Wrapper(self):
        NodeList = []
        for i in self.G:
            if (self.G.nodes[i]['type'] == 'V') and self.G.nodes[i]['known'] and \
               (self.G.nodes[i]['value'] == 0):
               NodeList.append(i)
        for i in NodeList:
            if self.Debug:
                print('Initialysed the zero import algorithm for the node', i)
            self.Zero_Import(i, i, Ignore_List = [], Remove_List = [])



    # RECURRENT FUNCTION!
    # Dealing with importing of a zero to avoid problems with division through
    # zero and autofilling of zero variables that can be implyed by imported zero variable
    # Instruction 1: At start -> look for all of the neighbors of the zero node
    # Instruction 2: At multiplication gates and abs gates -> look at the node
    # in the direction of the equation (specified as 'eqNode')
    # Instruction 3: At power gate (if zero came from the base) -> look at the
    # node in the direction of the equation (specified as 'eqNode')
    # Instruction 4: At power gate (if zero came from the power) -> replace
    # the node by the constant 1 (node 0 in all of the models)
    # Instruction 5: At equations -> delete the edge connecting the equation to the zero node
    def Zero_Import(self, Start, NodeNum,
                    Ignore_List = [], Remove_List = []):
        AllowedTypes = ['MG','ABS','SIN']
        Ignore_List.append(NodeNum)
        SuccList = []
        if NodeNum == Start:
            for i in self.G.successors(NodeNum):
                SuccList.append(i)
            for i in SuccList:
                self.Zero_Import(Start, i, Ignore_List, Remove_List)
        elif self.G.nodes[NodeNum]['type'] in AllowedTypes:
            #if self.G.has_edge(NodeNum, self.G.nodes[NodeNum]['eqNode']):
            for i in self.G.successors(NodeNum):
                self.Zero_Import(Start,
                                 i,#self.G.nodes[NodeNum]['eqNode'],
                                 Ignore_List,
                                 Remove_List)
            del Ignore_List[-1]
        elif self.G.nodes[NodeNum]['type'] == 'PG':
            # Check if the zero is in the base (0 ** x) then
            # propagate the zero import
            if Ignore_List[-2] == self.G.nodes[NodeNum]['base']:
                for i in self.G.successors(NodeNum):
                    self.Zero_Import(Start,i,
                                     Ignore_List,
                                     Remove_List)
            # In case the zero is in the power (x ** 0) then
            # substitute the node by the one with appropriate weight
            else:
                # Determine the weight of the connection between
                # power gate and next node in the direction of the
                # equation ('eqNode')
                OutNode = list(self.G.successors(NodeNum))[0]
                Weight_Of_Connection = self.G.edges[NodeNum,OutNode]['weight']
                # Replace the power gate by the node of constant 1 (node 0)
                self.G.add_weighted_edges_from([(0, OutNode,
                                                 Weight_Of_Connection)])
                self.G.remove_node(NodeNum)
            del Ignore_List[-1]
        elif self.G.nodes[NodeNum]['type'] == 'COS':
            # Determine the weight of the connection between
            # cosinus (cos(0)) node and next node in the
            # direction of the equation ('eqNode')
            OutNode = list(self.G.successors(NodeNum))[0]
            Weight_Of_Connection = self.G.edges[NodeNum,OutNode]['weight']
            if self.Debug:
                print('Set the node', NodeNum, \
                      'to a constant 1 as it is equal to cos(0)')
            # Replace the COS gate by the node of constant 1
            self.G.nodes[NodeNum]['type'] = 'I'
            self.G.nodes[NodeNum]['value'] = 1
            # Remove all of the incomming edges
            outEdges = []
            for i in self.G.out_edges(NodeNum):
                outEdges.append(i)
            for i in outEdges:
                self.G.remove_edge(*i)
            #self.G.add_weighted_edges_from([(0, OutNode,
            #                                 Weight_Of_Connection)])
            #self.G.remove_node(NodeNum)
        elif self.G.nodes[NodeNum]['type'] == 'E':
            Remove_List.append([Ignore_List[-2],NodeNum])
            del Ignore_List[-1]
        # Finishing procedure
        if NodeNum == Start:
            for i in Remove_List:
                if self.Debug:
                    print('Removed the edge from G during Zero Import check (', \
                          i[0], '<->', i[1], ')')
                self.G.remove_edge(i[0],i[1])
                # If the equation that was disconnected from
                # zero variable has only one connection more
                # then check whether this connection can be set to 0
                if self.G.degree(i[1]) == 1:
                    # Zero element of is the only neighbor of zero equation
                    ZeroElement = [n for n in self.G.predecessors(i[1])][0]
                    if self.Debug:
                        print('Initialysed the zero function algorithm for the node', \
                              ZeroElement)
                    self.Zero_Equation(ZeroElement,
                                       ZeroElement,
                                       Ignore_List = [i[0]],
                                       Multiplication_List = [],
                                       Power = 1)



    # Update the variable
    def Update_Var_Solution(self, VarNode, Value, Symb_Solution):
        G_eq_changed = False
        # Switch on the edges that are controled by this node
        if 'EnableSwitch' in self.G.nodes[VarNode]:
            SwitchNode = self.G.nodes[VarNode]['EnableSwitch']
            if self.G.nodes[SwitchNode]['Enabled'] == False:
                self.G.nodes[SwitchNode]['Enabled'] = True
                self.G.add_weighted_edges_from(self.G.nodes[SwitchNode]['EnableNodes'])
                G_eq_changed = True
                if self.Debug:
                    print('SWITCH GATE triggered upon variable import (solution).\
                          Swithing on the following edges:', \
                          self.G.nodes[SwitchNode]['EnableNodes'])
        if Value == 0:
            if self.Debug:
                print('Initialysed the zero import algorithm for the node', \
                      VarNode)
            self.Zero_Import(VarNode, VarNode, Ignore_List=[], Remove_List=[])
            G_eq_changed = True
        if G_eq_changed:
            # REDO the implementation of G_eq
            self.Make_G_Eq()
        self.G.nodes[VarNode]['known'] = True
        self.G.nodes[VarNode]['value'] = Value
        self.G.nodes[VarNode]['SymbRepr'] = Symb_Solution
        if self.Debug:
            print('The node', VarNode, \
                  'was set to the following value:', Value, \
                  'and with following symbolic representation:', Symb_Solution)
        # Upade G_eq
        self.G_eq.remove_node(VarNode)



    # Update the variable
    def Update_Var_Import(self, VarNode, Value):
        # Switch on the edges that are controled by this node
        if 'EnableSwitch' in self.G.nodes[VarNode]:
            SwitchNode = self.G.nodes[VarNode]['EnableSwitch']
            if self.G.nodes[SwitchNode]['Enabled'] == False:
                self.G.nodes[SwitchNode]['Enabled'] = True
                self.G.add_weighted_edges_from(self.G.nodes[SwitchNode]['EnableNodes'])
                if self.Debug:
                    print('SWITCH GATE triggered upon variable import. \
                          Swithing on the following edges:', \
                          self.G.nodes[SwitchNode]['EnableNodes'])
        self.G.nodes[VarNode]['known'] = True
        self.G.nodes[VarNode]['value'] = Value
        self.G.nodes[VarNode]['SymbRepr'] = self.G.nodes[VarNode]['SY_Var']
        if self.Debug:
            print('The node', VarNode, \
                  'was set to the following value:', Value)



    # Import data to the graph
    def Import_Old(self, VarName, Value):
        # Find the node by searching the variable names
        VarNode = self.Find_Node_By_Var_Name(VarName)
        if VarNode != None:
            if self.Debug:
                print('Updating the node:', VarNode)
            self.Update_Var_Import(VarNode, Value)
        else:
            raise Exception('Imported variable name was not found! Please, \
                            make sure the model and the variable is correct.')



    # Import data as text for user
    def Import(self, InputString):
        # Parse the input string
        Break = InputString.find('=')
        VarName = InputString[:Break].strip()
        VarNode = self.Find_Node_By_Var_Name(VarName)
        SetFunction = InputString[Break+1:].strip()
        Prefix = SetFunction[0]
        # Import the value of the variable if its numeric
        if Prefix.isdigit() or Prefix == '-':
            Break = SetFunction.find(' ')
            if Break == -1:
                Value = float(eval(SetFunction))
                self.Update_Var_Import(VarNode, Value)
            else:
                Value = float(eval(SetFunction[:Break].strip()))
                Unit = self.ureg[SetFunction[Break+1:].strip()]
                if Unit != self.G.nodes[VarNode]['unit']:
                    Value *= Unit.to(self.G.nodes[VarNode]['unit']).magnitude
                self.Update_Var_Import(VarNode, Value)
        else:
            Break = SetFunction.find('*')
            if Break == -1:
                VarName = SetFunction
                VarNode2 = self.Find_Node_By_Var_Name(VarName)
                self.Fusion_Base(VarNode, VarNode2, 1)
            else:
                VarName = SetFunction[:Break].strip()
                VarNode2 = self.Find_Node_By_Var_Name(VarName)
                Factor = float(eval(SetFunction[Break+1:].strip()))
                self.Fusion_Base(VarNode, VarNode2, Factor)



    # RECURRENT FUNCTION!
    # Function that gathers the equations connected to the discovered variable
    # Instruction 1: Each sampled equation is saved to Eq_List
    # Instruction 2: Stop algorithm on variables, that are not the discovered one
    # (saved under start input variable) and stop it at constants
    # Instruciton 3: On structural nodes look in the direction of the equation ('eqNode')
    # Ignore list is the list of nodes that were inspected before (to stop the algorithm to go back)
    # Start is a saved position of the first variable (it will allow to iterate through the variable)
    def Get_Connected_Eq(self, Start, NodeNum, Ignore_List=[], Eq_List = []):
        Ignore_List.append(NodeNum)
        AllowedTypes = ['MG','ABS','PG','SIN','COS']
        # Look around in the beginning
        if NodeNum == Start:
            for i in self.G.successors(NodeNum):
                if not (i in Ignore_List):
                    Eq_List = self.Get_Connected_Eq(Start, i,
                                                    Ignore_List,
                                                    Eq_List)
        # If the node is an equation:
        elif self.G.nodes[NodeNum]['type'] == 'E':
            Eq_List.append(NodeNum)
        # If the node is structural then go in the direction equation:
        elif (self.G.nodes[NodeNum]['type'] in AllowedTypes):
            OutNode = list(self.G.successors(NodeNum))
            if len(OutNode) == 1:
                Eq_List = self.Get_Connected_Eq(Start, OutNode[0], Ignore_List, Eq_List)
        return Eq_List



    # RECURENT IMPLEMENTATION
    # Function that gets a number of unknown variable of equation with UO = 1
    # (WILL WORK INPROPER ON EQ WITH UO != 1)
    # Instruction 1: Var_Node_Number = sum of var_node_number of connected nodes for not variables
    # Instruction 2: Var_node_number = None if the variable is known and its node number if the variable is known
    # Instruction 3: Stop the algorithm at constants (equations are allowed cause
    # no 2 equations are connected with each other without the variable inbetween)
    # Ignore list is the list of nodes that were inspected before (to stop the algorithm to go back)
    def Find_Var_Node(self, NodeNum, Ignore_List=[]):
        Ignore_List.append(NodeNum)
        Var_Node = None # number of the variable node
        AllowedTypes = ['MG','ABS','PG','E','SIN','COS']
        # If the node is an unknown variable:
        if self.G.nodes[NodeNum]['type'] == 'V':
            if self.G.nodes[NodeNum]['known'] == False:
                return NodeNum
        # Otherwise:
        elif (self.G.nodes[NodeNum]['type'] in AllowedTypes):
            # Look for neighbors
            for i in self.G.predecessors(NodeNum):
                # That were not sampled (when the var node is still unknown)
                if not (i in Ignore_List) and not Var_Node:
                    Var_Node = self.Find_Var_Node(i,Ignore_List)
        return Var_Node



    # RECURENT IMPLEMENTATION
    # Parsing of the equation on the node number E_number (recurrent implementation)
    # Instruction 1: Equation(equation node which is not a variable) = Sum (w_i * Equation_i),
    # where i are the neighbours
    # Instruction 2: Equation(known variable) is its value
    # Instruction 3: Equation(not known variable) is the variable itself
    # Instruction 4: Equation(Multiplication gate) = Product of w_i f_i,
    # where i are the neighbours
    # Instruction 5: Equation(Power gate) = w_1 f_1 ** (w_2 f_2),
    # where 1 and 2 are the neighbours, number of the base is located in the power gate atribute 'base'
    # Instruction 6: Equation(ABS gate) = abs(neighbour)
    # Ignore list is the list of nodes that were inspected before (to stop the algorithm to go back)
    def Parse_Eq(self, NodeNum, Ignore_List=[]):
        Ignore_List.append(NodeNum)
        ConstantNodes = ['C','I']
        # If the node is a variable:
        if self.G.nodes[NodeNum]['type'] == 'V':
            Symbolic_Eq = self.G.nodes[NodeNum]['SY_Var']
            if self.G.nodes[NodeNum]['known'] == False:
                Numeric_Eq = self.G.nodes[NodeNum]['SY_Var']
                Symbolic_Repr = self.G.nodes[NodeNum]['SY_Var']
            else:
                Numeric_Eq = self.G.nodes[NodeNum]['value']
                Symbolic_Repr = self.G.nodes[NodeNum]['SY_Var']
        # If the node is a constant:
        elif self.G.nodes[NodeNum]['type'] in ConstantNodes:
            Numeric_Eq = self.G.nodes[NodeNum]['value']
            Symbolic_Eq = self.G.nodes[NodeNum]['value']
            Symbolic_Repr = self.G.nodes[NodeNum]['value']
        # If the node is a sinus:
        elif self.G.nodes[NodeNum]['type'] == 'SIN':
            for i in self.G.in_edges(NodeNum):
                for j in i:
                    if not (j in Ignore_List):
                        PartialEquation = self.Parse_Eq(j, Ignore_List)
                        Numeric_Eq = sy.sin(PartialEquation[0])
                        Symbolic_Eq = sy.sin(PartialEquation[1])
                        Symbolic_Repr = sy.sin(PartialEquation[2])
        # If the node is a cosinus:
        elif self.G.nodes[NodeNum]['type'] == 'COS':
            for i in self.G.in_edges(NodeNum):
                for j in i:
                    if not (j in Ignore_List):
                        PartialEquation = self.Parse_Eq(j, Ignore_List)
                        Numeric_Eq = sy.cos(PartialEquation[0])
                        Symbolic_Eq = sy.cos(PartialEquation[1])
                        Symbolic_Repr = sy.cos(PartialEquation[2])
        elif self.G.nodes[NodeNum]['type'] == 'ABS':
            for i in self.G.in_edges(NodeNum):
                for j in i:
                    if not (j in Ignore_List):
                        PartialEquation = self.Parse_Eq(j, Ignore_List)
                        Numeric_Eq = abs(PartialEquation[0])
                        Symbolic_Eq = abs(PartialEquation[1])
                        Symbolic_Repr = abs(PartialEquation[2])
        # If the node is an equation:
        elif self.G.nodes[NodeNum]['type'] == 'E':
            Numeric_Eq = 0
            Symbolic_Eq = 0
            Symbolic_Repr = 0
            for i in self.G.in_edges(NodeNum):
                for j in i:
                    if not (j in Ignore_List):
                        Ignore_List = [NodeNum]
                        PartialEquation = self.Parse_Eq(j, Ignore_List)
                        Numeric_Eq += self.G.edges[i]['weight'] * PartialEquation[0]
                        Symbolic_Eq += self.G.edges[i]['weight'] * PartialEquation[1]
                        Symbolic_Repr += self.G.edges[i]['weight'] * PartialEquation[2]
        # If the node is a multiplication gate:
        elif self.G.nodes[NodeNum]['type'] == 'MG':
            Numeric_Eq = 1
            Symbolic_Eq = 1
            Symbolic_Repr = 1
            for (j,i) in self.G.in_edges(NodeNum):
                if not (j in Ignore_List):
                    PartialEquation = self.Parse_Eq(j, Ignore_List)
                    Numeric_Eq *= self.G.edges[j,i]['weight'] * PartialEquation[0]
                    Symbolic_Eq *= self.G.edges[j,i]['weight'] * PartialEquation[1]
                    Symbolic_Repr *= self.G.edges[j,i]['weight'] * PartialEquation[2]
        # If the node is a summation gate:
        elif self.G.nodes[NodeNum]['type'] == 'SG':
            Numeric_Eq = 0
            Symbolic_Eq = 0
            Symbolic_Repr = 0
            for (j,i) in self.G.in_edges(NodeNum):
                if not (j in Ignore_List):
                    PartialEquation = self.Parse_Eq(j, Ignore_List)
                    Numeric_Eq += self.G.edges[j,i]['weight'] * PartialEquation[0]
                    Symbolic_Eq += self.G.edges[j,i]['weight'] * PartialEquation[1]
                    Symbolic_Repr += self.G.edges[j,i]['weight'] * PartialEquation[2]
        # If the node is a power gate:
        elif self.G.nodes[NodeNum]['type'] == 'PG':
            base = self.G.nodes[NodeNum]['base']
            power = self.G.nodes[NodeNum]['power']
            PartialEquationBase = self.Parse_Eq(base, Ignore_List)
            PartialEquationPower = self.Parse_Eq(power, Ignore_List)
            Numeric_Eq = (self.G.edges[base,NodeNum]['weight'] * PartialEquationBase[0]) ** \
                         (self.G.edges[power, NodeNum]['weight'] * PartialEquationPower[0])
            Symbolic_Eq = (self.G.edges[base,NodeNum]['weight'] * PartialEquationBase[1]) ** \
                          (self.G.edges[power, NodeNum]['weight'] * PartialEquationPower[1])
            Symbolic_Repr = (self.G.edges[base,NodeNum]['weight'] * PartialEquationBase[2]) ** \
                            (self.G.edges[power, NodeNum]['weight'] * PartialEquationPower[2])
        return Numeric_Eq, Symbolic_Eq, Symbolic_Repr



    # Solver for the parsed equation (based on sympy)
    def Solve_Eq(self, Eq_Node, Var_Node):
        (Numeric_Eq, Symbolic_Eq, Symbolic_Repr) = self.Parse_Eq(Eq_Node, Ignore_List=[])
        if self.Trace or self.Debug: print('Equation: ',Symbolic_Eq, '= 0')
        # Solve the equation
        Solution = sy.solvers.solve(Numeric_Eq,self.G.nodes[Var_Node]['SY_Var'])
        Symb_Solution = sy.solvers.solve(Symbolic_Repr,self.G.nodes[Var_Node]['SY_Var'])
        # If the variable node is non negative delete all negative solutions
        if 'positive' in self.G.nodes[Var_Node]:
            Solution = [i for i in Solution if i>0]
        Symb_Solution = sy.simplify(Symb_Solution[0])
        if len(Solution) > 1:
            raise Exception('Ambigues solution! Multiple solutions detected')
        if len(Solution) == 0:
            raise Exception('No solution! Probably all solutions were ignored due \
                            to the variable restrictions (only positive, etc)')
        if self.Trace:
            print('Result:', self.G.nodes[Var_Node]['SY_Var'], \
                  '=', Symb_Solution,'= {:.2f}'.format(float(Solution[0])), \
                  self.G.nodes[Var_Node]['unit'].units,'\n')
        if self.Debug:
            print('Result:', self.G.nodes[Var_Node]['SY_Var'], \
                  '=', Symb_Solution,'= {:.2f}'.format(float(Solution[0])), \
                  self.G.nodes[Var_Node]['unit'].units)
        # Update the discovered variable
        self.Update_Var_Solution(Var_Node, float(Solution[0]), Symb_Solution)



    # Solver for the cycle
    def Solve_G_eq_Cycle(self, Cycle, SolutionVarNode):
        # Get the sympy object of the solution variable
        Var = self.G.nodes[SolutionVarNode]['SY_Var']
        # Parse all equations
        NumSystemOfEquations = []
        SymbSystemOfEquations = []
        for i in Cycle:
            (Numeric_Eq, Symbolic_Eq, Symbolic_Repr) = self.Parse_Eq(i, Ignore_List=[])
            NumSystemOfEquations.append(Numeric_Eq)
            SymbSystemOfEquations.append(Symbolic_Repr)
            if self.Trace or self.Debug:
                print('System of equations: ', Symbolic_Eq, '= 0')
        # Solve the system of equations
        Num_Solution = sy.solvers.solve(NumSystemOfEquations)
        Symb_Solution = sy.solvers.solve(SymbSystemOfEquations)
        # Filter the solutions
        if 'positive' in self.G.nodes[SolutionVarNode]:
            Num_Solution_List = []
            for i in range(len(Num_Solution)):
                if Num_Solution[i][Var] > 0:
                    Num_Solution_List.append(Num_Solution[i])
            Num_Solution = Num_Solution_List
        # Check for ambiguity
        if isinstance(Num_Solution, dict):
            # Extract the needed variable from the solution
            Num_Solution = Num_Solution[Var]
            #print Symb_Solution
            if Var in Symb_Solution[0]:
                Symb_Solution = Symb_Solution[0][Var]
            else:
                Symb_Solution = Num_Solution
        else:
            if len(Num_Solution) > 2:
                #print Num_Solution, type(Num_Solution)
                raise Exception('Ambigues solution! Multiple solutions detected')
            # Extract the needed variable from the solution
            Num_Solution = Num_Solution[0][Var]
            Symb_Solution = Symb_Solution[0][Var]
        # Transform the solutions
        if self.Trace:
            print('Result: ', Var, ' = ', Symb_Solution, \
                  ' = {:.2f}'.format(float(Num_Solution)), \
                  self.G.nodes[SolutionVarNode]['unit'].units,'\n')
        if self.Debug:
            print('Result: ', Var, ' = ', Symb_Solution, \
                  ' = {:.2f}'.format(float(Num_Solution)), \
                  self.G.nodes[SolutionVarNode]['unit'].units)
        # Update the variable in the graph
        self.Update_Var_Solution(SolutionVarNode, float(Num_Solution), Symb_Solution)



    # Find unknown variable list of the equation
    def FindVariableList(self, NodeNum, Start, Var_List = [], Ignore_List = []):
        Ignore_List.append(NodeNum)
        AllowedTypes = ['MG','ABS','PG','SIN','COS']
        # Look around in the beginning
        if NodeNum == Start:
            for i in self.G.predecessors(NodeNum):
                Var_List = self.FindVariableList(i, Start,
                                                     Var_List,
                                                     Ignore_List)
        # If the node is an unknown variable:
        elif (self.G.nodes[NodeNum]['type'] == 'V') and not self.G.nodes[NodeNum]['known']:
            Var_List.append(NodeNum)
        # If the node is structural then go in the direction variable:
        elif (self.G.nodes[NodeNum]['type'] in AllowedTypes):
            for i in self.G.predecessors(NodeNum):
                Var_List = self.FindVariableList(i, Start,
                                                 Var_List,
                                                 Ignore_List)
        return Var_List



    # Find shared unknown variable
    def FindSharedUnknownVariable(self,Eq1,Eq2):
        VarList1 = self.FindVariableList(Eq1,Eq1, Var_List = [], Ignore_List = [])
        VarList2 = self.FindVariableList(Eq2,Eq2, Var_List = [], Ignore_List = [])
        for i in VarList1:
            if i in VarList2:
                SharedVariable = i
        return SharedVariable



    # Check whether 2 numerical equaitons are symmetrical
    def Equations_Symmetrical(self, Solution1, Solution2):
        Division = Solution1 / Solution2
        if Division.is_real:
            return Division
        else: return False



    # Symmetry condition on dependent variables
    # In order for two equations to be symmetrical their dependent
    # vaiables have to match except one
    def Symmetry_Condition_On_Variables(self, Var1, Var2):
        Condition = True
        NotMatchingVariableCount = 0
        a = [i for i in Var1 if i not in Var2]
        b = [i for i in Var2 if i not in Var1]
        if (len(a) == 1) and (len(b) == 1):
            return True, a, b
        else: return False, 0, 0



    # RECURENT IMPLEMENTATION
    # Gepredecessorsn
    # Go through all structural nodes until the variable and save it
    def Get_Equation_Variables(self, NodeVar,
                               BagOfVariables = [],
                               Ignore_List = []):
        Ignore_List.append(NodeVar)
        AllowedTypes = ['MG','ABS','PG','E','SIN','COS']
        if self.G.nodes[NodeVar]['type'] == 'V':
            BagOfVariables.append(NodeVar)
            return BagOfVariables
        elif (self.G.nodes[NodeVar]['type'] in AllowedTypes):
            for i in self.G.predecessors(NodeVar):
                BagOfVariables = self.Get_Equation_Variables(i,
                                                             BagOfVariables,
                                                             Ignore_List)
        return BagOfVariables



    # Checks if two given equations are symmetrical (a = f(x) and
    # b = alpha * f(x), where alpha is a constant)
    def Check_For_Symmetry(self, VarNode):
        if self.G_eq.has_node(VarNode):
            # Get the cycles around the fused variable
            Cycles = nx.cycle_basis(self.G_eq,VarNode)
            # Filter only cycles of length 4 and leave only equations
            FourCycles = [x for x in Cycles if len(x) == 4]
            FilteredCycles = []
            for i in FourCycles:
                PotentialPair = [x for x in i if self.G_eq.nodes[x]['type']=='E']
                # Get two equations
                Eq1 = PotentialPair[0]
                Eq2 = PotentialPair[1]
                # Get the list of variables for both equations
                Var1 = self.Get_Equation_Variables(Eq1,
                                               BagOfVariables = [],
                                               Ignore_List = [])
                Var2 = self.Get_Equation_Variables(Eq2,
                                               BagOfVariables = [],
                                               Ignore_List = [])
                # If both equations depend on different ammount of variables then
                # the symmetry condition is automatically broken
                # If the number of dependent variables is equal, then
                # check that for both equations all except one variable (main unknown) are shared
                if len(Var1) == len(Var2):
                    SymmetryCondition = self.Symmetry_Condition_On_Variables(Var1, Var2)
                    if SymmetryCondition[0]:
                        MainUnknown1 = SymmetryCondition[1][0]
                        MainUnknown2 = SymmetryCondition[2][0]
                        # If the condition is satified then solve both equations
                        # in regard of main variable and check whether solutions are linear to each other
                        # First parse the equations
                        (Numeric_Eq1, Symbolic_Eq1, Symbolic_Repr1) = self.Parse_Eq(Eq1,
                                                                                Ignore_List=[])
                        (Numeric_Eq2, Symbolic_Eq2, Symbolic_Repr2) = self.Parse_Eq(Eq2,
                                                                                Ignore_List=[])
                        # Then solve them
                        Solution1 = sy.solvers.solve(Symbolic_Eq1,
                                                 self.G.nodes[MainUnknown1]['SY_Var'])[0]
                        Solution2 = sy.solvers.solve(Symbolic_Eq2,
                                                 self.G.nodes[MainUnknown2]['SY_Var'])[0]
                        # Check the solutions for their linearity
                        SymmetryCoef = self.Equations_Symmetrical(Solution1, Solution2)
                        if SymmetryCoef:
                            self.SymmetryCount += 1
                            EqName = 'SY-' + str(self.SymmetryCount)
                            if self.Debug:
                                print('Connected 2 symmetrical variables', \
                                      MainUnknown1, 'and', MainUnknown2, \
                                      'with equation', EqName, \
                                      '. Symmetry coefitient: ', float(SymmetryCoef))
                            self.G.add_node(EqName, type='E')
                            self.G.add_weighted_edges_from([(MainUnknown1,EqName,-1),
                                                        (MainUnknown2,EqName,float(SymmetryCoef))])



    # # Checks for the symmetry in search for redundant equations
    def Check_For_Symmetry_Wrapper(self):
        return None
        # Cycles = nx.cycle_basis(self.G_eq)
        # FourCycles = [x for x in Cycles if len(x) == 4]
        # FilteredCycles = []
        # for i in FourCycles:
        #     target = [x for x in i if self.G_eq.nodes[i]['type']=='E'])
        #     self.Check_For_Symmetry(**target)



    # Interactive solver
    def Interactive_Solver(self, NodeNum, Start,
                           SolutionVarNode,
                           Ignore_List = [],
                           Distance = 0):
        flag = True
        while flag:
            flag = False
            # Calculate the shorted path and sort the nodes accordingly
            p=nx.shortest_path_length(self.G_eq,source=Start)
            sorted_p = sorted(p.items(), key = lambda i: i[1])
            sorted_eq = [x for x in sorted_p if self.G_eq.nodes[x[0]]['type'] == 'E']
            for i in sorted_eq:
                if self.G_eq.degree(i[0]) == 1:
                    Var_Node = self.Find_Var_Node(i[0], Ignore_List = [])
                    if self.Debug: print('Found a solvable equation:', i[0])
                    self.Solve_Eq(i[0], Var_Node)
                    flag = True
                    # Initial illustration
                    if self.Illustrate:
                        self.Draw(self.Model,
                                  SolutionNode=SolutionVarNode,
                                  Step=self.Illustrate)
                        self.Illustrate += 1




    # Check the final equaion list
    def Check_Eq_List(self, Final_Eq_List, SolutionVarNode):
        Result = None
        for i in Final_Eq_List:
            if len(str(i))>2 and i[:2] == 'FE':
                if self.G.nodes[i]['main'] != SolutionVarNode:
                    Result = self.G.nodes[i]['main']
        return Result



    # Interactive solver wrapper
    def Interactive_Solver_Wrapper(self, SolutionVarNode):
        # Find the list of equations dependent on the solution variable
        # (solution of any of them will solve the problem)
        Final_Eq_List = self.Get_Connected_Eq(SolutionVarNode,
                                              SolutionVarNode,
                                              Ignore_List=[],
                                              Eq_List = [])
        if self.Debug:
            print('Equations giving solution:', Final_Eq_List)
        #print(self.G.nodes(data = True))
        for i in Final_Eq_List:
            if not self.G.nodes[SolutionVarNode]['known']:
                if self.Debug:
                    print('Attempting to solve through the equation', i)
                self.Interactive_Solver(i, i, SolutionVarNode,
                                        Ignore_List=[],
                                        Distance=0)
                if self.Debug:
                    if self.G.nodes[SolutionVarNode]['known']:
                        print('Problem solved through the equation', i)
                    else:
                        print('Unfortunately eguation', i, 'was not solved.')
                if not self.G.nodes[SolutionVarNode]['known']:
                    (Cycles, CycleExist) = self.CheckCycle_G_eq(i, Final_Eq_List)
                    if CycleExist:
                        for i in Cycles:
                            self.Solve_G_eq_Cycle(i, SolutionVarNode)



    # Check for Cycles
    def CheckCycle_G_eq(self, Node, EqList):
        CycleExist = False
        FilteredCycles = []
        # Make a subgraph with only equations with UO of 2
        HelperGraph = self.G_eq.copy()
        for i in self.G_eq.nodes():
            if (HelperGraph.nodes[i]['type'] == 'E') and (HelperGraph.degree(i) != 2):
                HelperGraph.remove_node(i)
        Cycles = nx.cycle_basis(HelperGraph)
        if Cycles:
            CycleExist = True
            for i in Cycles:
                FilteredCycles.append([x for x in i if HelperGraph.nodes[x]['type']=='E'])
        return (FilteredCycles, CycleExist)



    # Interactive solving (lets specify the variable node, important for
    # complex models (multiple connected graphs)):
    def Interactive_Solving_Hidden(self, VarNode=None, VarName=None):
        # Find the node corresponding for the solution variable
        if VarNode:
            SolutionVarNode = VarNode
        elif VarName:
            SolutionVarNode = self.Find_Node_By_Var_Name(VarName)
        if SolutionVarNode:
            if self.Debug: print('Solution variable:', SolutionVarNode)
            # Switch on the edges that are controled by this node (if available)
            if 'EnableSwitch' in self.G.nodes[SolutionVarNode]:
                SwitchNode = self.G.nodes[SolutionVarNode]['EnableSwitch']
                if self.G.nodes[SwitchNode]['Enabled'] == False:
                    self.G.nodes[SwitchNode]['Enabled'] = True
                    self.G.add_weighted_edges_from(self.G.nodes[SwitchNode]['EnableNodes'])
                    if self.Debug:
                        print('SWITCH GATE triggered upon solver initialisation. \
                              Swithing on the following edges:', \
                              self.G.nodes[SwitchNode]['EnableNodes'])
        # If the node was not found then raise an exception
        else:
            raise Exception('Please, identify either the solution variable node \
                            or solution variable name')
        # Initialyse G_eq
        if not self.Initialysed_G_eq:
            self.Zero_Import_Wrapper()
            self.Initialysed_G_eq = True
            self.Make_G_Eq()
            self.Check_For_Symmetry_Wrapper()
            self.Make_G_Eq()
        # Solve the problem for the solution node
        Final_Eq_List = self.Get_Connected_Eq(SolutionVarNode,
                                              SolutionVarNode,
                                              Ignore_List=[],
                                              Eq_List = [])
        # Initial illustration
        if self.Illustrate:
            self.Draw(self.Model,
                      SolutionNode=SolutionVarNode,
                      Step=self.Illustrate)
            self.Illustrate += 1
        Returgeting = self.Check_Eq_List(Final_Eq_List, SolutionVarNode)
        if Returgeting:
            self.Interactive_Solver_Wrapper(Returgeting)
        self.Interactive_Solver_Wrapper(SolutionVarNode)
        # If problem solved (solution node known) then return the results
        if self.G.nodes[SolutionVarNode]['known'] == True:
            if self.Trace or self.Debug:
                if self.G.nodes[SolutionVarNode]['unit'].units != 1:
                    print('Solution: ', VarName, \
                          ' = {:.2f}'.format(self.G.nodes[SolutionVarNode]['value']), \
                          self.G.nodes[SolutionVarNode]['unit'].units, '\n')
                    return self.G.nodes[SolutionVarNode]['value']* \
                           self.G.nodes[SolutionVarNode]['unit'].units
                else:
                    print('Solution: ', VarName, \
                          ' = {:.2f}'.format(self.G.nodes[SolutionVarNode]['value']), '\n')
                    return self.G.nodes[SolutionVarNode]['value']
            else:
                return self.G.nodes[SolutionVarNode]['value']
                #if self.G.nodes[SolutionVarNode]['unit'].units != 1:
                #    return self.G.nodes[SolutionVarNode]['value']* \
                #           self.G.nodes[SolutionVarNode]['unit'].units
                #else:
                #   return self.G.nodes[SolutionVarNode]['value']
        # If problem not solved then return the following message
        else: return 'The problem was not solved. Additional input data is required'



    # Interactive solcing for the user (does not let the user to set the VarNode):
    def Interactive_Solving(self, VarName):
        return self.Interactive_Solving_Hidden(VarName=VarName)
