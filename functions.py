# -*- coding: utf-8 -*-
"""
Created on Tue Nov  5 11:12:36 2019

@author: lainfied
"""
import pandas as pd

#%% Importing from Excel

def from_excel_to_pandas(path_input, file_name, sheet, dictionary):
    """
    func: Open an excel file and open it as a pandas frame
    path_input [string] is the input file,
    file_name [string] is the file name that you want to convert from excel to pandas and 
    sheet [string] is the sheet name
    dictionary [dic] can define the data type of each column of the imported excel file
    """
    
    file = pd.DataFrame(data= pd.ExcelFile(path_input+file_name).parse(sheet_name= sheet, index_col= None, converters= dictionary))
    
    return file
