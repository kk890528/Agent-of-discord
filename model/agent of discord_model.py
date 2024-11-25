# -*- coding: utf-8 -*-
"""
Created on Mon Aug 19 15:51:23 2024

@author: Emile
"""

import matplotlib.pyplot as plt
import networkx as nx
import seaborn as sns
import numpy as np
import math
from sklearn.cluster import KMeans
import gc
import pandas as pd
import random

def fixed_normal (m,sd,n):
    '''
     function to creat fixed normal distribution
    m:Mean
    sd: Standard Deviation
    n: numbers want to generate
    '''

    opinions=np.random.normal(m,sd,n)
    opinions[opinions>1]=1
    opinions[opinions<0]=0
    return opinions

def right_bounded(x,e,m):
    group1_x=x[x>0.5]
    group2_x=x[x<=0.5]
    e_r=np.zeros(x.shape)
    m1=0.2
    br_1=m1*group1_x+(1-m1)/2
    e_r[x>0.5]=br_1*e[x>0.5]
    m2=0.7
    br_2=m2*group2_x+(1-m2)/2
    e_r[x<=0.5]=br_2*e[x<=0.5]
    return e_r
class social_bot_paper:
    def __init__(self,n,network,e,robot_ratio,a,b,bots_loc='random'):
        '''
        n: number of nodes
        netwwork: networks structure (could be generated by networkx)
        e: tolerance of human agents
        robot_ratio: the ratio of bots
        a:
        b:
        bots_loc: the employment of bots in networks, have four options:
              1. random: randomly employ
              2. high degree: bots occupied the nodes with the highest centrality
              3. low degree: bots occupied the nodes with the lowest centrality
              4. middle: bots occupied the nodes with the middle centrality
        '''
        self.network=network
        #decides each agent is human or robot 1 is human 2 is robot
        self.species=np.full((n,),1)
        #bumber of bots and their location
        bots_n=n*robot_ratio
        degree=self.network.degree
        if bots_loc=='random':
          self.robots_loc=np.random.choice(range(0,n),round(bots_n),replace=False)
        
        if bots_loc=='high degree':
          self.robots_loc=np.array([i[0] for i in sorted(random.sample(tuple(degree),len(tuple(degree))), key=lambda x: x[1], reverse=True)[0:int(bots_n)]])
        if bots_loc=='low degree':
          self.robots_loc=np.array([i[0] for i in sorted(random.sample(tuple(degree),len(tuple(degree))),key=lambda x: x[1])[0:int(bots_n)]])
        if bots_loc=='middle':
          self.robots_loc=np.array([i[0] for i in sorted(random.sample(tuple(degree),len(tuple(degree))),key=lambda x: x[1])[int((n-bots_n)/2):int((n+bots_n)/2)]])
        
        if robot_ratio==0:
          self.robots_loc=np.random.choice(range(0,1000),round(0),replace=False)
        robots_loc=self.robots_loc
        self.species[robots_loc]=2
        
        #decide robots hold positive opinion
        self.pos_bots_loc=robots_loc[0:int(len(robots_loc)/2)]
        #decide robots hold negative opinion
        self.neg_bots_loc=robots_loc[int(len(robots_loc)/2):]
       
        #opinion
        mean1 = 0.6
        std_dev1 = 0.075
        # Parameters for the second normal distribution
        mean2 = 0.4
        std_dev2 = 0.075
        # Generate random numbers from the first normal distribution
        data1 = fixed_normal(mean1, std_dev1, 500)
        # Generate random numbers from the second normal distribution
        data2 = fixed_normal(mean2, std_dev2, 500)
        # Combine the data from the two distributions
        combined_data= np.concatenate((data1, data2))
        
        self.opinions=combined_data
        
        #if the agent is robot, opinions set beta distribution
        self.opinions[robots_loc]=np.random.beta(a=0.1,b=0.1,size=len(robots_loc))
        #set threshold
        self.threshold=np.full((n,),e)
        
        #if the agent is robot, threshold=10
        self.threshold[self.species==2]=10
    def step(self,a_h,a_b,m,share='random'):
        '''
        Function to excuate a round of simulation (generate one post and share)
        a_h: confidence of human
        a_b: confidence of bots
        m: homophily of human agents
        share: who can be the beginner? There are three options:
              1. random: both human and bots
              2. human: only human
              3. bots: only bots

        '''
        infulenced_people=[]
        express_list=[]
        infor_time=0
        
        # choose agent i
        if share == 'random':
            agent_i = np.random.choice(np.array(self.network.nodes), 1)[0]
        elif share == 'human':
            agent_i = np.random.choice(np.array(self.network.nodes)[self.species == 1],1)[0]
        elif share == 'bots':
            agent_i = np.random.choice(np.array(self.network.nodes)[self.species == 2],1)[0]
        if agent_i in self.robots_loc:
          a=a_b
    
        else:
          a=a_h
        infulenced_people.extend([agent_i])
        neighbors=self.network[agent_i]
        #express_opinion
        opinion=self.opinions[agent_i]+np.random.normal(0,0.05,1)
        if opinion>1:
            opinion=1
        if opinion<0:
            opinion=0
        neighbors_opinion=self.opinions[neighbors]
        neighbors_threshold=self.threshold[neighbors]
        neighbors_boubded_r=right_bounded(neighbors_opinion,neighbors_threshold,m)
        neighbors_boubded_l=neighbors_threshold-neighbors_boubded_r
        accept_or_not=neighbors_opinion*0
        opinion_differ=opinion-neighbors_opinion
        accept_or_not[opinion_differ>=0]=abs(opinion_differ[opinion_differ>=0])<neighbors_boubded_r[opinion_differ>=0]
        accept_or_not[opinion_differ<0]=abs(opinion_differ[opinion_differ<0])<neighbors_boubded_l[opinion_differ<0]
        
        infulenced_neighobr=list(np.array(neighbors)[accept_or_not==1])
        
        express_list.extend(infulenced_neighobr)
        
        infulenced_people.extend(infulenced_neighobr)
        infulenced_neighobr=[x for x in infulenced_neighobr if x not in self.robots_loc]
        #Opinion updates
        self.opinions[infulenced_neighobr]=self.opinions[infulenced_neighobr]+(opinion-self.opinions[infulenced_neighobr])*a

        infor_time+=1


        while len(express_list)!=0 and infor_time<21 :
            
            agent_i= np.random.choice(express_list)
            if agent_i in self.robots_loc:
              a=a_b
              
            else:
              a=a_h
            express_probility=1
            if flip(express_probility):
                #print(agent_i)
                agent_i_express=opinion+(self.opinions[agent_i]-opinion)*np.random.normal(0.5,0.05,1)
                if agent_i_express>1:
                    agent_i_express=1
                if agent_i_express<0:
                    agent_i_express=0
                express_list.remove(agent_i)
                neighbors=self.network[agent_i]
                
                neighbors_opinion=self.opinions[neighbors]
                neighbors_threshold=self.threshold[neighbors]
                neighbors_boubded_r=right_bounded(neighbors_opinion,neighbors_threshold,m)

                neighbors_boubded_l=neighbors_threshold-neighbors_boubded_r
                #print(a)
                accept_or_not=neighbors_opinion*0
                opinion_differ=agent_i_express-neighbors_opinion
                accept_or_not[opinion_differ>=0]=abs(opinion_differ[opinion_differ>=0])<neighbors_boubded_r[opinion_differ>=0]
                accept_or_not[opinion_differ<0]=abs(opinion_differ[opinion_differ<0])<neighbors_boubded_l[opinion_differ<0]
                accept_or_not[self.species[neighbors]==2]=1
                infulenced_neighobr=list(np.array(neighbors)[accept_or_not==1])
                # remove agents have been infulenced
                infulenced_neighobr=[x for x in infulenced_neighobr if x not in infulenced_people]
                express_list.extend(infulenced_neighobr)
                infulenced_people.extend(infulenced_neighobr)
                infulenced_neighobr=[x for x in infulenced_neighobr if x not in self.robots_loc]
                #Opinion updates
                self.opinions[infulenced_neighobr]=self.opinions[infulenced_neighobr]+((agent_i_express-self.opinions[infulenced_neighobr])*a)

                infor_time+=1
            else:
                express_list.remove(agent_i)
                infor_time+=1
                pass

        return self.opinions
    def polar_index(self):
        '''
        Function to calculate the current polarization stance of the network.
        '''
        o=self.opinions[self.species==1]
        kmeans = KMeans(n_clusters=2)
        kmeans.fit(np.reshape(o, (-1, 1)))
        labels = kmeans.labels_
        g1=o[labels==0]
        g2=o[labels==1]
        G=[g1,g2]
        a=1.6
        if len(g1)==0 or len(g2)==0:
            ER=0
        else:
            K=len(o)**(-1*(a+2))
            ER=K*sum(sum((len(i)**(1+a))*len(j)*abs(np.mean(i)-np.mean(j)) for j in G) for i in G)
        
        return ER