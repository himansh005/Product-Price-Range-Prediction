# -*- coding: utf-8 -*-
"""IndiaMART_Master.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xEDZ81kvwKgOpVSv-LFRHinBRAAgASzi

# IndiaMart PriceRangePrediction

New Section


```
# To Achieve the target, we have assumed the following things:

      1. 85% and above prices should be retained after outlier detection for finding the price range.
      2. Units which have counts < 5 are removed.
     
```


```
# The following ensemble technique is used to find outliers:

        1. Isolation Forests - IF
        2. DBScan
        3. LOF
        4. MaxVote(IF, DBScan, LOF)
```

```

# For estimation of amount of contamination, Inter-Quartile Range Data is considered. If Data(IQR)==100%, it is set to 98% and if <=85%, it is set to 87%
```

The **contamination**  factor and **epsilon** value are not fixed and infered dynamically by the above technique. Primary test indicate robust nature of this technique.

##Imports
"""

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN
import seaborn as sns

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

"""##Data Preprocessing"""

#read data
data1 = pd.read_csv('martdata/t1.csv')
data2 = pd.read_csv('martdata/t2.csv')
data3 = pd.read_csv('martdata/t3.csv')

#remove empty columns
data1 = data1.drop(columns=['Unnamed: 3','Unnamed: 4'])
data2 = data2.drop(columns=['Unnamed: 3','Unnamed: 4'])
data3 = data3.drop(columns=['Unnamed: 3','Unnamed: 4'])

"""### Categories Consolidation

1. Merge similar **units** by stemming. For example, "KG" and "Kilogram" are merged. Similarily, "Unit" and "unit" are merged.

2. Remove **units** whole value < 5.

Processing : **Data 1**
"""

data1.Unit.unique()

data1_group = data1.groupby(by='Unit')
data1_group.describe()

data1.Unit = data1.Unit.replace({"Unit": "unit","Pack": "pack"})
data1_group = data1.groupby(by='Unit')
data1_group.describe()

#thresholding

data1 = data1[data1.Unit != 'Kit']
data1 = data1[data1.Unit != 'ONWARDS']
data1 = data1[data1.Unit != 'Set']
data1 = data1[data1.Unit != 'Unit(s)']
data1 = data1[data1.Unit != 'kit']
data1 = data1[data1.Unit != '1nos']

data1.head()

"""Processing : **Data 2**"""

data2_group = data2.groupby(by='Unit')
data2_group.describe()

data2.Unit = data2.Unit.replace({"Unit": "unit", "Pack": "pack"})
data2.Unit = data2.Unit.replace({"Unit": "unit","Pack": "pack"})

#Thresholding

data2 = data2[data2.Unit != 'Pair(s)']
data2 = data2[data2.Unit != 'Pieces']
data2 = data2[data2.Unit != 'Set']
data2 = data2[data2.Unit != 'Unit/Onwards']

data2_group = data2.groupby(by='Unit')
data2_group.describe()

"""Processing : **Data 3**"""

data3['Unit'] = data3['Unit'].str.lower()
data3_group = data3.groupby(by='Unit')
data3_group.describe()

data3.Unit = data3.Unit.replace({"single piece": "piece",
                                 "per piece": "piece",
                                 "per piese":"piece",
                                 "pi":"piece",
                                 "peice":"piece",
                                 "pcs":"piece",
                                 "onepices":"piece",
                                 "one unit":"piece",
                                 "one pcs":"piece",
                                 "1":"piece",
                                 "1 pc":"piece",
                                 "1 pcs":"piece",
                                 "1 pice":"piece",
                                 "1 piece":"piece",
                                 "1pc":"piece",
                                 "1pcd":"piece",
                                 "1pcs":"piece",
                                 "1piece":"piece",
                                 "1pis":"piece",
                                 "single":"piece",
                                 "Unit":"unit",
                                 "Pc":"piece",
                                 "no":"number",
                                 "one":"piece",
                                 "one peace":"piece",
                                 "pair piece":"pair",
                                 "pc":"piece",
                                 "pics":"piece",
                                 "pices":"piece",
                                 "psc":"pieces",
                                 "unit(s)":"unit",
                                 "set(s)":"sets",
                                 "packet":"pack",
                                 "packet(s)":"pack",
                                 "packets":"pack",
                                 "piece(s)":"pieces",
                                 "piece(s) onwards":"pieces"
                                 })

data3 = data3[data3.Unit != '10']
data3 = data3[data3.Unit != '170 per peice']
data3 = data3[data3.Unit != '10-10000']
data3 = data3[data3.Unit != '100 pic']
data3 = data3[data3.Unit != '12 units']
data3 = data3[data3.Unit != '1000 per unit']
data3 = data3[data3.Unit != '3 set']
data3 = data3[data3.Unit != '4 pcs']
data3 = data3[data3.Unit != '4 units']
data3 = data3[data3.Unit != '5']
data3 = data3[data3.Unit != 'barrel']
data3 = data3[data3.Unit != 'carton']
data3 = data3[data3.Unit != 'day']
data3 = data3[data3.Unit != 'feet']
data3 = data3[data3.Unit != 'pound']
data3 = data3[data3.Unit != 'year']
data3 = data3[data3.Unit != 'unstitch']
data3 = data3[data3.Unit != 'xl size']
data3 = data3[data3.Unit != 'rs']
data3 = data3[data3.Unit != 'suit']
data3 = data3[data3.Unit != 'selfie kurtis']
data3 = data3[data3.Unit != 'dollar']
data3 = data3[data3.Unit != 'gram']
data3 = data3[data3.Unit != 'in']
data3 = data3[data3.Unit != 'kilogram']
data3 = data3[data3.Unit != 'meter']
data3 = data3[data3.Unit != 'ounce']
data3 = data3[data3.Unit != 'ounce(s)']

data3_group = data3.groupby(by='Unit')
data3_group.describe()

#concat all data
data = pd.concat([data1,data2,data3])
data.groupby(['Category Name','Unit']).describe()

"""# Driver Program

**The Main Ensembled Function**
"""
def getHyperparameters(sd,retain):
  
  import math
  
  dis=[]
  temp =list(sd['Price'])
  for i in range(0,len(temp)-1):
    dis.append(temp[i+1]-temp[i])

  arr = np.array(dis)
  diss = pd.DataFrame(dis,columns=['dis'])
  std=diss['dis'].std()
  ma = diss['dis'].max()
  n=len(dis)
  
  cnt={}
  unique_dis=list(set(dis))
  for i in unique_dis:
    cnt[i]=dis.count(i)
  keys = cnt.keys()
  keys=sorted(keys)
  cands=[]
  full = int(round((retain*n),0))
  for i in keys:
    full = full - cnt[i]
    cands.append(i)
    if(full<=0):
      break
    
  
  b = pd.DataFrame(cands)
  epsilon = round(np.max(np.array(b))*1000,0)/1000
  return(epsilon)

def findPriceRange(datas,contamination_factor,seed_percentage):
    
    
    datax = datas
    datay = datas
    dataz = datas
    ######_____Isolation Forests
    
    isolation_forest = IsolationForest(contamination=contamination_factor)
    if_vote = isolation_forest.fit_predict(dataz['Price'].values.reshape(-1,1))
    
    ######_____DBScan
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.cluster import DBSCAN
     
    scaler = MinMaxScaler()
    sd = scaler.fit_transform(datax)
    sd = pd.DataFrame(sd,columns=['Price'])
    
    
    outlier_detection = DBSCAN(eps = getHyperparameters(sd,seed_percentage) ,metric="euclidean",min_samples = 3,n_jobs = -1)
    clusters = outlier_detection.fit_predict(sd)
    clusters[clusters!=-1]=1
    
    dbscan_vote = clusters
    
    ######_____Local Outlier Factor
    clf = LocalOutlierFactor(n_neighbors=20, contamination=contamination_factor)
    y_pred = clf.fit_predict(np.array(datay['Price']).reshape(-1,1))
    X_scores = clf.negative_outlier_factor_

    lof_vote = y_pred
    

    
    final_votes = lof_vote + if_vote + dbscan_vote
    final_votes[final_votes>0] = 1
    final_votes[final_votes<0]=0
    pure_data = final_votes*np.array(datas['Price'])
    pure_data = np.extract(pure_data!=0, pure_data)
    min_price, max_price = np.min(pure_data), np.max(pure_data)
    return([min_price, max_price, pure_data])

def estimateContamination(dataChunk):
  
  #index column addition
  unnormal_data=pd.DataFrame(dataChunk)

  # Computing IQR
  Q1 = unnormal_data['Price'].quantile(0.25)
  Q3 = unnormal_data['Price'].quantile(0.75)
  IQR = Q3 - Q1 

  import random
  label_data = list(unnormal_data['Price'])
  t=[]
  for i in range(len(unnormal_data['Price'])):
    if( (label_data[i] <= (Q1 - 1.5 * IQR)) or (label_data[i] >= (Q3 + 1.5 * IQR))):
      t.append(-1)
    else:
      t.append(1)

  filtered = t
  #keep seed percentage == IQR range or 85% or 98%
  #assume 85%-98% purityz
  import math

  seed_percentage  = math.floor((len(filtered)/len(unnormal_data))*100)
  if(seed_percentage<85):
    seed_percentage = 87
  elif(seed_percentage>=99):
    seed_percentage = 98

#   print("Seed Percentage :",seed_percentage)

  contamination_factor=0.5*((100-seed_percentage)/100)    
  
  return([seed_percentage, contamination_factor])

#function to retrive relevant prices
#usage example : accessData('Impact Drill','Piece')

def accessData(category,unit):
  return(data['Price'][(data['Category Name']==category) & (data['Unit'] == unit)])

#dictionary catgory  -> unit -> prices

indexes = {}
categories = list(set(list(data['Category Name'])))
for category in categories:
  units = list(set(list(data['Unit'][data['Category Name'] == category])))
  indexes[category]=units

data.head()

debug = 0
prints=[]

"""**Computer Price Range for entire data**"""

for category in categories:
  for j in range(len(indexes[category])):
    
    dataChunk = pd.DataFrame(accessData(category,indexes[category][j]))
    minn, maxx, pdata = findPriceRange(dataChunk,estimateContamination(dataChunk)[1], estimateContamination(dataChunk)[0])
    prints.append("Price Range for {} per {} is {} to {}".format(category, indexes[category][j], minn, maxx))
    plot_figure(dataChunk,category,indexes[category][j],minn,maxx)





"""### Results Visualisation"""



def plot_figure(x,c,u,min_price,max_price):
    
    k = x
    fig, ax = plt.subplots()
    num_bins = 10
    n, bins, patches = ax.hist(k['Price'], num_bins, color=['grey'])
    d = ax.fill_betweenx(n,min_price,max_price,color='g',alpha=0.5)
    ax.set_xlabel('Prices')
    ax.set_ylabel('Counts')
    ax.set_title(r'Histogram for item-'+ c +' and unit - '+ u)
    fig.tight_layout()
    plt.show()







