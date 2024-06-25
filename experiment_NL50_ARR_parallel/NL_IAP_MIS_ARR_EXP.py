import networkx as nx
import pandas as pd
import socket
import math
import myDictionary as md
import copy
import random
import time
import datetime
import multiprocessing as mp

for difficulty in [1,2,3]:    
    for (dataID,numReps) in [(9,50),(0,50),(2,50),(3,50),(4,50),(5,50),(8,50),(1,10),(6,10),(7,10)]:    
        for rep in range(numReps):
            if __name__ == '__main__':
                print()
                print('dataID=',dataID)
                print('rep=',rep)
                print('difficulty=',difficulty)

                numCores = mp.cpu_count()
                p = mp.Pool(numCores)

                logSum = 0.5
                machineName = socket.gethostname()

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
                timeLimit = bestTime * 20000

                print('initial solution')
                print('best solution of size',len(bestStable))
                print('bestRevenue=',bestRevenue)
                print('bestTrial=',bestTrial)
                print('bestTime=',bestTime)
                print('timeLimit=',timeLimit)
                print(datetime.datetime.now())

                nLocal = 0

                multiArgs = []  
                for coreID in range(numCores):
                    multiArgs += [(coreID,relY,timeLimit,tic,toc,trial,bestRevenue,bestStable,bestTime,bestTrial,nLocal,confG,G,utility,pOption,halfY,logSum,dataID,rep,difficulty,machineName)]  

                results = p.map(md.ARR_Time_Revised2, multiArgs)

                coreArray = [] 
                machineArray = []
                logSumArray = []
                networkIDs = []
                reps = []
                numberNodes = []
                numberEdges = []
                finishTimeArray = []
                finishTrialArray = []
                bestTimeArray = []
                bestTrialArray = []
                bestRevenueArray = []

                for coreID0,relY0,timeLimit0,toc0,trial0,bestRevenue0,bestStable0,bestTime0,bestTrial0,nLocal0 in results:
                    coreArray += [coreID0]
                    machineArray += [machineName]
                    logSumArray += [logSum]
                    networkIDs += [dataID]
                    reps += [rep]
                    numberNodes += [len(G.nodes())]
                    numberEdges += [len(G.edges())]
                    finishTimeArray += [toc0 - tic]
                    finishTrialArray += [trial0]
                    bestTimeArray += [bestTime0]
                    bestTrialArray += [bestTrial0]
                    bestRevenueArray += [bestRevenue0]

                    print(coreID0,toc0-tic,bestTime0,bestTrial0,bestRevenue0)

                    grandResult = pd.DataFrame(list(zip(coreArray,machineArray,logSumArray,networkIDs,reps,numberNodes,numberEdges,finishTimeArray,finishTrialArray,bestTimeArray,bestTrialArray,bestRevenueArray)),columns =['Core','Machine','logSum','ID','Rep','Nodes','Edges','Finish Time','Finish Trial','Best Time','Best Trial','Best Revenue'])
                    grandResult.to_csv(r'result/result_ARR_NL_%s_%s_logSum%s_Difficulty%s.csv'%(dataID,rep,int(logSum*100),difficulty), index = False)#Check

                print('FINISH')
                print(datetime.datetime.now())


























