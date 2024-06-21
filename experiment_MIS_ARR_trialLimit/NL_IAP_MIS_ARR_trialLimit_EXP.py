import networkx as nx
import pandas as pd
import socket
import math
import myDictionary as md
import copy
import random
import time
import datetime



logSum = 1
machineName = socket.gethostname()
trialLimit = 6000

for difficulty in [1,2,3]:    
    for (dataID,numReps) in [(9,50),(0,50),(2,50),(3,50),(4,50),(5,50),(8,50),(1,10),(6,10),(7,10)]:
    
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
            
            
            halfY = {}
            for (i,j) in confG.nodes():
                halfY[i,j] = 0.5
                
            
            tic = time.time()
            trial = 0    
            relY = copy.deepcopy(halfY) # relY = seed
            stable = md.RR(relY,confG)
            revenue = md.revenue(stable,utility,logSum,pOption,G)
            
            bestTrial = trial
            stable = sorted(stable)
            bestStable = copy.deepcopy(stable)
            bestRevenue = revenue
            toc = time.time()
            bestTime = toc - tic
            trialLimit = max(trialLimit, bestTrial * 3)
            print()
            print('best solution of size',len(bestStable))
            print('bestRevenue=',bestRevenue)
            print('bestTrial=',bestTrial)
            print('bestTime=',bestTime)
            print(datetime.datetime.now())
    
            machineArray = [machineName]
            logSumArray = [logSum]
            optionsArray = [len(options['Option'])]
            networkIDs = [dataID]
            reps = [rep]
            numberNodes = [len(G.nodes())]
            numberEdges = [len(G.edges())]
            opts = [bestRevenue]
            RMSDArray = [0.0]
            times = [bestTime]        
            trials = [bestTrial]        
    
            result = pd.DataFrame(list(zip(machineArray,logSumArray,optionsArray,networkIDs,reps,numberNodes,numberEdges,opts,RMSDArray,times,trials)),columns =['Machine','logSum','Options','ID','Rep','Nodes','Edges','Revenue','RMSD','Time','Trial'])
            result.to_csv(r'result/result_ARR_NL_%s_%s_logSum%s_Difficulty%s.csv'%(dataID,rep,int(logSum*100),difficulty), index = False)#Check
            
            nLocal = 0
            while trial < trialLimit:
                
                # trial number += 1
                trial += 1
            
                # compute RMSD of relY = seed
                RMSD = 0.0
                for (i,j) in confG.nodes():
                    RMSD += (relY[i,j] - 0.5) ** 2
                RMSD = RMSD / len(confG.nodes())
                RMSD = math.sqrt(RMSD)
                
                               

                ## find random stable sets near relY; same = True if stable == bestStable
                stable, same = md.RRComplete(relY,confG,bestStable) # stable is not sorted if len(stable) != len(bestStable)
                
            
                if same == 0:
                    revenue = md.revenue(stable,utility,logSum,pOption,G)
            
                    if bestRevenue < revenue:
                        bestTrial = trial
                        stable = sorted(stable) # the stabe set of maxRevenue
                        bestStable = copy.deepcopy(stable)
                        bestRevenue = revenue
                        toc = time.time()
                        bestTime = toc - tic
                        print()
                        print('best solution of size',len(bestStable))
                        print('bestRevenue=',bestRevenue)
                        print('bestTrial=',bestTrial)
                        print('bestTime=',bestTime)
                        trialLimit = max(trialLimit, bestTrial * 3)
                        print('trialLimit=',trialLimit)
                        print('remaining time = ',(trialLimit - bestTrial) * bestTime / bestTrial)
                        print(datetime.datetime.now())
    
                        machineArray += [machineName]
                        logSumArray += [logSum]
                        optionsArray += [len(options['Option'])]
                        networkIDs += [dataID]
                        reps += [rep]
                        numberNodes += [len(G.nodes())]
                        numberEdges += [len(G.edges())]
                        opts += [bestRevenue]
                        RMSDArray += [RMSD]
                        times += [bestTime]        
                        trials += [bestTrial]        
            
                        result = pd.DataFrame(list(zip(machineArray,logSumArray,optionsArray,networkIDs,reps,numberNodes,numberEdges,opts,RMSDArray,times,trials)),columns =['Machine','logSum','Options','ID','Rep','Nodes','Edges','Revenue','RMSD','Time','Trial'])
                        result.to_csv(r'result/result_ARR_NL_%s_%s_logSum%s_Difficulty%s.csv'%(dataID,rep,int(logSum*100),difficulty), index = False)#Check
    
                                                            
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
            
            
            print()
            print('FINISH')
            print('finishTime=',toc - tic)
            print(datetime.datetime.now())
            print('finishTrial=',trial)
    
            machineArray += ['FINISH']
            logSumArray += [logSum]
            optionsArray += [len(options['Option'])]
            networkIDs += [dataID]
            reps += [rep]
            numberNodes += [len(G.nodes())]
            numberEdges += [len(G.edges())]
            opts += [bestRevenue]
            RMSDArray += [-1]
            times += [toc-tic]        
            trials += [trial]        
    
            result = pd.DataFrame(list(zip(machineArray,logSumArray,optionsArray,networkIDs,reps,numberNodes,numberEdges,opts,RMSDArray,times,trials)),columns =['Machine','logSum','Options','ID','Rep','Nodes','Edges','Revenue','RMSD','Time','Trial'])
            result.to_csv(r'result/result_ARR_NL_%s_%s_logSum%s_Difficulty%s.csv'%(dataID,rep,int(logSum*100),difficulty), index = False)#Check
            
            
            
            
            
            
            
            
            
            
            
            
            
            
    










