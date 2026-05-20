"""Change the previous csv files so that they are properly formatted"""

import ast
import os

import numpy as np
import pandas as pd


def reformat_csv(file_path):
    # Read the CSV file
    df = pd.read_csv(file_path, index_col=0)
    print(file_path)
    # Convert string representations to NumPy arrays
    for col in df.columns[:-1]:
        df[col] = df[col].apply(
            lambda x: (
                np.array(ast.literal_eval(x))
                if isinstance(x, str) and x.startswith("[") and x.find(",") != -1
                else x
            )
        )

    # Overwrite the original CSV
    df.to_csv(file_path)


def process_all_csvs(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            reformat_csv(file_path)


# Specify root directory
root = "./resultados/"
for folder in os.listdir(root):
    if os.path.isdir(root + folder):
        print(folder)
        process_all_csvs(root + folder)
