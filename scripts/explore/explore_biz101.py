import pandas as pd

df = pd.read_csv('train/data/biz_101/ban_hang.csv', encoding = 'utf-8-sig')
print(df.shape)
print(df.dtypes)
print(df.head())