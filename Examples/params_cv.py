# -*- coding: utf-8 -*-
"""
Created on Mon Apr 26 13:30:45 2021

@author: A694772
"""
from CST.utils.dataset_utils import load_sktime_dataset, return_all_dataset_names
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import pandas as pd
from CST.shapelet_transforms.mini_CST import MiniConvolutionalShapeletTransformer
from sklearn.pipeline import Pipeline
from itertools import combinations
from sklearn.model_selection import GridSearchCV

resume = False

available_memory_bytes = 62*1e9
max_cpu_cores = 86
numba_n_thread = 3
size_mult = 3500

max_process = max_cpu_cores//numba_n_thread


ps = []
for r in range(1, 6):
    ps.extend(list(combinations([100, 95, 90, 85, 80], r)))
n_splits = [1, 3, 5, 7, 10]
params = {'CST__P': ps,
          'CST__n_splits': n_splits}
print(params)

if resume:
    df = pd.read_csv('params_csv2.csv', sep=';')
    df = df.set_index('Unnamed: 0')
    print(df.index.values)
else:
    df = pd.DataFrame()

dataset_names = return_all_dataset_names()

for d_name in dataset_names:
    results = {}
    print(d_name)
    if d_name not in df.index.values:
        X, y, le = load_sktime_dataset(d_name, normalize=True)
        if X.shape[2] > 10:
            pipe = Pipeline([('CST', MiniConvolutionalShapeletTransformer()),
                             ('rf', RandomForestClassifier(n_estimators=400))])
    
            n_jobs = int(available_memory_bytes // (X.nbytes * size_mult))
            n_jobs = max(n_jobs if n_jobs <= max_process else max_process, 1)
            print('Launching {} parallel jobs'.format(n_jobs))
            clf = GridSearchCV(pipe, params, n_jobs=n_jobs, cv=10, verbose=1)
            clf.fit(X, y)
            print('Done')
            p_key = clf.cv_results_['params']
            rank = clf.cv_results_['mean_test_score']
            
            for i, p in enumerate(p_key):
                if str(p) in results.keys():
                    results[str(p)].append(rank[i])
                else:
                    results.update({str(p): [rank[i]]})
            print('Dumping results to csv')
            df = pd.concat(
                [df, pd.DataFrame(results, index=[d_name])], axis=0)
            df.to_csv('params_csv3.csv', sep=';')
