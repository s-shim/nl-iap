import networkx as nx
import pandas as pd
import socket
import math
import myDictionary as md
import copy
import random
import time
import datetime


def profile(lines,nodes,options,forbidden):
    utility = {}
    confSubG = nx.Graph()
    G = nx.Graph()
    confG = nx.Graph()
    
    for i in nodes['Node']:
        for j in options['Option']:
            [probability_ij] = nodes.loc[nodes['Node']==i,'P%s'%j]
            utility[i,j] = math.log(probability_ij / (1 - probability_ij))
    
    for j in options['Option']:
        confSubG.add_node(j)
        
    for pair in forbidden['Pair']:
        [source_pair] = forbidden.loc[forbidden['Pair']==pair,'Source']
        [target_pair] = forbidden.loc[forbidden['Pair']==pair,'Target']
        confSubG.add_edge(source_pair,target_pair)
            
    for i in nodes['Node']:
        G.add_node(i)
    
    for l in lines['Line']:
        [source_l] = lines.loc[lines['Line']==l,'Source']
        [target_l] = lines.loc[lines['Line']==l,'Target']
        G.add_edge(source_l,target_l)
    
    for u in G.nodes():
        for q in options['Option']:
            confG.add_node((u,q))
    
    for u in G.nodes():
        for pair in forbidden['Pair']:
            [source_pair] = forbidden.loc[forbidden['Pair']==pair,'Source']
            [target_pair] = forbidden.loc[forbidden['Pair']==pair,'Target']
            
            confG.add_edge((u,source_pair),(u,target_pair))
    
    for u, v in G.edges():
        for pair in forbidden['Pair']:
            [source_pair] = forbidden.loc[forbidden['Pair']==pair,'Source']
            [target_pair] = forbidden.loc[forbidden['Pair']==pair,'Target']
            
            confG.add_edge((u,source_pair),(v,target_pair))
            confG.add_edge((u,target_pair),(v,source_pair))
    
    return utility, confG, G, confSubG



def revenue(stable,utility,logSum,pOption,G):
    stb = {}
    for i in G.nodes():
        stb[i] = []
    for (i,j) in stable:
        stb[i] += [j]
    
    zY = {}
    for i in G.nodes():
        zY[i] = 0.0
        for j in stb[i]:
            zY[i] += math.exp(utility[i,j]/logSum)
    
    revenue = 0.0
    for i in G.nodes():
        for j in stb[i]:
            prob_ij = zY[i] ** logSum / (1 + zY[i] ** logSum) * (math.exp(utility[i,j]/logSum) / zY[i])
            revenue += prob_ij * pOption[j]
    
    return revenue



def RR(relY,confG):

    yG = copy.deepcopy(confG)
    ptbY0 = {}
    ptbY1 = {}
    for (i,j) in confG.nodes():
        ptbY0[i,j] = random.random() * relY[i,j] 
        ptbY1[i,j] = relY[i,j] + random.random() * (1 - relY[i,j]) 
        if ptbY0[i,j] < 1 - ptbY1[i,j]:
            yG.remove_node((i,j))

    stable = []
    while len(yG.edges()) > 0:
        largestY = 0.0
        largest_ij = (-1,-1)
        for (i,j) in yG.nodes():
            if largestY < ptbY1[i,j]:
                largestY = ptbY1[i,j]
                largest_ij = (i,j)
        stable += [largest_ij]
        deleteNeighbors = [largest_ij]
        deleteNeighbors += list(yG.neighbors(largest_ij)) 
        for (i_n,j_n) in deleteNeighbors:
            yG.remove_node((i_n,j_n))
    stable += list(yG.nodes())        

    return stable



def RRComplete(relY,confG,bestStable):

    yG = copy.deepcopy(confG)
    ptbY0 = {}
    ptbY1 = {}
    for (i,j) in confG.nodes():
        ptbY0[i,j] = random.random() * relY[i,j] 
        ptbY1[i,j] = relY[i,j] + random.random() * (1 - relY[i,j]) 
        if ptbY0[i,j] < 1 - ptbY1[i,j]:
            yG.remove_node((i,j))

    stable = []
    while len(yG.edges()) > 0:
        largestY = 0.0
        largest_ij = (-1,-1)
        for (i,j) in yG.nodes():
            if largestY < ptbY1[i,j]:
                largestY = ptbY1[i,j]
                largest_ij = (i,j)
        stable += [largest_ij]
        deleteNeighbors = [largest_ij]
        deleteNeighbors += list(yG.neighbors(largest_ij)) 
        for (i_n,j_n) in deleteNeighbors:
            yG.remove_node((i_n,j_n))
    stable += list(yG.nodes())        


    if len(bestStable) != len(stable):
        same = 0
    else:
        stable = sorted(stable)
        same = 1
        for index in range(len(stable)):
            if stable[index] != bestStable[index]:
                same = 0
                break

    return stable, same


def RRComplete2(args):
    relY,confG,bestStable = args
    return RRComplete(relY,confG,bestStable)



def ARR_Time(unitTime,relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum):
    ticUnit = time.time()    
    while toc - ticUnit < unitTime:
        
        # trial number += 1
        trial += 1
    
        # compute RMSD of relY = seed
        RMSD = 0.0
        for (i,j) in confG.nodes():
            RMSD += (relY[i,j] - 0.5) ** 2
        RMSD = RMSD / len(confG.nodes())
        RMSD = math.sqrt(RMSD)
        
                       

        ## find random stable sets near relY; same = True if stable == bestStable
        stable, same = RRComplete(relY,confG,bestStable) # stable is not sorted if len(stable) != len(bestStable)
        
    
        if same == 0:
            revenue0 = revenue(stable,utility,logSum,pOption,G)
    
            if bestRevenue < revenue0:
                bestTrial = trial
                stable = sorted(stable) # the stabe set of maxRevenue
                bestStable = copy.deepcopy(stable)
                bestRevenue = revenue0
                toc = time.time()
                bestTime = toc - tic
                timeLimit = max(timeLimit, bestTime * 3)
        
                                                    
        move = True # by exponential smoothing
        if same == 1: # relY is close to bestStable
            nLocal += 1
            if random.random() < min(1, nLocal/20) * RMSD: # relY is too close to bestStable
                nLocal = 0
                relY = copy.deepcopy(halfY) # reset relY to halfY = centroid
                move = False
        else:
            nLocal = 0
            if same != 0:
                print('something wrong')
    
            
        if move == True:
            alpha = 1 / (1 + math.exp(4 * RMSD)) # convergence speed
            for (i,j) in confG.nodes():
                relY[i,j] = (1 - alpha) * relY[i,j]
            for (i,j) in bestStable:
                relY[i,j] += alpha * 1  
        else:
            if move != False:
                print('something wrong')
    
        toc = time.time()
        
    return relY,timeLimit,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal



def ARR_Time2(args):
    unitTime,relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum = args
    return ARR_Time(unitTime,relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum)



def ARR_Time_Revised(coreID,relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum,dataID,rep,difficulty,machineName):

    machineArray = [machineName]
    logSumArray = [logSum]
    networkIDs = [dataID]
    reps = [rep]
    numberNodes = [len(G.nodes())]
    numberEdges = [len(G.edges())]
    opts = [bestRevenue]
    RMSDArray = [0.0]
    times = [bestTime]        
    trials = [bestTrial]        

    result = pd.DataFrame(list(zip(machineArray,logSumArray,networkIDs,reps,numberNodes,numberEdges,opts,RMSDArray,times,trials)),columns =['Machine','logSum','ID','Rep','Nodes','Edges','Revenue','RMSD','Time','Trial'])
    result.to_csv(r'log/result_ARR_NL_%s_%s_logSum%s_Difficulty%s_Core%s.csv'%(dataID,rep,int(logSum*100),difficulty,coreID), index = False)#Check

    while toc - tic < timeLimit:
        
        # trial number += 1
        trial += 1
    
        # compute RMSD of relY = seed
        RMSD = 0.0
        for (i,j) in confG.nodes():
            RMSD += (relY[i,j] - 0.5) ** 2
        RMSD = RMSD / len(confG.nodes())
        RMSD = math.sqrt(RMSD)
        
                       

        ## find random stable sets near relY; same = True if stable == bestStable
        stable, same = RRComplete(relY,confG,bestStable) # stable is not sorted if len(stable) != len(bestStable)
        
    
        if same == 0:
            revenue0 = revenue(stable,utility,logSum,pOption,G)
    
            if bestRevenue < revenue0:
                bestTrial = trial
                stable = sorted(stable) # the stabe set of maxRevenue
                bestStable = copy.deepcopy(stable)
                bestRevenue = revenue0
                toc = time.time()
                bestTime = toc - tic
                #timeLimit = max(timeLimit, bestTime * 3)

                machineArray += [machineName]
                logSumArray += [logSum]
                networkIDs += [dataID]
                reps += [rep]
                numberNodes += [len(G.nodes())]
                numberEdges += [len(G.edges())]
                opts += [bestRevenue]
                RMSDArray += [RMSD]
                times += [bestTime]        
                trials += [bestTrial]        
    
                #result = pd.DataFrame(list(zip(machineArray,logSumArray,networkIDs,reps,numberNodes,numberEdges,opts,RMSDArray,times,trials)),columns =['Machine','logSum','ID','Rep','Nodes','Edges','Revenue','RMSD','Time','Trial'])
                #result.to_csv(r'log/result_ARR_NL_%s_%s_logSum%s_Difficulty%s_Core%s.csv'%(dataID,rep,int(logSum*100),difficulty,coreID), index = False)#Check
        
                                                    
        move = True # by exponential smoothing
        if same == 1: # relY is close to bestStable
            nLocal += 1
            if random.random() < min(1, nLocal/20) * RMSD: # relY is too close to bestStable
                nLocal = 0
                relY = copy.deepcopy(halfY) # reset relY to halfY = centroid
                move = False
        else:
            nLocal = 0
            if same != 0:
                print('something wrong')
    
            
        if move == True:
            alpha = 1 / (1 + math.exp(4 * RMSD)) # convergence speed
            for (i,j) in confG.nodes():
                relY[i,j] = (1 - alpha) * relY[i,j]
            for (i,j) in bestStable:
                relY[i,j] += alpha * 1  
        else:
            if move != False:
                print('something wrong')
    
        toc = time.time()
        
    machineArray += ['FINISH']
    logSumArray += [logSum]
    networkIDs += [dataID]
    reps += [rep]
    numberNodes += [len(G.nodes())]
    numberEdges += [len(G.edges())]
    opts += [bestRevenue]
    RMSDArray += [-1]
    times += [toc-tic]        
    trials += [trial]        

    result = pd.DataFrame(list(zip(machineArray,logSumArray,networkIDs,reps,numberNodes,numberEdges,opts,RMSDArray,times,trials)),columns =['Machine','logSum','ID','Rep','Nodes','Edges','Revenue','RMSD','Time','Trial'])
    result.to_csv(r'log/result_ARR_NL_%s_%s_logSum%s_Difficulty%s_Core%s.csv'%(dataID,rep,int(logSum*100),difficulty,coreID), index = False)#Check

    return coreID,relY,timeLimit,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal



def ARR_Time_Revised2(args):
    coreID, relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum,dataID,rep,difficulty,machineName = args
    return ARR_Time_Revised(coreID,relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum,dataID,rep,difficulty,machineName)
