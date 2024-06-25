import networkx as nx
import pandas as pd
from gurobipy import *
import socket
import myDictionary as md
from itertools import combinations

machineName = socket.gethostname()
logSum = 0.5

for difficulty in [1,2,3]:    
    for (dataID,numReps) in [(9,50),(0,50),(2,50),(3,50),(4,50),(5,50),(8,50),(1,10),(6,10),(7,10)]:    

        machineArray = []
        logSumArray = []
        networkIDs = []
        reps = []
        numberNodes = []
        numberEdges = []
        opts = []
        times = []
        accurates = []

        for rep in range(numReps):            

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

            theStable = []
            for r in range(1,len(confSubG.nodes())+1):
                for c in combinations(list(confSubG.nodes()),r):
                    if len(confSubG.subgraph(list(c)).edges()) == 0:
                        theStable += [list(c)]
        
    
            # ILP formulation
            model = Model('Inequity Aversion Pricing - NL')
            model.setParam('LogFile', 'log/log_difficulty%s_NLLazy_%s_lambda%s_%s_%s.txt'%(difficulty,machineName,int(logSum*100), dataID, rep))
            
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
        
            
            for i in G.nodes():
                for j in options['Option']:
                    for k in options['Option']:
                        if j != k:
                            LHS = [(1, Prob[i,j]), (- math.exp(utility[i,j] / logSum) / math.exp(utility[i,k] / logSum), Prob[i,k]), (1, Y[i,k])]
                            model.addConstr(LinExpr(LHS)<=1, name='Eq.IIA(%s,%s,%s)'%(i,j,k))
                            
            for i in G.nodes():
                n_stb = 0
                for stb in theStable:
                    n_stb += 1
                    
                    z_Y_stb = 0.0
                    for j in stb:
                        z_Y_stb += math.exp(utility[i,j] / logSum)
                    w_z_Y_stb = z_Y_stb ** logSum / (1 + z_Y_stb ** logSum)
                    dw_z_Y_stb = logSum * z_Y_stb ** (logSum - 1) / (1 + z_Y_stb ** logSum) ** 2
                    
                    LHS_ub = []
                    LHS_lb = []
                    for j in options['Option']:
                        LHS_ub += [(1,Prob[i,j])]
                        LHS_ub += [(- dw_z_Y_stb * math.exp(utility[i,j] / logSum), Y[i,j])]
    
                        LHS_lb += [(1,Prob[i,j])]
                        if j in stb:
                            LHS_lb += [(-1,Y[i,j])]
                        else:
                            LHS_lb += [(1,Y[i,j])]
                        
                    rhs_ub = w_z_Y_stb
                    rhs_lb = w_z_Y_stb - len(stb)
                    for j in stb:
                        rhs_ub = rhs_ub - dw_z_Y_stb * math.exp(utility[i,j] / logSum)
    
                    model.addConstr(LinExpr(LHS_ub)<=rhs_ub, name='Eq.UB(%s,%s)'%(i,n_stb)).Lazy = 1
                    model.addConstr(LinExpr(LHS_lb)>=rhs_lb, name='Eq.LB(%s,%s)'%(i,n_stb)).Lazy = 1
    
        
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
    
                tpw[i] = 0
                for j in uOpt[i]:
                    tpw[i] += math.exp(utility[i,j] / logSum)
                    
                for j in uOpt[i]:
                    [price_j] = options.loc[options['Option']==j,'Price']
                    totalDemand += price_j * tpw[i] ** logSum / (1 + tpw[i] ** logSum) * math.exp(utility[i,j] / logSum) / tpw[i]
            print(totalDemand)


            machineArray += [machineName]
            logSumArray += [logSum]
            networkIDs += [dataID]
            reps += [rep]
            numberNodes += [len(G.nodes())]
            numberEdges += [len(G.edges())]
            opts += [model.objVal]
            times += [model.Runtime]
            accurates += [totalDemand]
                        
            result = pd.DataFrame(list(zip(machineArray,logSumArray,networkIDs,reps,numberNodes,numberEdges,opts,accurates,times)),columns =['Machine','logSum','NetworkID','Rep','Nodes','Edges','OPT','Accurate','Time'])
            result.to_csv(r'result/resultMIS_NLLazy_lambda%s_%s_Difficulty%s.csv'%(int(logSum*100),dataID,difficulty), index = False)#Check
                
            optSol = pd.DataFrame(list(zip(varName,varValue)),columns =['varName','varValue'])
            optSol.to_csv(r'log/optMIS_NLLazy_lambda%s_%s_%s_Difficulty%s.csv'%(int(logSum * 100),dataID,rep,difficulty), index = False)#Check
