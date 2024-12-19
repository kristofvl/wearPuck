import pandas as pd
import numpy as np
from glob import glob
from tqdm.auto import tqdm
import os

def add_timestamp(my_df, df_ts):
    df_ts.index= df_ts.message
    joined_df = my_df.join(df_ts, "message", rsuffix="no").dropna()
    return joined_df

def load_recording(rec_folder):
    imu_df = pd.read_csv(rec_folder + "imu.csv")
    bme_df = pd.read_csv(rec_folder + "bme.csv")
    button_df = pd.read_csv(rec_folder + "button.csv")
    beacon_df = pd.read_csv(rec_folder + "beacon.csv")
    
    
    ts_df = pd.read_csv(rec_folder+ "timestamps.csv")
    imu_df = add_timestamp(imu_df, ts_df)
    bme_df = add_timestamp(bme_df, ts_df)
    button_df = add_timestamp(button_df, ts_df)
    beacon_df = add_timestamp(beacon_df, ts_df)
    
    merged_df = pd.concat([imu_df, bme_df]).sort_values(by="timestamp").ffill().bfill().reset_index().drop("index", axis=1)
    merged_df = pd.concat([merged_df, button_df]).sort_values(by="timestamp").ffill().fillna(0).reset_index().drop("index", axis=1)
    merged_df = pd.concat([merged_df, beacon_df]).sort_values(by="timestamp").ffill().bfill().reset_index().drop(["index", "messageno", "timestamp_recno"], axis=1)
    
    merged_df.button = merged_df.button.apply(lambda x: 0 if x == 0 or x is False or x == "False" else 1)
    return merged_df, imu_df, bme_df, ts_df

def merge_all_recs(save_folder=None):
    print(f"merging all recordings and saving in {save_folder}")
    if save_folder is not None and not os.path.isdir(save_folder):
        os.makedirs(save_folder)
    all_dfs = []
    rec_folders = glob("recs/*")
    for rec_fold in tqdm(rec_folders):
        try:
            if not os.path.isfile(f"{save_folder}/{rec_fold[5:]}.csv") and save_folder is not None:
                merged_df, _, _, _ = load_recording(rec_fold + "/")
                merged_df.to_csv(f"{save_folder}/{rec_fold[5:]}.csv")
            
                
            else:
                merged_df = pd.read_csv(f"{save_folder}/{rec_fold[5:]}.csv", index_col=[0])
            all_dfs.append(({rec_fold[5:]}, merged_df))
        except Exception as e:
            print(e)
    return all_dfs

if __name__ == "__main__":
    merge_all_recs("merged_new")
