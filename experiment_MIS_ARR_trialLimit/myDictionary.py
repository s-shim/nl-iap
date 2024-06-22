import networkx as nx
import pandas as pd
import socket
import math
import myDictionary as md
import copy
import random



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
