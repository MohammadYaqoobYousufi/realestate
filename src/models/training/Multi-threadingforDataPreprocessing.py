import concurrent.futures
import pandas as pd
import numpy as np

def clean_chunk(df_chunk):
    # Example cleaning step
    df_chunk['price_per_sqft'] = df_chunk['price'] / df_chunk['sqft']
    return df_chunk

df = pd.read_csv('data.csv')
chunks = np.array_split(df, 4)

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(clean_chunk, chunks)

df_cleaned = pd.concat(results)
