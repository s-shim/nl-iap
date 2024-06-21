import networkx as nx
import pandas as pd
from gurobipy import *
import socket
import myDictionary as md
import sys, os
if os.path.exists(r'log/optMIS_MNL_%s_%s_Difficulty%s.csv'%(dataID,rep,difficulty)): sys.exit(1)

machineName = socket.gethostname()

difficulty, dataID, numReps, rep = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])

# for difficulty in [1,2,3]:    
#     for (dataID,numReps) in [(9,50),(0,50),(2,50),(3,50),(4,50),(5,50),(8,50),(1,10),(6,10),(7,10)]:    

machineArray = []
networkIDs = []
reps = []
numberNodes = []
numberEdges = []
opts = []
times = []
accurates = []

# for rep in range(numReps):            
    
lines = pd.read_csv('../data/lines/lines_%s.csv'%dataID)

if difficulty == 1:
    # easy instances
    nodes = pd.read_csv('../data/nodes_3products_revised/nodes_revised_%s_%s.csv'%(dataID,rep))
    options = pd.read_csv('../data/options_3products.csv')
    forbidden = pd.read_csv('../data/forbiddenPairs_3products_generous.csv')

if difficulty == 2:
    # difficult instances
    nodes = pd.read_csv('../data/nodes_3products_medium/nodes_medium_%s_%s.csv'%(dataID,rep))
    options = pd.read_csv('../data/options_3products_medium.csv')
    forbidden = pd.read_csv('../data/forbiddenPairs_3products_medium.csv')

if difficulty == 3:
    # very difficult instances
    nodes = pd.read_csv('../data/nodes_3products_difficult/nodes_difficult_%s_%s.csv'%(dataID,rep))
    options = pd.read_csv('../data/options_3products_difficult.csv')
    forbidden = pd.read_csv('../data/forbiddenPairs_3products_difficult.csv')


pOption = {}
for j in options['Option']:
    [pOption[j]] = options.loc[options['Option']==j,'Price']
    
utility, confG, G, confSubG = md.profile(lines,nodes,options,forbidden)


# ILP formulation
model = Model('Inequity Aversion Pricing - MNL')
model.setParam('LogFile', 'log/log_difficulty%s_MNL_%s_%s_%s.txt'%(difficulty,machineName, dataID, rep))

# Employ Variables
y_vars = []
y_names = []
for u in G.nodes():
    for p in options['Option']:
        y_vars += [(u,p)]
        y_names += ['Y[%s,%s]'%(u,p)]        
Y = model.addVars(y_vars, vtype = GRB.BINARY, name = y_names)

prob_vars = []
prob_names = []
for u in G.nodes():
    prob_vars += [(u,0)]
    prob_names += ['Prob[%s,%s]'%(u,0)]        
    for p in options['Option']:
        prob_vars += [(u,p)]
        prob_names += ['Prob[%s,%s]'%(u,p)]        
Prob = model.addVars(prob_vars, vtype = GRB.CONTINUOUS, name = prob_names)

# Add constrains
for (u,p), (v,q) in confG.edges():
    LHS = [(1,Y[u,p]),(1,Y[v,q])]
    RHS = 1
    model.addConstr(LinExpr(LHS)<=RHS, name='Eq.IS(%s,%s,%s,%s)'%(u,p,v,q))
    
for (i,j) in confG.nodes():
    LHS = [(-1,Y[i,j]),(1,Prob[i,j])]
    RHS = 1
    model.addConstr(LinExpr(LHS)<=0, name='Eq.Prob<=Y(%s,%s)'%(i,j))

## entire probability = 1 for every individual
for i in G.nodes():
    LHS = [(1,Prob[i,0])]
    for j in options['Option']:
        LHS += [(1,Prob[i,j])]
    model.addConstr(LinExpr(LHS)==1, name='Eq.EntProb(%s)'%(i))

## Prob[i,j] <= odds[i,j] * Prob[i,0]
for (i,j) in confG.nodes():
    [prob_ij] = nodes.loc[nodes['Node']==i, 'P%s'%j]
    odds = prob_ij / (1 - prob_ij)        
    LHS = [(-odds,Prob[i,0]),(1,Prob[i,j])]
    model.addConstr(LinExpr(LHS)<=0, name='Eq.Prob<=Base(%s,%s)'%(i,j))

## Prob[i,0] <= 1/odds[i,j] * Prob[i,j] + (1 - Y[i,j])
for (i,j) in confG.nodes():
    [prob_ij] = nodes.loc[nodes['Node']==i, 'P%s'%j]
    odds = prob_ij / (1 - prob_ij)        
    LHS = [(1,Y[i,j]),(-1/odds,Prob[i,j]),(1,Prob[i,0])]
    model.addConstr(LinExpr(LHS)<=1, name='Eq.Base<=Prob(%s,%s)'%(i,j))

# Set objective
objTerms = []
for (u,p) in confG.nodes():
    [price_p] = options.loc[options['Option']==p,'Price']
    [prob_p] = nodes.loc[nodes['Node']==u, 'P%s'%p]
    objTerms += [(price_p,Prob[u,p])]
        
model.setObjective(LinExpr(objTerms), GRB.MAXIMIZE)
model.update()
model.optimize()
    
uOpt = {}
for i in G.nodes():
    uOpt[i] = []

varName = []
varValue = []
for v in model.getVars():
    varName += [v.varname]
    varValue += [v.x]
    if v.varname[0] == 'Y' and v.x > 1 - 0.0001:
        offer = v.varname[2:-1].split(',')
        user  = int(offer[0])
        dOpt  = int(offer[1])
        uOpt[user] += [dOpt]


odds = {}
tpw = {}
totalDemand = 0
for i in nodes['Node']:
    for j in options['Option']:
        [probability_ij] = nodes.loc[nodes['Node']==i,'P%s'%j]
        odds[i,j] = probability_ij / (1 - probability_ij)

    tpw[i] = 1
    for j in uOpt[i]:
        tpw[i] += odds[i,j]
        
    for j in uOpt[i]:
        [price_j] = options.loc[options['Option']==j,'Price']
        totalDemand += price_j * odds[i,j] / tpw[i]
print('totalDemand=',totalDemand)

machineArray += [machineName]
networkIDs += [dataID]
reps += [rep]
numberNodes += [len(G.nodes())]
numberEdges += [len(G.edges())]
opts += [model.objVal]
times += [model.Runtime]
accurates += [totalDemand]
            
result = pd.DataFrame(list(zip(machineArray,networkIDs,reps,numberNodes,numberEdges,opts,accurates,times)),columns =['Machine','NetworkID','Rep','Nodes','Edges','OPT','Accurate','Time'])
result.to_csv(r'result/resultMIS_MNL%s_%s_Difficulty%s.csv'%(dataID,rep,difficulty), index = False)#Check
    
optSol = pd.DataFrame(list(zip(varName,varValue)),columns =['varName','varValue'])
optSol.to_csv(r'log/optMIS_MNL_%s_%s_Difficulty%s.csv'%(dataID,rep,difficulty), index = False)#Check
    
