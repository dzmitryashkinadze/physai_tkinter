import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from math import sqrt
import networkx as nx
import sqlite3
import os
import physai as PhysAI
import pint # for the unit check
#from backend import GraphSolver

class MainApplication(tk.Frame):
    def __init__(self, parent, scaleFactor, conn, *args, **kwargs):
        # Initialyze the frame
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        ###################### COLOR BLOCK ##################
        self.colors = {
            'bg':'#373836', # main background color,
            'bg_active':'#414240', # active background color (lines, selected)
            'edge_p': '#82CE82', # postive edge
            'edge_n': '#f38181', # postive edge
            'var_sol': '#B461E8', # solution variable
            'var_known': '#DB913D', # known variable / constant
            'var_unknown': '#2D91BC', # unknown variable
            'indicator': '#E124E8' # indicator tool
        }
        #####################################################

        # Connection to the DB
        self.conn = conn
        self.parent.configure(background=self.colors['bg'])
        # create a registry object for calculations with units
        self.ureg = pint.UnitRegistry()
        # Hypervariables
        self.grid = True
        self.NodeLabels = False
        self.EdgeLabels = False
        self.scaleFactor = scaleFactor
        self.variable_r = 14*self.scaleFactor
        self.Padding_between_buttons = 5*self.scaleFactor
        self.canvas_width = int(550*self.scaleFactor)
        self.canvas_height = int(950*self.scaleFactor)
        self.grid_spacing = int(50*self.scaleFactor)
        # Add the geometry and labels
        geometry = str(self.canvas_width) + 'x' + str(self.canvas_height)
        self.parent.geometry(geometry)
        # Add problem text section
        self.ProblemText = tk.Message(self.parent, text = "", width = int(510*self.scaleFactor))
        self.ProblemText.config(font = ("Courier",
                                        int(12*self.scaleFactor)),
                                foreground='white')
        self.ProblemText.pack(side='top', expand = 'yes')
        self.ProblemText.configure(background=self.colors['bg'])
        # Popup dictionary gives the instructions about the information
        # that is asked at the popup
        self.popupDictionary = {'V1': [{'Label': 'Variable name',
                                        'Entry':'SY_Var'},
                                       {'Label': 'Variable unit',
                                        'Entry':'unit'}],
                                'C1': [{'Label': 'Constant name',
                                        'Entry':'SY_Var'},
                                       {'Label': 'Constant value',
                                        'Entry':'value'},
                                       {'Label': 'Constant unit',
                                        'Entry':'unit'}],
                                'Edge3': [{'Label': 'Edge weight',
                                           'Entry':'weight'}]}
        self.popupStateChange = {'V1': 'V',
                                 'C1': 'C',
                                 'Edge3': ''}
        # Add node images to Memory
        self.indicator = tk.PhotoImage(file='GraphicElements/Indicator.gif')
        self.I_gif = tk.PhotoImage(file='GraphicElements/NodeImage/Constant1.gif')
        self.PG1_gif = tk.PhotoImage(file='GraphicElements/NodeImage/PowerGate11.gif')
        self.PB_gif = tk.PhotoImage(file='GraphicElements/NodeImage/PowerBase.gif')
        self.PG3_gif = tk.PhotoImage(file='GraphicElements/NodeImage/PowerGate3.gif')
        self.P4_gif = tk.PhotoImage(file='GraphicElements/NodeImage/PowerGate4.gif')
        self.SG_gif = tk.PhotoImage(file='GraphicElements/NodeImage/SummationGate1.gif')
        self.MG_gif = tk.PhotoImage(file='GraphicElements/NodeImage/MultiplicationGate1.gif')
        self.Eq_gif = tk.PhotoImage(file='GraphicElements/NodeImage/Equation1.gif')
        self.SW_gif = tk.PhotoImage(file='GraphicElements/NodeImage/SwitchNoBackground.gif')
        self.SW_Edge_gif = tk.PhotoImage(file='GraphicElements/NodeImage/SwitchEdgeNoBackground.gif')
        self.Filter_gif = tk.PhotoImage(file='GraphicElements/NodeImage/Filter1.gif')
        self.Filter_tan = tk.PhotoImage(file='GraphicElements/NodeImage/TAN1.gif')
        self.Filter_cos = tk.PhotoImage(file='GraphicElements/NodeImage/COS1.gif')
        self.Filter_sin = tk.PhotoImage(file='GraphicElements/NodeImage/SIN1.gif')
        self.EraseNode = tk.PhotoImage(file = "GraphicElements/EraseNode.gif")
        self.EraseEdge = tk.PhotoImage(file = "GraphicElements/EraseEdge.gif")
        self.imageTool1 = tk.PhotoImage(file = "GraphicElements/EdgeP1.gif")
        self.imageTool2 = tk.PhotoImage(file = "GraphicElements/EdgeN1.gif")
        self.Filter_abs = tk.PhotoImage(file = "GraphicElements/NodeImage/ABS1.gif")
        self.cursor_gif = tk.PhotoImage(file = 'GraphicElements/Cursor.gif')
        self.skills_gif = tk.PhotoImage(file = 'GraphicElements/rucksack.gif')
        self.fusion_gif = tk.PhotoImage(file = 'GraphicElements/fusion.gif')
        # Node gif dictionary
        self.NodeGifDict = {'I': self.I_gif,
                            'PG': self.PG1_gif,
                            'SG': self.SG_gif,
                            'MG': self.MG_gif,
                            'E': self.Eq_gif,
                            'SWITCH': self.SW_gif,
                            'ABS': self.Filter_abs,
                            'SIN': self.Filter_sin,
                            'COS': self.Filter_cos,
                            'TAN': self.Filter_tan,
                            'PEI': self.PB_gif}
        # Initialyze the graph
        self.G = nx.DiGraph()
        # State of the generator
        self.State = ''
        # Window title
        self.parent.title('Content maker')
        # Define a menu
        menubar = tk.Menu(self.parent)
        # create a pulldown menu File
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label='Open problem',
                             command=self.OpenProblem)
        filemenu.add_command(label='Save problem as',
                             command=self.WriteProblem)
        filemenu.add_command(label='Open skill',
                             command=self.OpenSkill)
        filemenu.add_command(label='Save skill as',
                             command=self.WriteSkill)
        filemenu.add_command(label='Delete',
                             command=self.DeleteProblem)
        filemenu.add_command(label='Exit',
                             command=self.escapeApp)
        menubar.add_cascade(label='File', menu=filemenu)
        # create a pulldown menu Edit
        editmenu = tk.Menu(menubar, tearoff=0)
        editmenu.add_command(label='Problem text',
                             command=self.editText)
        editmenu.add_command(label='Tools',
                             command=self.editTools)
        editmenu.add_command(label='Erase edge',
                             command= lambda: self.StartAction('EraseEdge'))
        editmenu.add_command(label='Erase node',
                             command= lambda: self.StartAction('EraseNode'))
        editmenu.add_command(label='Variable',
                             command= lambda: self.StartAction('EditVariable'))
        editmenu.add_command(label='Constant',
                             command= lambda: self.StartAction('EditConstant'))
        editmenu.add_command(label='Equation',
                             command= lambda: self.StartAction('EditEquation'))
        editmenu.add_command(label='Bundle',
                             command= self.EditBundle)
        menubar.add_cascade(label='Edit', menu=editmenu)
        # create a pulldown menu Add
        addmenu = tk.Menu(menubar, tearoff=0)
        addmenu.add_command(label='Positive edge',
                             command= lambda: self.UserAddElement('EdgeP1'))
        addmenu.add_command(label='Negative edge',
                             command= lambda: self.UserAddElement('EdgeN1'))
        addmenu.add_command(label='Equation node',
                             command= lambda: self.UserAddElement('E'))
        addmenu.add_command(label='Multiplication gate',
                             command= lambda: self.UserAddElement('MG'))
        addmenu.add_command(label='Summation gate',
                             command= lambda: self.UserAddElement('SG'))
        addmenu.add_command(label='Power gate',
                             command= lambda: self.UserAddElement('PG'))
        addmenu.add_command(label='Indicator edge',
                             command= lambda: self.StartAction('Indicator'))
        addmenu.add_command(label='Sinus filter',
                             command= lambda: self.UserAddElement('SIN'))
        addmenu.add_command(label='Cosinus filter',
                             command= lambda: self.UserAddElement('COS'))
        addmenu.add_command(label='Constant One Node',
                            command= lambda: self.UserAddElement('I'))
        addmenu.add_command(label='ABS Filter',
                            command= lambda: self.UserAddElement('ABS'))
        addmenu.add_command(label='TAN Filter',
                            command= lambda: self.UserAddElement('TAN'))
        addmenu.add_command(label='Variable Fusion',
                            command= lambda: self.StartAction('Fusion1'))
        addmenu.add_command(label='Node Labels',
                            command= self.SwitchNodeLabels)
        addmenu.add_command(label='Graph Log',
                            command= self.GraphLog)
        addmenu.add_separator()
        addmenu.add_command(label='Variable Node',
                            command= lambda: self.AddVariable())
        addmenu.add_command(label='Named Constant Node',
                            command= lambda: self.AddConstant())
        addmenu.add_command(label='Skill graph',
                            command= lambda: self.AddSkill())
        menubar.add_cascade(label='Add', menu=addmenu)
        # Bind the functionality for relocation of the graph
        self.parent.bind("<Shift-Up>", lambda event: self.MoveSkillGraph(1))
        self.parent.bind("<Shift-Down>", lambda event: self.MoveSkillGraph(2))
        self.parent.bind("<Shift-Left>", lambda event: self.MoveSkillGraph(3))
        self.parent.bind("<Shift-Right>", lambda event: self.MoveSkillGraph(4))
        # Bind the functionality for adjusting of variable radius
        #self.parent.bind("<Control-Up>", lambda event: self.Change_Var_r(1.1))
        #self.parent.bind("<Control-Down>", lambda event: self.Change_Var_r(0.9))
        # display the menu
        self.parent.config(menu=menubar)

        # initialize toolbar
        self.toolbar = tk.Frame(self.parent, borderwidth=1, width = int(510*self.scaleFactor))

        self.tool_container = tk.Frame(self.toolbar)
        self.tool_container.pack(side = 'left', fill='x')

        CheckButton = HoverButton(self.toolbar,
                                text="CHECK",
                                background = self.colors['bg'],
                                activebackground = self.colors['bg_active'],
                                foreground = 'white',
                                highlightbackground= self.colors['bg_active'],
                                command= self.FinalCheck)
        CheckButton.pack(side='right',padx=(5*self.scaleFactor))

        ResetButton = HoverButton(self.toolbar,
                                text="RESET",
                                background = self.colors['bg'],
                                activebackground = self.colors['bg_active'],
                                foreground = 'white',
                                highlightbackground= self.colors['bg_active'],
                                command= self.ResetProblem)
        ResetButton.pack(side='right',padx=(5*self.scaleFactor))

        self.toolbar.pack(side = 'top', fill='x')
        self.toolbar.configure(background = self.colors['bg'])


        # initialyze canvas
        self.canvas = tk.Canvas(self.parent,
                                width=self.canvas_width,
                                height=self.canvas_height,
                                highlightthickness=1,
                                highlightbackground=self.colors['bg_active'])
        #self.canvas.configure(background='white')
        self.canvas.pack()
        self.canvas.configure(background = self.colors['bg'])
        # Not visible widgets that work with events
        #self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind('<Motion>', self.motion)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drop)
        #self.canvas.configure(cursor="hand1")
        # Make the grid lines
        self.checkered(self.canvas, self.grid_spacing)
        self.NumberOfAliases = 0
        self.AliasProtection = False
        self.ProblemNumber = 1
        self.InitialyzeUI(1)

    def ResetProblem(self):
        self.InitialyzeUI(self.ProblemDATA[0])
        print('Problem reseted')

    def GraphLog(self):
        print('###############  NODES  #################')
        print(self.G.nodes(data = True))
        print('###############  EDGES  #################')
        print(self.G.edges(data = True))

    def MoveSkillGraph(self, direction):
        if self.State == 'MoveSkillGraphState':
            if direction == 1:
                dx = 0
                dy = -1
            elif direction == 2:
                dx = 0
                dy = 1
            elif direction == 3:
                dx = -1
                dy = 0
            elif direction == 4:
                dx = 1
                dy = 0
            # Figure out if the move is valid (does not intersect with other elements of graph)
            COLLISION = False
            for i in range(self.StartSkillGraph,len(self.G)+1):
                newX = self.G.nodes[i]['xpos'] + dx
                newY = self.G.nodes[i]['ypos'] + dy
                for j in range(1,self.StartSkillGraph):
                    if ('xpos' in self.G.nodes[j]) and \
                       (newX == self.G.nodes[j]['xpos']) and \
                       (newY == self.G.nodes[j]['ypos']):
                        COLLISION = True
            if not COLLISION:
                for i in range(self.StartSkillGraph,len(self.G)+1):
                    self.G.nodes[i]['xpos'] += dx
                    self.G.nodes[i]['ypos'] += dy
                self.update_canvas()
            else:
                messagebox.showerror('Error!', 'Place occupied by other elements of graph!')

    def SwitchNodeLabels(self):
        self.NodeLabels = not self.NodeLabels
        self.update_canvas()

    def EditBundle(self):
        oldState = []
        oldState.append(self.ProblemDATA[4])
        newBundle = BundleDialog(self.parent, oldState = oldState)
        if newBundle.result:
            self.ProblemDATA[4] = newBundle.result


    def updateEq(self,NodeSelected):
        oldState = []
        if 'ExpectedParsing' in self.G.nodes[NodeSelected]:
            oldState.append(1)
            oldState.append(self.G.nodes[NodeSelected]['ExpectedParsing'])
        else:
            oldState.append(0)
            oldState.append('')
        VarParams = EqDialog(self.parent, oldState = oldState)
        if VarParams.result:
            if VarParams.result[0] == 1:
                self.G.nodes[NodeSelected]['ExpectedParsing'] = VarParams.result[1]
            elif 'ExpectedParsing' in self.G.nodes[NodeSelected]:
                del self.G.nodes[NodeSelected]['ExpectedParsing']


    def AskNextLevel(self):
        FullMessage = '\nThis is correct!\nDo you want to go to the next problem?'
        MsgBox = tk.messagebox.askquestion('Correct!',FullMessage, icon='info')
        if MsgBox == 'yes':
            self.InitialyzeUI(self.ProblemDATA[0]+1)


    def FinalCheck(self):
        StructureCheck = self.CheckGraph()
        if StructureCheck[0]:
            Checker = PhysAI.GraphSolver(Graph = self.G)
            result = Checker.Check()
            if result['Solved']:
                self.AskNextLevel()
            else:
                print(result['Error'])
                FullMessage = 'Your are wrong!'
                messagebox.showinfo('TRY HARDER!', FullMessage)
        else:
            messagebox.showerror('WRONG GRAPH!', StructureCheck[1])


    def AddSkill(self):
        maxSKILL = self.ProblemDATA[21]
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM SKILLS WHERE ID <= {};".format(maxSKILL))
        try:
            skills = list(cursor.fetchall())
            LoadSuccess = True
        except:
            LoadSuccess = False
        if LoadSuccess and (len(skills)>0):
            SelectedSkill = SkillDialog(self.parent, oldState = skills)
            if SelectedSkill.result:
                self.AppendSkillGraph(SelectedSkill.result)
        else:
            messagebox.showerror('Error!', 'Skill DB empty or not available!')


    def getGraphCage(self,Graph):
        top=-1
        right=-1
        bottom=100
        left=100
        for i in Graph.nodes():
            if Graph.nodes[i]['xpos']<left:
                left = Graph.nodes[i]['xpos']
            if Graph.nodes[i]['xpos']>right:
                right = Graph.nodes[i]['xpos']
            if Graph.nodes[i]['ypos']<bottom:
                bottom = Graph.nodes[i]['ypos']
            if Graph.nodes[i]['ypos']>top:
                top = Graph.nodes[i]['ypos']
        return [top,bottom,right,left]


    def AppendSkillGraph(self, skillPath):
        # Load the graph
        GraphToAppend = nx.read_graphml(skillPath)
        GraphToAppend = self.G_Remaping(GraphToAppend)
        print('Loaded skill', skillPath)
        # Adapt and position the skill graph inside main problem graph
        # Remaping
        Remaping = {}
        NodeList = []
        start = len(self.G) +1
        self.StartSkillGraph = start
        # get the node list
        for i in GraphToAppend.nodes():
            NodeList.append(i)
        # create Remaping and backmaping to correct for the deleted node
        for i in range(len(GraphToAppend)):
            Remaping[NodeList[i]] = i + start
        # Relabel the node names
        GraphToAppend = nx.relabel_nodes(GraphToAppend, Remaping)
        # Shift the graph elements down
        # solely for visualizatoin purposes
        G_Cage = self.getGraphCage(self.G)
        ToAppend_Cage = self.getGraphCage(GraphToAppend)
        V_Shift = G_Cage[0] - ToAppend_Cage[1] + 1
        for i in GraphToAppend.nodes():
            GraphToAppend.nodes[i]['ypos'] += V_Shift
        # Increment the variables of the graph copy ending on the number
        # Example: x1 --> x2 (first alias) x1 --> x3 (second alias)
        # Keep track of renamed variables for later fusion
        #AcceptableEnding = ['0','1','2','3','4','5','6','7','8']
        for i in GraphToAppend.nodes(data = 'type'):
            if i[1] == 'PG':
                GraphToAppend.nodes[i[0]]['power'] = Remaping[GraphToAppend.nodes[i[0]]['power']]
                #if (GraphToAppend.nodes[i[0]]['base']+start) in ProtectedList:
                #    GraphToAppend.nodes[i[0]]['base'] = Remaping[GraphToAppend.nodes[i[0]]['base']] - start
                #else:
                #    GraphToAppend.nodes[i[0]]['base'] = Remaping[GraphToAppend.nodes[i[0]]['base']]
                #if (GraphToAppend.nodes[i[0]]['power']+start) in ProtectedList:
                #    GraphToAppend.nodes[i[0]]['power'] = Remaping[GraphToAppend.nodes[i[0]]['power']] - start
                #else:
                #    GraphToAppend.nodes[i[0]]['power'] = Remaping[GraphToAppend.nodes[i[0]]['power']]
            #elif i[1] == 'V':
                # Renaming variables
                #VarName = GraphToAppend.nodes[i[0]]['SY_Var']
                #if isinstance(VarName, str) and (VarName[-1] in AcceptableEnding):
                #    Increment = self.NumberOfAliases
                #    NewVarName = VarName[:-1] + str(int(VarName[-1]) + Increment)
                #    GraphToAppend.nodes[i[0]]['SY_Var'] = NewVarName
                # Renaming of switch links in variable nodes (switch node)
        # Merge main graph with horizontal alias
        self.G = nx.compose(self.G, GraphToAppend)
        # update the canvas
        self.State = 'MoveSkillGraphState'
        self.update_canvas()


    def AddConstant(self):
        self.State = 'C1'
        ConstParams = ConstDialog(self.parent)
        if ConstParams.result:
            try:
                test = self.ureg[ConstParams.result[1]]
                self.State = 'C2'
                self.G.add_node(len(self.G)+1, type='C')
                self.G.nodes[len(self.G)]['SY_Var'] = ConstParams.result[0]
                self.G.nodes[len(self.G)]['unit'] = ConstParams.result[1]
                self.G.nodes[len(self.G)]['value'] = ConstParams.result[2]
            except:
                messagebox.showerror('Error!', 'Unit not recognised!')


    def AddVariable(self):
        self.State = 'V1'
        VarParams = VarDialog(self.parent)
        if VarParams.result:
            try:
                test = self.ureg[VarParams.result[1]]
                self.State = 'V2'
                self.G.add_node(len(self.G)+1, type='V')
                self.G.nodes[len(self.G)]['SY_Var'] = VarParams.result[0]
                self.G.nodes[len(self.G)]['unit'] = VarParams.result[1]
                if VarParams.result[2] == 1:
                    self.G.nodes[len(self.G)]['known'] = True
                    self.G.nodes[len(self.G)]['value'] = float(VarParams.result[3])
                    if VarParams.result[4] == 1:
                        messagebox.showerror('Error', 'Solution variable can not be known!')
                        self.G.remove_node(len(self.G))
                        self.State = ''
                elif VarParams.result[4] == 1:
                    self.G.nodes[len(self.G)]['SolutionVar'] = True
                    self.G.nodes[len(self.G)]['ExpectedValue'] = float(VarParams.result[5])
            except:
                messagebox.showerror('Error!', 'Unit not recognised!')


    # Start action specified in action parameter
    def StartAction(self, action):
        self.update_canvas()
        self.State = action


    def motion(self,event):
        StructuralNodes = ['I','MG','SG','E','PG','SWITCH','SIN','COS','ABS','TAN','PEI','V2','C2']
        if self.State in StructuralNodes:
            self.G.nodes[len(self.G)]['xpos'] = event.x / self.grid_spacing
            self.G.nodes[len(self.G)]['ypos'] = event.y / self.grid_spacing
            self.update_canvas()

    def editText(self):
        newText = TextDialog(self.parent,self.ProblemDATA[1])
        # Update the problem text
        if newText.result:
            self.ProblemDATA[1] = newText.result.strip()
            self.ProblemText.configure(text = self.ProblemDATA[1])

    def UpdateToolBox(self):
        # Restore tool container and fill it with tools
        self.tool_container.destroy()
        self.tool_container = tk.Frame(self.toolbar)
        self.tool_container.configure(background = self.colors['bg'])
        self.tool_container.pack(side = 'left', fill='x')
        # Create with new tools
        Tool0 = tk.Button(self.tool_container,
                                 text="Cursor",
                                 image = self.cursor_gif,
                                 bg = self.colors['bg'],
                                 command= lambda: self.StartAction(''))
        Tool0.config(highlightbackground=self.colors['bg_active'])
        Tool0.image = self.cursor_gif
        Tool0.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[5] == 1:
            Tool1 = tk.Button(self.tool_container,
                                     text="Positive Edge",
                                     image = self.imageTool1,
                                     bg = self.colors['bg'],
                                     command= lambda: self.UserAddElement('EdgeP1'))
            Tool1.config(highlightbackground=self.colors['bg_active'])
            Tool1.image = self.imageTool1
            Tool1.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[6] == 1:
            Tool2 = tk.Button(self.tool_container,
                                     text="Negative Edge",
                                     image = self.imageTool2,
                                     bg = self.colors['bg'],
                                     command= lambda: self.UserAddElement('EdgeN1'))
            Tool2.config(highlightbackground=self.colors['bg_active'])
            Tool2.image = self.imageTool2
            Tool2.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[7] == 1:
            Tool3 = tk.Button(self.tool_container,
                                     text="Equation Gate",
                                     image = self.Eq_gif,
                                     bg = self.colors['bg'],
                                     command = lambda: self.UserAddElement('E'))
            Tool3.config(highlightbackground=self.colors['bg_active'])
            Tool3.image = self.Eq_gif
            Tool3.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[8] == 1:
            Tool4 = tk.Button(self.tool_container,
                                     text="Multiplication Gate",
                                     image = self.MG_gif,
                                     bg = self.colors['bg'],
                                     command = lambda: self.UserAddElement('MG'))
            Tool4.config(highlightbackground=self.colors['bg_active'])
            Tool4.image = self.MG_gif
            Tool4.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[9] == 1:
            Tool5 = tk.Button(self.tool_container,
                                     text="Summation Gate",
                                     image = self.SG_gif,
                                     bg = self.colors['bg'],
                                     command = lambda: self.UserAddElement('SG'))
            Tool5.config(highlightbackground=self.colors['bg_active'])
            Tool5.image = self.SG_gif
            Tool5.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[10] == 1:
            Tool6 = tk.Button(self.tool_container,
                                     text="Power Gate",
                                     image = self.PG1_gif,
                                     bg = self.colors['bg'],
                                     command = lambda: self.UserAddElement('PG'))
            Tool6.config(highlightbackground=self.colors['bg_active'])
            Tool6.image = self.PG1_gif
            Tool6.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[11] == 1:
            Tool7 = tk.Button(self.tool_container,
                                     text="Sinus",
                                     image = self.Filter_sin,
                                     bg = self.colors['bg'],
                                     command = lambda: self.UserAddElement('SIN'))
            Tool7.config(highlightbackground=self.colors['bg_active'])
            Tool7.image = self.Filter_sin
            Tool7.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[12] == 1:
            Tool8 = tk.Button(self.tool_container,
                                     text="Cosinus",
                                     image = self.Filter_cos,
                                     bg = self.colors['bg'],
                                     command = lambda: self.UserAddElement('COS'))
            Tool8.config(highlightbackground=self.colors['bg_active'])
            Tool8.image = self.Filter_cos
            Tool8.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[13] == 1:
            Tool9 = tk.Button(self.tool_container,
                                 text="Erase Node",
                                 image = self.EraseNode,
                                 bg = self.colors['bg'],
                                 command= lambda: self.StartAction('EraseNode'))
            Tool9.config(highlightbackground=self.colors['bg_active'])
            Tool9.image = self.EraseNode
            Tool9.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[14] == 1:
            Tool10 = tk.Button(self.tool_container,
                                 text="Erase Edge",
                                 image = self.EraseEdge,
                                 bg = self.colors['bg'],
                                 command= lambda: self.StartAction('EraseEdge'))
            Tool10.config(highlightbackground=self.colors['bg_active'])
            Tool10.image = self.EraseEdge
            Tool10.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[15] == 1:
            Tool11 = tk.Button(self.tool_container,
                                 text="Constant One Node",
                                 image = self.I_gif,
                                 bg = self.colors['bg'],
                                 command= lambda: self.UserAddElement('I'))
            Tool11.config(highlightbackground=self.colors['bg_active'])
            Tool11.image = self.I_gif
            Tool11.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[16] == 1:
            Tool12 = tk.Button(self.tool_container,
                                 text="ABS Filter",
                                 image = self.Filter_abs,
                                 bg = self.colors['bg'],
                                 command= lambda: self.UserAddElement('ABS'))
            Tool12.config(highlightbackground=self.colors['bg_active'])
            Tool12.image = self.Filter_abs
            Tool12.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[17] == 1:
            Tool13 = tk.Button(self.tool_container,
                                 text="TAN Filter",
                                 image = self.Filter_tan,
                                 bg = self.colors['bg'],
                                 command= lambda: self.UserAddElement('TAN'))
            Tool13.config(highlightbackground=self.colors['bg_active'])
            Tool13.image = self.Filter_tan
            Tool13.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[18] == 1:
            Tool14 = tk.Button(self.tool_container,
                                text="Indicator edge",
                                image = self.indicator,
                                bg = self.colors['bg'],
                                command= lambda: self.StartAction('Indicator'))
            Tool14.config(highlightbackground=self.colors['bg_active'])
            Tool14.image = self.indicator
            Tool14.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[19] == 1:
            Tool15 = tk.Button(self.tool_container,
                                text="Skills",
                                image = self.skills_gif,
                                bg = self.colors['bg'],
                                command= self.AddSkill)
            Tool15.config(highlightbackground=self.colors['bg_active'])
            Tool15.image = self.skills_gif
            Tool15.pack(side='left',padx=int(5*self.scaleFactor))
        if self.ProblemDATA[20] == 1:
            Tool15 = tk.Button(self.tool_container,
                                text="Variable Fusion",
                                image = self.fusion_gif,
                                bg = self.colors['bg'],
                                command= lambda: self.StartAction('Fusion1'))
            Tool15.config(highlightbackground=self.colors['bg_active'])
            Tool15.image = self.fusion_gif
            Tool15.pack(side='left',padx=int(5*self.scaleFactor))


    def editTools(self):
        tools = self.ProblemDATA[5:21]
        newTools = ToolDialog(self.parent,tools)
        if newTools.result:
            self.ProblemDATA[5:21] = newTools.result
            self.UpdateToolBox()


    # Initialyzation of the structural node addition algorithm
    def UserAddElement(self, status):
        #if self.State == '':
        self.update_canvas()
        self.State = status
        TriggerNode = ['SWITCH','I','V','C','E','MG','SG','PG','ABS','SIN','COS','PEI','TAN']
        # Trigger addition of node ! Do nothing if its an edge
        if self.State in TriggerNode:
            # add node if status needs it
            self.G.add_node(len(self.G)+1, type=status)
            print('Added node', len(self.G))
            # add value = 1 if its I node
            if status == 'I':
                self.G.nodes[len(self.G)]['value']=1.0

    def updateConst(self,NodeSelected):
        oldState = []
        oldState.append(self.G.nodes[NodeSelected]['SY_Var'])
        oldState.append(self.G.nodes[NodeSelected]['unit'])
        oldState.append(self.G.nodes[NodeSelected]['value'])
        VarParams = ConstDialog(self.parent, oldState = oldState)
        if VarParams.result:
            try:
                test = self.ureg[VarParams.result[1]]
                self.G.nodes[NodeSelected]['SY_Var'] = VarParams.result[0]
                self.G.nodes[NodeSelected]['unit'] = VarParams.result[1]
                self.G.nodes[NodeSelected]['value'] = VarParams.result[2]
            except:
                messagebox.showerror('Error!', 'Unit not recognised!')


    def updateVar(self,NodeSelected):
        oldState = []
        oldState.append(self.G.nodes[NodeSelected]['SY_Var'])
        oldState.append(self.G.nodes[NodeSelected]['unit'])
        if 'value' in self.G.nodes[NodeSelected]:
            oldState.append(1)
            oldState.append(self.G.nodes[NodeSelected]['value'])
        else:
            oldState.append(0)
            oldState.append('')
        if 'ExpectedValue' in self.G.nodes[NodeSelected]:
            oldState.append(1)
            oldState.append(self.G.nodes[NodeSelected]['ExpectedValue'])
        else:
            oldState.append(0)
            oldState.append('')
        VarParams = VarDialog(self.parent, oldState = oldState)
        if VarParams.result:
            try:
                test = self.ureg[VarParams.result[1]]
                self.G.nodes[NodeSelected]['SY_Var'] = VarParams.result[0]
                self.G.nodes[NodeSelected]['unit'] = VarParams.result[1]
                if VarParams.result[2] == 1:
                    self.G.nodes[NodeSelected]['known'] = True
                    self.G.nodes[NodeSelected]['value'] = VarParams.result[3]
                    if VarParams.result[4] == 1:
                        messagebox.showerror('Error', 'Solution variable can not be known!')
                        self.G.remove_node(NodeSelected)
                        self.State = ''
                else:
                    self.G.nodes[NodeSelected]['known'] = False
                    if 'value' in self.G.nodes[NodeSelected]:
                        del self.G.nodes[NodeSelected]['value']
                if VarParams.result[4] == 1:
                    self.G.nodes[NodeSelected]['SolutionVar'] = True
                    self.G.nodes[NodeSelected]['ExpectedValue'] = VarParams.result[5]
                else:
                    self.G.nodes[NodeSelected]['SolutionVar'] = False
                    if 'ExpectedValue' in self.G.nodes[NodeSelected]:
                        del self.G.nodes[NodeSelected]['ExpectedValue']
            except:
                messagebox.showerror('Error!', 'Unit not recognised!')


    def on_press(self, event):
        StructuralNodes = ['I','MG','SG','E','PG','SWITCH','SIN','COS','ABS','TAN','PEI','V2','C2']
        # Get coordinates of the click and round them to the neargest grid point
        x_click = int(round(event.x * 1. / self.grid_spacing))
        y_click = int(round(event.y * 1. / self.grid_spacing))
        # Get the name of the selected node
        NODEFOUND = False
        for (name, content) in self.G.nodes(data = True):
            if ('xpos' in content) and \
               (x_click == content['xpos']) and \
               (y_click == content['ypos']):
                NodeSelected = name
                NODEFOUND = True
        if NODEFOUND:
            if self.State == '':
                self.State = 'DragAndDroping'
                self.NodeBeingDraged = NodeSelected
                self.DragedOldCoord = [x_click,y_click]
            elif self.State == 'EdgeP1':
                if self.G.nodes[NodeSelected]['type'] != 'E':
                    self.EdgeOrigin = NodeSelected
                    self.State = 'EdgeP2'
                else:
                    messagebox.showerror('Error', 'Edge can not start at equation!')
                    self.State = ''
                    self.update_canvas()
            elif self.State == 'EdgeN1':
                if self.G.nodes[NodeSelected]['type'] != 'E':
                    self.EdgeOrigin = NodeSelected
                    self.State = 'EdgeN2'
                else:
                    messagebox.showerror('Error', 'Edge can not start at equation!')
                    self.State = ''
                    self.update_canvas()
            elif self.State == 'EraseNode':
                #self.State = ''
                self.UpdateNodeList(NodeSelected)
                self.update_canvas()
            elif self.State == 'EraseEdge':
                self.State = 'EraseEdge1'
                self.EdgeOrigin = NodeSelected
            elif self.State == 'EditVariable':
                if self.G.nodes[NodeSelected]['type'] == 'V':
                    self.updateVar(NodeSelected)
                    #self.State = ''
                    self.update_canvas()
            elif self.State == 'EditEquation':
                if self.G.nodes[NodeSelected]['type'] == 'E':
                    self.updateEq(NodeSelected)
                    #self.State = ''
                    self.update_canvas()
            elif self.State == 'EditConstant':
                if self.G.nodes[NodeSelected]['type'] == 'C':
                    self.updateConst(NodeSelected)
                    #self.State = ''
                    self.update_canvas()
            elif self.State == 'Indicator':
                if self.G.nodes[NodeSelected]['type'] != 'E':
                    if not ('power' in self.G.nodes[NodeSelected]):
                        self.IndicatedPG = NodeSelected
                        self.State = 'Indicator2'
                    else:
                        messagebox.showerror('Error', 'This power gate already has a power indicator!')
                        self.State = ''
                        self.update_canvas()
                else:
                    messagebox.showerror('Error', 'Indicator must start at power gate!')
                    self.State = ''
                    self.update_canvas()
            elif self.State == 'Fusion1':
                if self.G.nodes[NodeSelected]['type'] == 'V':
                    self.FusedVariable = NodeSelected
                    self.FusedVariableX = self.G.nodes[NodeSelected]['xpos']
                    self.FusedVariableY = self.G.nodes[NodeSelected]['ypos']
                    self.State = 'Fusion2'
                else:
                    messagebox.showerror('Error', 'Only variables can be fused!')
                    self.State = ''
                    self.update_canvas()
        else:
            if self.State in StructuralNodes:
                self.State = ''
                self.G.nodes[len(self.G)]['xpos'] = x_click
                self.G.nodes[len(self.G)]['ypos'] = y_click
                self.update_canvas()


    # Remove a node from node list
    def UpdateNodeList(self,name):
        StructuralNodes = ['MG','SIN','COS','ABS']
        ConstantNodes = ['I','C']
        # maping of the old nodes on new nodes
        Remaping = {}
        NodeList = []
        # remove the node
        self.G.remove_node(name)
        print('Removed node', name)
        # get the node list
        for i in self.G.nodes():
            NodeList.append(i)
        # create Remaping and backmaping to correct for the deleted node
        for i in range(len(NodeList)):
            Remaping[NodeList[i]] = i+1
        # Relabel the node names
        self.G = nx.relabel_nodes(self.G, Remaping)
        # relabel all links in atributes of structural nodes
        for i in self.G.nodes(data = 'type'):
            # Remove a switch trigger atribute from variables if the switch was removed
            if i[1] == 'V':
                if ('EnableSwitch' in self.G.nodes[i[0]]) :
                    if self.G.nodes[i[0]]['EnableSwitch'] == name:
                        del self.G.nodes[i[0]]['EnableSwitch']
                    else:
                        newSwitch = Remaping[self.G.nodes[i[0]]['EnableSwitch']]
                        self.G.nodes[i[0]]['EnableSwitch'] = newSwitch
            if i[1] == 'PG':
                if ('base' in self.G.nodes[i[0]]) and (self.G.nodes[i[0]]['base'] in Remaping):
                    self.G.nodes[i[0]]['base'] = Remaping[self.G.nodes[i[0]]['base']]
                if ('power' in self.G.nodes[i[0]]) and (self.G.nodes[i[0]]['power'] in Remaping):
                    self.G.nodes[i[0]]['power'] = Remaping[self.G.nodes[i[0]]['power']]
        # Check if the node is a switch and if so
        # Remove the Switch attribute from regarded edges
        for i in self.G.edges():
            if ('Switch' in self.G.edges[i]):
                if (self.G.edges[i]['Switch'] == name):
                    del self.G.edges[i]['Switch']
                else:
                    self.G.edges[i]['Switch'] = Remaping[self.G.edges[i]['Switch']]



    def on_drag(self, event):
        if self.State == 'DragAndDroping':
            self.G.nodes[self.NodeBeingDraged]['xpos'] = event.x / self.grid_spacing
            self.G.nodes[self.NodeBeingDraged]['ypos'] = event.y / self.grid_spacing
            self.update_canvas()
        if self.State == 'EdgeP2':
            self.update_canvas()
            self.draw_Hovering_Edge(self.EdgeOrigin,event.x,event.y, col = self.colors['edge_p'])
        if self.State == 'EdgeN2':
            self.update_canvas()
            self.draw_Hovering_Edge(self.EdgeOrigin,event.x,event.y, col = self.colors['edge_n'])
        if self.State == 'EraseEdge1':
            self.update_canvas()
            self.draw_Hovering_Edge(self.EdgeOrigin,event.x,event.y, col = 'red', erasing = True)
        if self.State == 'Indicator2':
            self.update_canvas()
            self.draw_Hovering_Edge(self.IndicatedPG,event.x,event.y, col = self.colors['indicator'])
        if self.State == 'Fusion2':
            self.G.nodes[self.FusedVariable]['xpos'] = event.x / self.grid_spacing
            self.G.nodes[self.FusedVariable]['ypos'] = event.y / self.grid_spacing
            self.update_canvas()


    def on_drop(self, event):
        EdgeStates = ['EdgeP2', 'EdgeN2']
        # Get coordinates of the click and round them to the neargest grid point
        x_drop = int(round(event.x * 1. / self.grid_spacing))
        y_drop = int(round(event.y * 1. / self.grid_spacing))
        OriginNodes = ['V','C','I']
        IndicatorNodes = ['E']
        # Get the name of the selected node
        NODEFOUND = False
        for (name, content) in self.G.nodes(data = True):
            if ('xpos' in content) and \
               (x_drop == content['xpos']) and \
               (y_drop == content['ypos']):
                NodeSelected = name
                NODEFOUND = True
        if NODEFOUND:
            if self.State == 'DragAndDroping':
                self.State = ''
                self.G.nodes[self.NodeBeingDraged]['xpos'] = self.DragedOldCoord[0]
                self.G.nodes[self.NodeBeingDraged]['ypos'] = self.DragedOldCoord[1]
                self.update_canvas()
            elif self.State == 'EdgeP2':
                if (not self.G.nodes[NodeSelected]['type'] in OriginNodes) and (NodeSelected != self.EdgeOrigin):
                    self.State = 'EdgeP1'
                    self.G.add_weighted_edges_from([(self.EdgeOrigin,NodeSelected,1.)])
                    self.update_canvas()
                else:
                    messagebox.showerror('Error', 'Edge can not go to the variable!')
                    self.State = ''
                    self.update_canvas()
            elif self.State == 'EdgeN2':
                if (not self.G.nodes[NodeSelected]['type'] in OriginNodes) and (NodeSelected != self.EdgeOrigin):
                    self.State = 'EdgeN1'
                    self.G.add_weighted_edges_from([(self.EdgeOrigin,NodeSelected,-1.)])
                    self.update_canvas()
                else:
                    messagebox.showerror('Error', 'Edge can not go to the variable!')
                    self.State = ''
                    self.update_canvas()
            if self.State == 'EraseEdge1':
                self.State = 'EraseEdge'
                self.DeleteEdgeFromList(self.EdgeOrigin, NodeSelected)
                self.update_canvas()
            if self.State == 'Indicator2':
                if (self.G.nodes[NodeSelected]['type'] == 'PG') and (NodeSelected != self.IndicatedPG):
                    if self.G.has_edge(self.IndicatedPG,NodeSelected):
                        self.G.remove_edge(self.IndicatedPG,NodeSelected)
                    self.State = 'Indicator'
                    self.G.add_weighted_edges_from([(self.IndicatedPG,NodeSelected,1.0)])
                    self.G.edges[self.IndicatedPG,NodeSelected]['PI'] = True
                    self.update_canvas()
                else:
                    messagebox.showerror('Error', 'Indicator can not go to this node!')
                    self.State = ''
                    self.update_canvas()
            if self.State == 'Fusion2':
                if (self.G.nodes[NodeSelected]['type'] == 'V') and (self.FusedVariable != NodeSelected):
                    self.Fusion(self.FusedVariable,NodeSelected)
                    self.State = 'Fusion1'
                    self.update_canvas()
                else:
                    messagebox.showerror('Error', 'Only variables can be fused!')
                    self.State = ''
                    self.update_canvas()
        else:
            if self.State == 'DragAndDroping':
                self.State = ''
                self.G.nodes[self.NodeBeingDraged]['xpos'] = x_drop
                self.G.nodes[self.NodeBeingDraged]['ypos'] = y_drop
                self.update_canvas()
            if self.State in EdgeStates:
                self.State = ''
                self.update_canvas()
            if self.State == 'EraseEdge1':
                self.State = 'EraseEdge'
                self.update_canvas()
            if self.State == 'Fusion2':
                self.State = ''
                self.G.nodes[self.FusedVariable]['xpos'] = self.FusedVariableX
                self.G.nodes[self.FusedVariable]['ypos'] = self.FusedVariableY
                self.update_canvas()


    def Fusion(self,a,b):
        # Link all of the nodes that were connected to the VarNode2
        # (variable from model 2) to VarNode1 (variable from model 1)
        EdgeList = []
        print('Fusion of variables',a,b)
        # Drag the first variable to the second
        self.G.nodes[a]['xpos'] = self.G.nodes[b]['xpos']
        self.G.nodes[a]['ypos'] = self.G.nodes[b]['ypos']
        # relink it
        for i in self.G.out_edges(b, data='weight'):
            self.G.add_weighted_edges_from([(a, i[1], i[2])])
            # Relink the power gate (base or power) if the variable
            # is linked to PG
            if self.G.nodes[i[1]]['type'] == 'PG':
                #if self.G.nodes[i[1]]['base'] == i[0]:
                #    self.G.nodes[i[1]]['base'] = a
                if self.G.nodes[i[1]]['power'] == i[0]:
                    self.G.nodes[i[1]]['power'] = a
        # Delete the absolete variable
        self.UpdateNodeList(b)
        #self.G.remove_node(b)
        # Renumber the main graph
        #self.G = self.G_Remaping(self.G)

    # Remove an edge from list
    def DeleteEdgeFromList(self,Node1,Node2):
        if self.G.has_edge(Node1,Node2):
            self.G.remove_edge(Node1,Node2)
            print('Removed edge [', Node1,',',Node2,']')
        elif self.G.has_edge(Node2,Node1):
            self.G.remove_edge(Node2,Node1)
            print('Removed edge [', Node2,',',Node1,']')



    def InitialyzeSKILL(self, skillID):
        # Extract the problem
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM SKILLS WHERE ID = {};".format(skillID))
        try:
            self.ProblemDATA = list(cursor.fetchone())
            LoadSuccess = True
        except:
            print('Requested database entry does not exist')
            LoadSuccess = False
        if LoadSuccess:
            # Update the problem text
            self.ProblemText.configure(text = self.ProblemDATA[1])
            # Update the window wm_title
            self.parent.title('Skill #{}'.format(self.ProblemDATA[0]))
            # Update the graph
            GRAPH_PATH = self.ProblemDATA[2]
            if GRAPH_PATH:
                # Load the graph
                self.G = nx.read_graphml(GRAPH_PATH)
                self.G = self.G_Remaping(self.G)
                print('Loaded', GRAPH_PATH)
                # Update tool menu
                #self.UpdateToolBox()
                self.update_canvas()
        else:
            messagebox.showerror('Error', 'DB enty not found!')



    def InitialyzeUI(self, problemID):
        # Extract the problem
        self.State = ''
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM PROBLEMS WHERE ID = {};".format(problemID))
        try:
            self.ProblemDATA = list(cursor.fetchone())
            LoadSuccess = True
        except:
            print('Requested database entry does not exist')
            LoadSuccess = False
        if LoadSuccess:
            # Update the problem text
            self.ProblemText.configure(text = self.ProblemDATA[1])
            # Update the window wm_title
            self.parent.title('Problem #{}'.format(self.ProblemDATA[0]))
            # Update the graph
            GRAPH_PATH = self.ProblemDATA[3]
            if GRAPH_PATH:
                # Load the graph
                self.G = nx.read_graphml(GRAPH_PATH)
                self.G = self.G_Remaping(self.G)
                print('Loaded', GRAPH_PATH)
                # Update tool menu
                self.UpdateToolBox()
                self.update_canvas()
        else:
            messagebox.showerror('Error', 'DB enty not found!')


    # Relabeling of nodes and attributes
    def G_Remaping(self, Graph):
        # Remaping to change node names from str to int
        # and correct skipped nodes ("13","15" etc)
        StructuralNodes = ['MG','SIN','COS','ABS']
        ConstantNodes = ['I','C']
        Remaping = {}
        #IntRemaping = {}
        NodeList = []
        # Create the mapping ("2" --> 2, etc (string to integer in node names))
        for i in Graph.nodes():
            NodeList.append(i)
        for i in range(len(NodeList)):
            Remaping[NodeList[i]] = i+1
            #IntRemaping[int(NodeList[i])] = i+1
        # Relabel the node names
        Graph = nx.relabel_nodes(Graph, Remaping)
        # Convert all of the value attributes to float
        # in case it was wrong in graphml
        for i in Graph.nodes(data = 'type'):
            #if i[1] == 'PG':
            #    Graph.nodes[i[0]]['power'] = IntRemaping[Graph.nodes[i[0]]['power']]
            if i[1] in ConstantNodes:
                Graph.nodes[i[0]]['value'] = float(Graph.nodes[i[0]]['value'])
        # Convert all of the weight attributes to float
        # in case it was wrong in graphml
        for i in Graph.edges():
            Graph.edges[i]['weight'] = float(Graph.edges[i]['weight'])
        return Graph


    def OpenSkill(self):
        # Generate the dialog to chose the file
        self.State = ''
        Filename = filedialog.askopenfilename(initialdir = 'Graphs/Skills/',
                                                   title = 'Select file',
                                                   filetypes = (('graphml files','*.graphml'),
                                                                ('all files','*.*')))
        if Filename:
            keyPos = Filename.find('ContantMaikerGUI/Graphs/Skills/Skill')
            if keyPos != -1:
                start = keyPos + 36
                SkillID = int(Filename[start : start + 3])
                self.InitialyzeSKILL(SkillID)


    def OpenProblem(self):
        # Generate the dialog to chose the file
        self.State = ''
        Filename = filedialog.askopenfilename(initialdir = 'Graphs/Problems/',
                                                   title = 'Select file',
                                                   filetypes = (('graphml files','*.graphml'),
                                                                ('all files','*.*')))
        if Filename:
            keyPos = Filename.find('ContantMaikerGUI/Graphs/Problems/Problem')
            if keyPos != -1:
                start = keyPos + 40
                ProblemID = int(Filename[start : start + 3])
                self.InitialyzeUI(ProblemID)


    def CheckGraph(self):
        GraphValidity = True
        Errors = []
        for i in self.G.nodes():
            if self.CheckNode(i):
                GraphValidity = False
                Errors.append(('Node',self.G.nodes[i],i))
        for i in self.G.edges():
            if self.CheckEdge(i[0],i[1]):
                GraphValidity = False
                Errors.append(('Edge',i))
        return [GraphValidity,Errors]



    def WriteProblem(self):
        #StructureCheck = self.CheckGraph()
        #if StructureCheck[0]:
        self.State = ''
        FilePath = filedialog.asksaveasfilename(initialdir = 'Graphs/Problems/',
                                                defaultextension=".graphml",
                                                filetypes=[('GraphML files', '.graphml'),
                                                           ('all files', '.*')],
                                                title="Choose location")
        if FilePath:
            keyPos = FilePath.find('ContantMaikerGUI/Graphs/Problems/Problem')
            if keyPos != -1:
                # Update problem ID
                start = keyPos + 40
                ProblemID = int(FilePath[start : start + 3])
                self.ProblemDATA[0] = ProblemID
                # Update graph path
                start_path = keyPos + 17
                GraphPath = FilePath[start_path:]
                self.ProblemDATA[3] = GraphPath
                # Write the graph into graphml format
                nx.write_graphml(self.G, GraphPath)
                print('Writen file', GraphPath)
                # Initialyze the cursor
                cursor = self.conn.cursor()
                # Delete old DB entry
                cursor.execute("DELETE FROM PROBLEMS WHERE ID = {};".format(ProblemID))
                # Write a new DB entry
                sqlite_insert = '''INSERT INTO PROBLEMS (
                        ID,
                        TEXT,
                        IMAGE_PATH,
                        GRAPH_PATH,
                        BUNDLE,
                        TOOL_POSITIVE_EDGE,
                        TOOL_NEGATIVE_EDGE,
                        TOOL_EQUATION,
                        TOOL_MULTIPLICATION_GATE,
                        TOOL_SUMMATION_GATE,
                        TOOL_POWER_GATE,
                        TOOL_SINUS,
                        TOOL_COSINUS,
                        TOOL_ERASE_NODE,
                        TOOL_ERASE_EDGE,
                        TOOL_CONSTANT_ONE,
                        TOOL_ABS_FILTER,
                        TOOL_TAN_FILTER,
                        TOOL_POWER_BASE_POINTER,
                        TOOL_SKILLS,
                        TOOL_VAR_FUSION,
                        MAX_TOOL )
                        VALUES
                        (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);'''
                data_tuple = tuple(self.ProblemDATA)
                cursor.execute(sqlite_insert, data_tuple)
                self.conn.commit()
                print('DB written')



    def WriteSkill(self):
        self.State = ''
        FilePath = filedialog.asksaveasfilename(initialdir = 'Graphs/Skills/',
                                                defaultextension=".graphml",
                                                filetypes=[('GraphML files', '.graphml'),
                                                           ('all files', '.*')],
                                                title="Choose location")
        if FilePath:
            keyPos = FilePath.find('ContantMaikerGUI/Graphs/Skills/Skill')
            if keyPos != -1:
                # Update problem ID
                start = keyPos + 36
                SkillID = int(FilePath[start : start + 3])
                #self.ProblemDATA[0] = ProblemID
                # Update graph path
                start_path = keyPos + 17
                GraphPath = FilePath[start_path:]
                self.ProblemDATA[2] = GraphPath
                # Write the graph into graphml format
                nx.write_graphml(self.G, GraphPath)
                print('Writen file', GraphPath)
                #print(GraphPath,self.ProblemDATA)
                # Initialyze the cursor
                cursor = self.conn.cursor()
                # Delete old DB entry
                cursor.execute("DELETE FROM SKILLS WHERE ID = {};".format(SkillID))
                # Write a new DB entry
                sqlite_insert = '''INSERT INTO SKILLS (
                                   ID,
                                   SKILL_DESCRIPTION,
                                   SKILL_GRAPH_PATH )
                                   VALUES
                                   (?,?,?);'''
                data_tuple = tuple((SkillID, self.ProblemDATA[1], GraphPath))
                cursor.execute(sqlite_insert, data_tuple)
                self.conn.commit()
                print('DB written')



    def DeleteProblem(self):
        # Initialyze the cursor
        cursor = self.conn.cursor()
        # Delete old DB entry
        cursor.execute("DELETE FROM PROBLEMS WHERE ID = {};".format(self.ProblemDATA[0]))
        print('Problem {} deleted from DB'.format(self.ProblemDATA[0]))
        # Delete graphml file
        ProblemNumber = str(self.ProblemDATA[0])
        if len(ProblemNumber) == 1:
            ProblemNumber = '00' + ProblemNumber
        elif len(ProblemNumber) == 2:
            ProblemNumber = '0' + ProblemNumber
        path = 'Graphs/Problems/Problem' + ProblemNumber + '.graphml'
        os.remove(path)


    # Closes the application
    def escapeApp(self):
        self.parent.destroy()


    # Redraw the canvas
    def update_canvas(self):
        NamedNodes = ['V','C']
        # Clear the canvas
        self.canvas.delete('all')
        # Make the grid lines
        if self.grid:
            self.checkered(self.canvas, self.grid_spacing)
        # Draw the edges
        for i in self.G.edges():
            if self.G.edges[i]['weight'] > 0:
                self.draw_Edge(i[0],i[1], col = self.colors['edge_p'])
            else:
                self.draw_Edge(i[0],i[1], col = self.colors['edge_n'])
            if 'Switch' in self.G.edges[i]:
                self.draw_Switch_Taget_Edge(self.G.edges[i]['Switch'],
                                            i[0],i[1])
        # Draw the switch edges
        for (name, content) in self.G.nodes(data = True):
            if 'EnableSwitch' in content:
                self.draw_Edge(name,
                               self.G.nodes[name]['EnableSwitch'],
                               trigger=True)
        # Draw nodes ontop of everything
        for (name, content) in self.G.nodes(data = True):
            self.Draw(name)



    # Dashed line from the switch node to the edge it is controlling
    def draw_Switch_Taget_Edge(self, SwitchNode, Node1, Node2):
        # coordinates of the switch node
        x_switch = self.G.nodes[SwitchNode]['xpos'] * self.grid_spacing
        y_switch = self.G.nodes[SwitchNode]['ypos'] * self.grid_spacing
        # coordinates of the nodes spanning the controlled edge
        x0 = self.G.nodes[Node1]['xpos'] * self.grid_spacing
        y0 = self.G.nodes[Node1]['ypos'] * self.grid_spacing
        x1 = self.G.nodes[Node2]['xpos'] * self.grid_spacing
        y1 = self.G.nodes[Node2]['ypos'] * self.grid_spacing
        # coordinates of the controlled edge center
        x_middle = (x0+x1)/2.
        y_middle = (y0+y1)/2.
        # draw the line
        self.canvas.create_line(x_switch, y_switch,
                                x_middle, y_middle,
                                dash=(4,4))
        # draw a circle ontop of the line center
        r_switch = int(self.variable_r / 1.6)
        self.canvas.create_oval(x_middle-r_switch,
                                y_middle-r_switch,
                                x_middle+r_switch,
                                y_middle+r_switch,
                                fill="white")
        # draw a switch gif in the circle
        self.canvas.create_image(x_middle, y_middle, image=self.SW_Edge_gif)


    # Drawing of all nodes
    def Draw(self, NodeName, col = 'black'):
        # Nodes with own illustration
        GifNodes = ['I','MG','SG','E','PG','SWITCH','SIN','COS','ABS','TAN','PEI']
        #GifWithText = ['SIN','COS','ABS','TAN']
        # coordinates of the node
        x = self.G.nodes[NodeName]['xpos'] * self.grid_spacing
        y = self.G.nodes[NodeName]['ypos'] * self.grid_spacing
        # Draw the gif nodes
        if self.G.nodes[NodeName]['type'] in GifNodes:
            if self.G.nodes[NodeName]['type'] == 'SWITCH':
                r_switch = int(self.variable_r / 1.6)
                self.canvas.create_oval(x-r_switch,
                                        y-r_switch,
                                        x+r_switch,
                                        y+r_switch,
                                        fill="white")
            img = self.NodeGifDict[self.G.nodes[NodeName]['type']]
            self.canvas.create_image(x, y, image=img)
            if self.NodeLabels:
                self.canvas.create_text(x,y-12*self.scaleFactor,
                                        text=NodeName,
                                        fill="white")
            #if self.G.nodes[NodeName]['type'] in GifWithText:
                #self.canvas.create_text(x,y,
                #                        text=self.G.nodes[NodeName]['type'])
            #if self.CheckNode(NodeName):
            #    self.canvas.create_text(x,y,
            #                            text='!', fill = 'red')
        else:
            NamedNodes = ['C','V']
            # coordinates of the edges for the node circle
            x0 = x - self.variable_r
            y0 = y - self.variable_r
            x1 = x + self.variable_r
            y1 = y + self.variable_r
            # change the node colour to red if the node is not valid
            #if self.CheckNode(NodeName):
            #   col = 'red'
            if 'ExpectedValue' in self.G.nodes[NodeName]:
                col = self.colors['var_sol']
            elif 'value' in self.G.nodes[NodeName]:
                col = self.colors['var_known']
            else:
                col = self.colors['var_unknown']
            # get the text for the node(its type if its not C or V)
            # or its name if its C or V
            if self.G.nodes[NodeName]['type'] in NamedNodes:
                text = self.G.nodes[NodeName]['SY_Var']
            else:
                text = self.G.nodes[NodeName]['type']
            # draw the node
            self.canvas.create_oval(x0, y0, x1, y1, fill=col, outline= col)
            # insert the text
            self.canvas.create_text(x,y,
                                    text=text,
                                    fill="white")
            # insert the node number
            #self.canvas.create_text(x,y-10,
            #                        text=str(NodeName),
            #                        fill="black")
            # insert the node number above the text
            if self.NodeLabels:
                self.canvas.create_text(x,y-12*self.scaleFactor,
                                        text=NodeName,
                                        fill="white")


    # Drawing of the edge
    def draw_Hovering_Edge(self,Node1,x1,y1,col,erasing = False):
        x0 = self.G.nodes[Node1]['xpos'] * self.grid_spacing
        y0 = self.G.nodes[Node1]['ypos'] * self.grid_spacing
        if erasing:
            self.canvas.create_line(x0,y0,x1, y1, fill=col, dash=(5,5))
        else:
            self.canvas.create_line(x0,y0,x1, y1, fill=col, arrow= tk.LAST)

    # Drawing of the edge
    def draw_Edge(self,
                  Node1,
                  Node2,
                  col='white',
                  trigger=False):
        # trigger flag is for the switch trigger (dashed line)
        # coordinates of the nodes spanning the edge
        x0 = self.G.nodes[Node1]['xpos'] * self.grid_spacing
        y0 = self.G.nodes[Node1]['ypos'] * self.grid_spacing
        x1 = self.G.nodes[Node2]['xpos'] * self.grid_spacing
        y1 = self.G.nodes[Node2]['ypos'] * self.grid_spacing
        # coordinates of the controlled edge center
        shift = 6*self.scaleFactor
        if sqrt((x1-x0)**2 + (y1-y0)**2)>0:
            x_add = shift * (x1-x0) / sqrt((x1-x0)**2 + (y1-y0)**2)
            y_add = shift * (y1-y0) / sqrt((x1-x0)**2 + (y1-y0)**2)
        else:
            x_add = 0
            y_add = 0
        x_middle = (x0+x1)/2. + x_add
        y_middle = (y0+y1)/2. + y_add
        # draw a dashed line if the edge is for the switch trigger
        if trigger:
            self.canvas.create_line(x0, y0,
                                    x1, y1,
                                    fill=col,
                                    dash=(4,4))
        # if its a normal edge
        else:
            # check edge for validity
            if self.CheckEdge(Node1,Node2):
                # change the colour of the edge to red it its invalid
                col = 'red'
            elif self.EdgeLabels and (self.G.edges[Node1,Node2]['weight'] != 1):
                weight = self.G.edges[Node1,Node2]['weight']
                if int(weight) == weight:
                    weight = int(weight)
                self.canvas.create_text(x_middle, y_middle-12,
                                        text=weight,
                                        fill=col)
            # draw the edge
            self.canvas.create_line(x0, y0, x1, y1, fill=col)
            # draw the arrow
            self.canvas.create_line(x0,y0,x_middle, y_middle, fill=col, arrow= tk.LAST)
            if ('PI' in self.G.edges[Node1,Node2]) and (self.G.edges[Node1,Node2]['PI']):
                r = 4
                self.canvas.create_oval(x_middle-r, y_middle-r,x_middle+r, y_middle+r, fill=self.colors['indicator'])


    # Check the edge validity
    def CheckEdge(self, Node1, Node2):
        EdgeValid = False
        # edge is valid if it has weight attribute and it is float
        if not ('weight' in self.G.edges[Node1, Node2] and \
                isinstance(self.G.edges[Node1, Node2]['weight'], float)):
            EdgeValid = True
        return EdgeValid


    # Check the node complexity and validity
    def CheckNode(self, Node):
        NodeValid = False
        StructuralNodes = ['MG','SIN','COS','ABS']
        NodesWithDegree2 = ['SIN','COS','ABS']
        ConstantNodes = ['I','C']
        # variable nodes must include following attributes:
        # xpos, ypos (integer)
        # SY_Var, unit (strings)
        if self.G.nodes[Node]['type'] == 'V':
            if not ('xpos' in self.G.nodes[Node] and \
                    'ypos' in self.G.nodes[Node] and \
                    'SY_Var' in self.G.nodes[Node] and \
                    'unit' in self.G.nodes[Node]):
                NodeValid = True
        # power gates must include following attributes:
        # xpos, ypos (integer)
        # target power, base and eqNode nodes should be connected with PG
        # PG should have 3 edges (base, power and OUT)
        elif self.G.nodes[Node]['type'] == 'PG':
            if not ('xpos' in self.G.nodes[Node] and \
                    'ypos' in self.G.nodes[Node] and \
                    len(list(self.G.predecessors(Node))) == 2 and \
                    len(list(self.G.successors(Node))) == 1):
                NodeValid = True
            if not NodeValid:
                NumberOfPEI = 0
                for i in self.G.in_edges(Node):
                    if ('PI' in self.G.edges[i]) and (self.G.edges[i]['PI']):
                        NumberOfPEI += 1
                if NumberOfPEI != 1:
                    NodeValid = True
        # structural nodes must include following attributes:
        # xpos, ypos (integer)
        # eqNode target should be connected with the origin node
        elif self.G.nodes[Node]['type'] in StructuralNodes:
            if not ('xpos' in self.G.nodes[Node] and \
                    'ypos' in self.G.nodes[Node] and \
                    len(list(self.G.successors(Node))) == 1):
                NodeValid = True
        # SIN, COS and ABS gates must only be connected with two edges (IN and OUT)
        elif self.G.nodes[Node]['type'] in NodesWithDegree2:
            if self.G.degree[Node] != 2:
                NodeValid = True
        # Constant nodes should have the value atribute and it has to be float
        # NOT implemented, but
        # 'I' (constant one) node should have xpos, ypos and value only
        # 'C' node should have xpos, ypos, value, SY_Var and unit attibutes
        elif self.G.nodes[Node]['type'] in ConstantNodes:
            if not('value' in self.G.nodes[Node] and \
                   isinstance(self.G.nodes[Node]['value'], float)):
                NodeValid = True
        return NodeValid


    # Makes the grid in the background
    def checkered(self, canvas, line_distance):
        # vertical lines at an interval of 'line_distance' pixel
        #print(type(line_distance))
        for x in range(line_distance, self.canvas_width,line_distance):
            canvas.create_line(x, 0, x, self.canvas_height, fill=self.colors['bg_active'])
        # horizontal lines at an interval of 'line_distance' pixel
        for y in range(line_distance, self.canvas_height,line_distance):
            canvas.create_line(0, y, self.canvas_width, y, fill=self.colors['bg_active'])



class ToolDialog(simpledialog.Dialog):
    def __init__(self, parent, tools):
        self.tools = tools
        super(ToolDialog,self).__init__(parent)

    def body(self, master):
        self.geometry("500x400")
        self.v1 = tk.IntVar(value=self.tools[0])
        self.v2 = tk.IntVar(value=self.tools[1])
        self.v3 = tk.IntVar(value=self.tools[2])
        self.v4 = tk.IntVar(value=self.tools[3])
        self.v5 = tk.IntVar(value=self.tools[4])
        self.v6 = tk.IntVar(value=self.tools[5])
        self.v7 = tk.IntVar(value=self.tools[6])
        self.v8 = tk.IntVar(value=self.tools[7])
        self.v9 = tk.IntVar(value=self.tools[8])
        self.v10 = tk.IntVar(value=self.tools[9])
        self.v11 = tk.IntVar(value=self.tools[10])
        self.v12 = tk.IntVar(value=self.tools[11])
        self.v13 = tk.IntVar(value=self.tools[12])
        self.v14 = tk.IntVar(value=self.tools[13])
        self.v15 = tk.IntVar(value=self.tools[14])
        self.v16 = tk.IntVar(value=self.tools[15])
        b1 = tk.Checkbutton(master, text = 'Positive Edge Tool', variable = self.v1)
        b2 = tk.Checkbutton(master, text = 'Negative Edge Tool', variable = self.v2)
        b3 = tk.Checkbutton(master, text = 'Equation Tool', variable = self.v3)
        b4 = tk.Checkbutton(master, text = 'Multiplication Tool', variable = self.v4)
        b5 = tk.Checkbutton(master, text = 'Summation Tool', variable = self.v5)
        b6 = tk.Checkbutton(master, text = 'Power Tool', variable = self.v6)
        b7 = tk.Checkbutton(master, text = 'Sinus Tool', variable = self.v7)
        b8 = tk.Checkbutton(master, text = 'Cosinus Tool', variable = self.v8)
        b9 = tk.Checkbutton(master, text = 'Node Eraser Tool', variable = self.v9)
        b10 = tk.Checkbutton(master, text = 'Edge Eraser Tool', variable = self.v10)
        b11 = tk.Checkbutton(master, text = 'Constant One', variable = self.v11)
        b12 = tk.Checkbutton(master, text = 'ABS Filter', variable = self.v12)
        b13 = tk.Checkbutton(master, text = 'TAN Filter', variable = self.v13)
        b14 = tk.Checkbutton(master, text = 'Indicator edge', variable = self.v14)
        b15 = tk.Checkbutton(master, text = 'Skills', variable = self.v15)
        b16 = tk.Checkbutton(master, text = 'Variable fusion', variable = self.v16)
        b1.pack(side = 'top')
        b2.pack(side = 'top')
        b3.pack(side = 'top')
        b4.pack(side = 'top')
        b5.pack(side = 'top')
        b6.pack(side = 'top')
        b7.pack(side = 'top')
        b8.pack(side = 'top')
        b9.pack(side = 'top')
        b10.pack(side = 'top')
        b11.pack(side = 'top')
        b12.pack(side = 'top')
        b13.pack(side = 'top')
        b14.pack(side = 'top')
        b15.pack(side = 'top')
        b16.pack(side = 'top')
        return b1 # initial focus

    def retrieve_output(self):
        return [self.v1.get(),
                self.v2.get(),
                self.v3.get(),
                self.v4.get(),
                self.v5.get(),
                self.v6.get(),
                self.v7.get(),
                self.v8.get(),
                self.v9.get(),
                self.v10.get(),
                self.v11.get(),
                self.v12.get(),
                self.v13.get(),
                self.v14.get(),
                self.v15.get(),
                self.v16.get()]

    def apply(self):
        self.result = self.retrieve_output()


class TextDialog(simpledialog.Dialog):
    def __init__(self, parent, textDeafult):
        self.textDeafult = textDeafult
        super(TextDialog,self).__init__(parent)

    def make_new_line(self,event):
        self.e1.insert('insert', '\n')

    def body(self, master):
        self.geometry("500x500")
        tk.Label(master, text="Enter new problem text:").pack()
        self.e1 = tk.Text(master)
        self.e1.bind('<Control-Down>', self.make_new_line)
        #self.e1.configure(width = 450)
        self.e1.pack()
        self.e1.insert('insert', self.textDeafult)
        return self.e1 # initial focus

    def retrieve_input(self):
        return self.e1.get('1.0','end')

    def apply(self):
        first = self.retrieve_input()
        self.result = first


class VarDialog(simpledialog.Dialog):

    def __init__(self, parent, oldState = None):
        self.oldParams = oldState
        super(VarDialog,self).__init__(parent)

    def body(self, master):
        self.geometry("500x300")

        Entry1 = tk.Frame(master)
        tk.Label(Entry1, text="Variable name:").pack(side = 'left')
        self.VarName = tk.Entry(Entry1)
        self.VarName.pack(side = 'left')
        Entry1.pack()

        Entry2 = tk.Frame(master)
        tk.Label(Entry2, text="Variable unit:").pack(side = 'left')
        self.VarUnit = tk.Entry(Entry2)
        self.VarUnit.pack(side = 'left')
        Entry2.pack()

        Entry3 = tk.Frame(master)
        self.VarKnown = tk.IntVar(value=0)
        CheckBox = tk.Checkbutton(Entry3,
                                  text = 'Variable known:',
                                  variable = self.VarKnown)
        CheckBox.pack(side = 'left')
        Entry3.pack()

        Entry4 = tk.Frame(master)
        tk.Label(Entry4, text="Variable value:").pack(side = 'left')
        self.VarValue = tk.Entry(Entry4)
        self.VarValue.pack(side = 'left')
        Entry4.pack()

        Entry5 = tk.Frame(master)
        self.VarSolution = tk.IntVar(value=0)
        CheckBox = tk.Checkbutton(Entry5,
                                  text = 'To be found:',
                                  variable = self.VarSolution)
        CheckBox.pack(side = 'left')
        Entry5.pack()

        Entry6 = tk.Frame(master)
        tk.Label(Entry6, text="Expected value:").pack(side = 'left')
        self.SolutionValue = tk.Entry(Entry6)
        self.SolutionValue.pack(side = 'left')
        Entry6.pack()

        if self.oldParams:
            self.VarName.insert(0, self.oldParams[0])
            self.VarUnit.insert(0, self.oldParams[1])
            self.VarKnown.set(self.oldParams[2])
            self.VarValue.insert(0, self.oldParams[3])
            self.VarSolution.set(self.oldParams[4])
            self.SolutionValue.insert(0, self.oldParams[5])

        return self.VarName # initial focus

    def retrieve_input(self):
        #print(self.VarValue.get(), type(self.VarValue.get()))
        return [self.VarName.get(),
                self.VarUnit.get(),
                self.VarKnown.get(),
                self.VarValue.get(),
                self.VarSolution.get(),
                self.SolutionValue.get()]

    def apply(self):
        self.result = self.retrieve_input()


class ConstDialog(simpledialog.Dialog):

    def __init__(self, parent, oldState = None):
        self.oldParams = oldState
        super(ConstDialog,self).__init__(parent)

    def body(self, master):
        self.geometry("500x300")

        Entry1 = tk.Frame(master)
        tk.Label(Entry1, text="Constant name:").pack(side = 'left')
        self.VarName = tk.Entry(Entry1)
        self.VarName.pack(side = 'left')
        Entry1.pack()

        Entry2 = tk.Frame(master)
        tk.Label(Entry2, text="Constant unit:").pack(side = 'left')
        self.VarUnit = tk.Entry(Entry2)
        self.VarUnit.pack(side = 'left')
        Entry2.pack()

        Entry3 = tk.Frame(master)
        tk.Label(Entry3, text="Constant value:").pack(side = 'left')
        self.VarValue = tk.Entry(Entry3)
        self.VarValue.pack(side = 'left')
        Entry3.pack()

        if self.oldParams:
            self.VarName.insert(0, self.oldParams[0])
            self.VarUnit.insert(0, self.oldParams[1])
            self.VarValue.insert(0, self.oldParams[2])

        return self.VarName # initial focus

    def retrieve_input(self):
        return [self.VarName.get(),
                self.VarUnit.get(),
                float(self.VarValue.get())]

    def apply(self):
        self.result = self.retrieve_input()


class BundleDialog(simpledialog.Dialog):

    def __init__(self, parent, oldState = None):
        self.oldParams = oldState
        super(BundleDialog,self).__init__(parent)

    def body(self, master):
        self.geometry("500x300")
        self.SkillVar = tk.StringVar(master)
        choices = { 'Introduction','Kinematics','Mechanics','Electrodynamics','Thermodynamics','Optics','Modern Physics'}
        if self.oldParams:
            self.SkillVar.set(self.oldParams)
        else:
            self.SkillVar.set('Introduction') # set the default option
        popupMenu = tk.OptionMenu(master, self.SkillVar, *choices)
        label = tk.Label(master, text="Choose the bundle")
        label.pack()
        popupMenu.pack()
        return None

    def retrieve_input(self):
        return self.SkillVar.get()

    def apply(self):
        self.result = self.retrieve_input()


class EqDialog(simpledialog.Dialog):

    def __init__(self, parent, oldState = None):
        self.oldParams = oldState
        super(EqDialog,self).__init__(parent)

    def body(self, master):
        self.geometry("500x300")

        Entry1 = tk.Frame(master)
        self.Flag1 = tk.IntVar(value=0)
        CheckBox = tk.Checkbutton(Entry1,
                                  text = 'To be found:',
                                  variable = self.Flag1)
        CheckBox.pack(side = 'left')
        Entry1.pack()


        Entry2 = tk.Frame(master)
        tk.Label(Entry2, text="Expected parsing:").pack(side = 'left')
        self.ExpParsing = tk.Entry(Entry2)
        self.ExpParsing.pack(side = 'left')
        Entry2.pack()

        if self.oldParams:
            self.Flag1.set(self.oldParams[0])
            self.ExpParsing.insert(0, self.oldParams[1])

        return None # initial focus

    def retrieve_input(self):
        return [self.Flag1.get(),
                self.ExpParsing.get()]

    def apply(self):
        self.result = self.retrieve_input()



class SkillDialog(simpledialog.Dialog):

    def __init__(self, parent, oldState = None):
        self.skills = oldState
        super(SkillDialog,self).__init__(parent)

    def body(self, master):
        self.geometry("500x300")
        self.SkillVar = tk.StringVar(master)
        self.skillDict = {}
        choices = []
        for skill in self.skills:
            self.skillDict[skill[1]] = skill[2]
            choices.append(skill[1])
        #choices = self.skillDict.keys()
        self.SkillVar.set(choices[0]) # set the default option
        popupMenu = tk.OptionMenu(master, self.SkillVar, *choices)
        label = tk.Label(master, text="Choose your skill!")
        label.pack()
        popupMenu.pack()
        return None

    def retrieve_input(self):
        key = self.SkillVar.get()
        value = self.skillDict[key]
        return value

    def apply(self):
        self.result = self.retrieve_input()


class HoverButton(tk.Button):
    def __init__(self, master, **kw):
        tk.Button.__init__(self,master=master,**kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        self['background'] = self.defaultBackground



def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


# Main program body
if __name__ == '__main__':
    # Set flag according to the resolution of your pyscreen
    # scaleFactor=1: bad screen
    # scaleFactor=2: good screen

    # Create connection to the database
    database = 'PhysAI.db'
    conn = create_connection(database)
    with conn:
        scaleFactor = 1.0
        root = tk.Tk()
        MainApplication(root, scaleFactor=scaleFactor, conn = conn).pack(side='top', fill='both', expand=True)
        root.mainloop()
