import pandas as pd
import numpy as np

d = {'Cool' : [2,3,6,1,8,2,2,3], 'Dope' : [6, 34, 43, 21, 12, 100, 1, 7]}
df = pd.DataFrame(d)

df2 = df.sort_values(by=['Cool'])
print(df)
print(df2)

d = df2.to_numpy()
print(d)
print(d[3])