import requests
from bs4 import BeautifulSoup
import os as os
import csv
import pandas as pd
import numpy as np
import chardet

#get csv files from url
url = "https://www.tesourotransparente.gov.br/ckan/dataset/transferencias-obrigatorias-da-uniao"
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', {'class': 'resource-url-analytics'})

    if links:
        for link in links:
            csv_url = link.get('href')
            csv_response = requests.get(csv_url)
            
            if csv_response.status_code == 200:
                file_name = csv_url.split("/")[-1]
                with open(file_name, "wb") as csv_file:
                    csv_file.write(csv_response.content)
                print(f"Download of {file_name} completed successfully.")
            else:
                print(f"Failed to download the CSV file: {csv_url}")
    else:
        print("Links to the CSV files not found on the page.")
else:
    print("Failed to access the page.")
    
    #check csv file encoding
def detect_encoding(arquivo):
    with open(arquivo, 'rb') as f:
        encode = chardet.detect(f.read())
        print('Encoding:', encode)
    return encode

ITR_encoding = detect_encoding('C:/Codes/teste_ds/ITR.csv')
FPM_encoding = detect_encoding('C:/Codes/teste_ds/FPM.csv')

#load csv files into pandas DataFrames
address = 'C:/Codes/teste_ds/'

csv_files = [f for f in os.listdir(address) if f.endswith('.csv')]
dataframes = {}

for file in csv_files:
    full_path = os.path.join(address, file)
    df_name = os.path.splitext(file)[0]
    dataframes[df_name] = pd.read_csv(full_path, encoding='ISO-8859-1', delimiter=';', skiprows=7)
    
    #check dfs
count_dfs = 0
for df_name, df in dataframes.items():
    print(f'DataFrame Name: {df_name}')
    count_dfs = count_dfs+1
print(count_dfs)

print(dataframes['CIDEEST'].head())

#replace categorical month/year to numeric and handle missing data, keep AL only 
for df_name, df in dataframes.items():
    dataframes[df_name].replace('-', pd.NA)
    dataframes[df_name].fillna(0)
    
    dataframes[df_name] = dataframes[df_name][(dataframes[df_name]['UF'] == 'AL')]
    dataframes[df_name]=dataframes[df_name].rename(columns=lambda x: x.replace("janeiro/", "").replace("fevereiro/", "").replace("março/", "").
                               replace("abril/", "").replace("maio/", "").replace("junho/", "").replace("julho/", "").replace("agosto/", "").
                               replace("setembro/", "").replace("outubro/", "").replace("novembro/", "").replace("dezembro/", ""))
    
    wanted_years = ['17', '18', '19', '20', '21', '22']
    for years in wanted_years:
        if years not in dataframes[df_name].columns:
            dataframes[df_name].insert(3, years, ['-'], allow_duplicates = True)
            
    
for df_name, df in dataframes.items():
    dataframes[df_name]=dataframes[df_name][['UF','17', '18', '19', '20', '21', '22']]
    dataframes[df_name]=pd.melt(dataframes[df_name], id_vars='UF',value_vars=['17','18','19','20','21','22'])
    dataframes[df_name]['index']=dataframes[df_name].groupby(['UF', 'variable']).cumcount()
    dataframes[df_name] = pd.pivot_table(dataframes[df_name], index=['UF', 'index'], columns='variable', values='value', aggfunc='first')
    dataframes[df_name].reset_index(inplace=True)
    dataframes[df_name].fillna('-',inplace=True)
    dataframes[df_name]['CSV Nome'] = df_name
    
    year_map = {
        '17':'2017',
        '18':'2018',
        '19':'2019',
        '20':'2020',
        '21':'2021',
        '22':'2022'
    }
    
    dataframes[df_name].rename(columns=year_map,inplace=True)
    
    #create output dataframe
output_columns = ['CSV Nome', 'ESTADOS', 'UF', 'Mes', '2017', '2018', '2019', '2020', '2021', '2022']
output_df = pd.DataFrame(columns = output_columns)
dfs_conc = list(dataframes.values())
output_df=pd.concat(dfs_conc,axis=0,ignore_index=True)

output_df['Mes']=list(range(1,13))*count_dfs
output_df['ESTADOS'] = 'ALAGOAS'
output_df['UF'] = 'AL'
output_df.drop('index',axis=1,inplace=True)
output_df.columns.name=''


output_df=output_df[['CSV Nome', 'ESTADOS', 'UF', 'Mes', '2017','2018','2019','2020','2021','2022']]
output_df.replace('-', 0, inplace=True)

print(output_df)

output_df.to_csv('Transferências Obrigatórias da União - AL - 2017 a 2022.csv')