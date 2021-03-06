# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 17:50:01 2020

@author: lainfied
"""

from __future__ import print_function
from ortools.sat.python import cp_model

#%% Setting paths

my_path= 'C:/Users/lainfied/Desktop/DL/1.Arbeit_2019/Analysis_diverse/16.Shiftplanning/'

path_input= my_path+'1.Input/'
path_code= my_path+'2.Code/'
path_output= my_path+'3.Output/'

import os
#%% Directories

print('The previous working directory is: {}'.format(os.getcwd()))
os.chdir(path_code)
print('The current working directory is: {}'.format(os.getcwd()))

#%% Importing packages

import pandas as pd
import numpy as np

# Importing own functions

from functions import from_excel_to_pandas

#%% Defining functions

# Class to print solutions

class ShiftsPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Print intermediate solutions."""
    
        def __init__(self, shifts, num_anlagen, num_all_workers, num_days, num_shifts, sols):
            cp_model.CpSolverSolutionCallback.__init__(self)
            self.shifts= shifts
            self._num_anlagen= num_anlagen
            self._num_all_workers = num_all_workers
            self._num_days = num_days
            self._num_shifts = num_shifts
            self._solutions = set(sols)
            self._solution_count = 0
    
        def on_solution_callback(self):
            if self._solution_count in self._solutions:
                print('Solution %i' % self._solution_count)
                for d in range(self._num_days):
                    print('Day %i' % d)
                    for n in range(self._num_all_workers):
                        is_working = False
                        for a in range(self._num_anlagen):
                            for s in range(self._num_shifts):
                                if self.Value(self._shifts[(n, d, a, s)]):
                                    is_working = True
                                    print('  Worker %i works shift %i in line %i ' % (n, s, a))
                                if not is_working:
                                    print('  Worker {} does not work '.format(n))
                print()
            self._solution_count += 1
    
        def solution_count(self):
            return self._solution_count

def solver(num_anlagen, num_supervisors, num_workers, preferences_file):
    
    # This program tries to find an optimal assignment of workers to shifts
    # (3 shifts per day, for 6 days), subject to some constraints (see below).
    # Each worker can request to be assigned to specific shifts.
    # The optimal assignment maximizes the number of fulfilled shift requests.
    
    preferences= from_excel_to_pandas(path_input, preferences_file, "Shift_preference", {})
    preferences= preferences.set_index('worker', inplace= False)
    
    anlage_restrictions= from_excel_to_pandas(path_input, preferences_file, "Prod_line_poss", {})
    anlage_restrictions= anlage_restrictions.set_index('worker', inplace= False)
    
    num_shifts = 3
    
    num_days= 6
    
    all_workers= range(num_supervisors+num_workers)
    all_shifts= range(num_shifts)
    all_days= range(num_days)
    all_anlagen= range(num_anlagen)
    
    shift_requests= []
    
    for n in all_workers:
        shift_requests.append([[list(preferences.loc[n]) for a in all_anlagen] for d in all_days])
    
    # Creates the model
        
    model = cp_model.CpModel()
    
    # Creates shift variables.
    # Shifts[(n, d, s)]: worker 'n' works shift 's' on day 'd' on line 'a'.
    
    all_valid= []
    
    for n in all_workers:
        for a in all_anlagen:
            if anlage_restrictions.loc[n][a] == 0: # Some workers are not allowed to work in some lines
                pass
            else:
                for d in all_days:
                    for s in all_shifts:
                        if (a, d, s) not in [(0, 5, 1), (0, 5, 2), (1, 5, 0), \
                           (1, 5, 1), (1, 5, 2), (2, 5, 0), (2, 5, 1), (2, 5, 2)]: #some shifts are not worked at some production lines
                            all_valid.append([n, d, a, s])
                        else:
                            pass
    
    
    all_valid_df= pd.DataFrame(all_valid)
    all_valid_df.columns= ['n', 'd', 'a', 's']
    
    shifts = {}
    
    for element in all_valid:
        shifts[(element[0], element[1], element[2], element[3])] = model.NewBoolVar('shift_n%id%ia%is%i' % (element[0], element[1], element[2], element[3]))
    
    # Each shift is assigned to exactly seven workers (2 supervisors and 2 workers)
    
    # For line 1, 2 and 3
    # Each shift is assigned to exactly 2 supervisors.
    
    for a in all_anlagen:
        for d in all_days:
            for s in all_shifts:
                
                possible_workers= np.array((all_valid_df[(all_valid_df['d'] == d) & (all_valid_df['a'] == a) & (all_valid_df['s']  == s)]['n']))
                possible_workers= list(possible_workers[possible_workers <= num_supervisors-1])
                
                if len(possible_workers)> 0:
                    model.Add(sum(shifts[(n, d, a, s)] for n in possible_workers) == 2)
                else:
                    pass
    
                            
    for a in all_anlagen:
        for d in all_days:
            for s in all_shifts:
                
                possible_workers= np.array(all_valid_df[(all_valid_df['d'] == d) & (all_valid_df['a'] == a) & (all_valid_df['s']  == s)]['n'])
                possible_workers= list(possible_workers[possible_workers >= num_supervisors])
                
                if len(possible_workers)> 0:
                
                    model.Add(sum(shifts[(n, d, a, s)] for n in possible_workers) == 2)
                else:
                    pass
    
                
    # Each worker works at most one shift per day and each worker can be at most at one production line each day and each shift
    
    for n in all_workers:
        for d in all_days:
            
            possible_anlagen= list(all_valid_df[(all_valid_df['n'] == n) & (all_valid_df['d'] == d)]['a'])
            possible_shifts= list(all_valid_df[(all_valid_df['n'] == n) & (all_valid_df['d'] == d)]['s'])
            possible_anlagen_shifts= [(possible_anlagen[i], possible_shifts[i]) for i in range(len(possible_anlagen))]
            
            if len(possible_anlagen_shifts)> 0:
                model.Add(sum(shifts[(n, d, element[0], element[1])] for element in possible_anlagen_shifts) <= 1)
            else:
                pass
    
    # min_shifts_assigned is the largest integer such that every worker can be
    # assigned at least that number of shifts.
    
    min_shifts_per_worker = 4
    max_shifts_per_worker = 6
    
    for n in all_workers:
        
        possible_info= all_valid_df[all_valid_df['n']== n]
        possible_days= list(possible_info['d'])
        possible_anlagen= list(possible_info['a'])
        possible_shifts= list(possible_info['s'])
        
        possibilities= [(possible_days[i], possible_anlagen[i], possible_shifts[i]) for i in range(len(possible_days))]
        
        if len(possibilities)>0:
            num_shifts_worked = sum(shifts[(n, element[0], element[1], element[2])] for element in possibilities)
            
            model.Add(min_shifts_per_worker <= num_shifts_worked)
            model.Add(num_shifts_worked <= max_shifts_per_worker)
        
        else: 
            pass
    
    # Workers should rest at least two shifts between work shifts
    
    all_workers_restriction= []
    
    for n in all_workers:
        worker= []
        for d in all_days:
            for s in all_shifts:
                worker.append(sum(shifts[(n, d, a, s)] for a in all_anlagen if [n, d, a, s] in all_valid))
                
        all_workers_restriction.append(worker)
    
    
    for each_workers_restriction in all_workers_restriction:
        
        for i in range(len(each_workers_restriction)):
            model.Add(sum(each_workers_restriction[i:i+3]) <= 1)
    
    # Calling maximizatin function
    
    model.Maximize(
        sum(shift_requests[element[0]][element[1]][element[2]][element[3]] * \
            shifts[(element[0], element[1], element[2], element[3])] for element in all_valid))
    
    solver= cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 100.0
    
    status= solver.Solve(model)
    
    if status != 3:
        
        print('A solution found:')
        
        for a in all_anlagen:
            print('Production line: %i' % a)
            for d in all_days:
                print('Day %i' % d)
                for s in all_shifts:
                    print('Shift: %i' % s)
                    for n in all_workers:
                        
                        try:
                                                        
                            if shift_requests[n][d][a][s] == 1:
                                print('Worker %i works shift %i at line %i (requested).' % (n, s, a))
                            else:
                                print('Worker %i works shift %i at line %i (not requested).' % (n, s, a))
                        
                        except:
                            pass
                        
                        
        print('Statistics')
        print('  - conflicts       : %i' % solver.NumConflicts())
        print('  - branches        : %i' % solver.NumBranches())
        print('  - wall time       : %f s' % solver.WallTime())
        
        # List with all the shift information
        shift_model= []
            
        for a in all_anlagen:
            for s in all_shifts:
                
                workers_all_days= []
                for n in all_workers:
                    for d in all_days:
                        try:
                            workers_all_days.append(solver.Value(shifts[(n, d, a, s)]))
                        except:
                            workers_all_days.append(0)
                shift_model.append(workers_all_days)
        
        # Saving data frame
                
        shift_model= pd.DataFrame(shift_model).T
        
        index= ['Worker_{0:02d}_day_{0:02d}'.format(n, d) for n in all_workers for d in all_days] # Adding index to data_frame
        cols= ['Prod_line_%i_Shift_%i' % (a, s) for a in all_anlagen for s in all_shifts] # Adding 
        
        shift_model.index= index
        shift_model.columns= cols
        
        # Verifying answers
        # Supervisors/Workers per shift
        
        string= ['Supervisor per shift:', 'Workers per shift:']
        
        opc_s= [0, num_supervisors]
        opc_e= [num_supervisors, num_supervisors+num_workers]
        
        print('')
        print('Verifying total number of supervisors and workers in each shift')
        print('')
        
        for i in range(len(opc_s)):
            print(string[i])
        
            count= 0
            for a in all_anlagen:
                for s in all_shifts:
                    for d in all_days:
                        
                        result= sum([solver.Value(shifts[(n, d, a, s)]) for n in range(opc_s[i], opc_e[i]) if [n, d, a, s] in all_valid])
                        
                        if (([n, d, a, s] in all_valid) and (result== 2)) or ([n, d, a, s] not in all_valid): # In each shift you need to have 2 supervisors and 2 workers
                            pass
                        else:
                            count+= 1
                            print('Problem a%i s%i' % (a, s))
            
            print('Number of problems equals to %i' % count)
        
        # Max number of shifts each worker can have
        
        print('')
        print('Verifying total number shifts/day each supervisor/worker might have')
        print('')
        
        count= 0
        for n in all_workers:
            
            for d in all_days:
                
                result= sum([solver.Value(shifts[(n, d, s, a)]) for s in all_shifts for a in all_anlagen if [n, d, s, a] in all_valid])
                if result == 0 or result == 1: # Each worker, can only have 0 or 1 shift per day.
                    pass
                else:
                    count+= 1
                    print('Problem at n%i d%i' % (n, d))
                    
        print('Total number of conflicts equals to: %i' % count)
                
    else:
        print('No solution was found, iterate')
    
    return shift_model
        
#%% Calling the solver

#The 21042024_shift_preferences.xlsx has the Shift preference of the workers and the in which line each worker can work

# 3 Production lines (the information should be consistent with the file 21042024_shift_preferences.xlsx)
# 20 Supervisors
# 20 Workers

shift_result= solver(3, 20, 20, "21042024_shift_preferences.xlsx") 
shift_result.to_excel(path_output+"DOMPZ_schedule.xlsx")
