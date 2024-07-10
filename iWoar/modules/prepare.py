import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob

from tqdm.auto import tqdm
import json

def load_all_recs():
    all_dfs = []
    rec_files = glob("data/*.csv")
    for fname in rec_files:
        merged_df = pd.read_csv(fname, index_col=[0])
        all_dfs.append((fname, merged_df))
    return all_dfs

convert_to_intlabel = lambda x: 0 if x == "Null" else 1 if x == "hw" else 2
convert_to_binlabel = lambda x: 0 if x == "Null" or x == "dry" else 1

def apply_labels(dfs):
    l_dfs = []
    label_df = pd.read_csv("labels.csv")
    label_df["fileid"]  = label_df.datetime
    for ind, row in label_df.iterrows():
        df = None
        found = False
        for rec_id, df in dfs:
            rec_id = rec_id[5:]
            if rec_id == row.fileid[-40:]:
                df["label"] = "Null"
                found = True
                break
            
        if not found:
            print("labels not found", row.fileid[-40:], rec_id)
            continue
        for d in json.loads(row.label):
            ## find df in which to apply the labels:
            df.loc[d["start"]:d["end"], "label"] = d["timeserieslabels"][0]
        df["intlabel"] = df.label.apply(convert_to_intlabel)
        df["binlabel"] = df.label.apply(convert_to_binlabel)
        df["altlabel"] = 0
        starts = df[(df.intlabel.diff() > 0) & (df.intlabel != 2)]
        ends = df[df.intlabel.diff() == -2]
        for start, end in zip(starts.index.to_list(), ends.index.to_list()):
            df.loc[start:end, "altlabel"] = 1
        df["subject"] = f"{ind+1:02d}"
        l_dfs.append(df)
    return l_dfs
    


def visualize_hws(l_dfs):
    all_l_dfs = pd.concat(l_dfs).reset_index(drop=True)
    start_pos = all_l_dfs[all_l_dfs.binlabel.diff() > 0]
    end_pos = all_l_dfs[all_l_dfs.binlabel.diff() < 0]
    hws = []
    out = []
    offset = 5000
    after = 10000
    end_offs = []
    for num, (i, row) in enumerate(start_pos.iterrows()):
        tmp_df = all_l_dfs.iloc[np.max([i-offset, 0]): i+ after].reset_index(drop=True).reset_index().copy()
        if len(tmp_df) >= offset+after:
            hws.append(tmp_df)
            end_offs.append(end_pos.index[num] - i + offset)
        #else:
            #hws.append(all_l_dfs.iloc[np.max([i-offset, 0]): i].reset_index(drop=True).reset_index().copy())
    for j, hwdf in enumerate(hws):
        hwdf.humid = hwdf.humid - hwdf.humid.iloc[offset]
        hwdf.temp = hwdf.temp - hwdf.temp.iloc[offset]
        hwdf.press = hwdf.press - hwdf.press.iloc[offset]
    hws_concat = pd.concat(hws)
    fig, ax = plt.subplots(figsize=(4,3))
    sns.lineplot(data=hws_concat, x="index", y="humid")
    plt.axvline(offset, color="green", label="begin of HW")
    for k, l in enumerate(end_offs):
        plt.axvline(l, c="orange", alpha=0.15, label=None if k != 0 else "end of HW")
    ax.set_ylabel("humidity change in %-points")
    ax.set_xlabel("time in s")

    ticks = np.linspace(0 , offset + after, 11)
    ticklabels = [int(x) for x in ((ticks - offset) // 50)]
    ax.set_xticks(ticks, ticklabels, rotation=45)
    leg = plt.legend()

    for l in leg.get_lines():
        l.set_alpha(1)

    plt.tight_layout()
    plt.savefig("humid.pdf")

    fig, ax = plt.subplots(figsize=(5,2))
    plt.boxplot(durations, vert=False, bootstrap=5000, meanline=True, showmeans=True, showfliers=True)
    ax.set_yticks([])
    ax.set_xticks([np.min(durations),10,15,20,25,30,35, 40, np.max(durations)])
    plt.grid()
    ax.set_xlabel("Hand washing duration in s")
    plt.tight_layout()
    plt.savefig("hw_stats.pdf")

    fig, ax = plt.subplots(figsize=(4,3))
    sns.lineplot(data=hws_concat, x="index", y="temp")
    plt.axvline(offset, color="green", label="begin of HW")
    for k, l in enumerate(end_offs):
        plt.axvline(l, c="orange", alpha=0.15, label=None if k != 0 else "end of HW")
    ax.set_ylabel("temperature change in °K")
    ax.set_xlabel("time in s")

    ticks = np.linspace(0 , offset + after, 11)
    ticklabels = [int(x) for x in ((ticks - offset) // 50)]
    ax.set_xticks(ticks, ticklabels, rotation=45)
    ax.set_ylim(-2,2)
    leg = plt.legend()

    for l in leg.get_lines():
        l.set_alpha(1)
    plt.tight_layout()
    plt.savefig("temp.pdf")

    fig, ax = plt.subplots(figsize=(4,3))
    sns.lineplot(data=hws_concat, x="index", y="press")
    plt.axvline(offset, color="green", label="begin of HW")
    for k, l in enumerate(end_offs):
        plt.axvline(l, c="orange", alpha=0.15, label=None if k != 0 else "end of HW")
    ax.set_ylabel("pressure change in hPa")
    ax.set_xlabel("time in s")

    ticks = np.linspace(0 , offset + after, 11)
    ticklabels = [int(x) for x in ((ticks - offset) // 50)]
    ax.set_xticks(ticks, ticklabels, rotation=45)
    ax.set_ylim(-2,2)
    leg = plt.legend()

    for l in leg.get_lines():
        l.set_alpha(1)
    plt.tight_layout()
    plt.savefig("press.pdf")


    for ind in range(len(start_pos)):
        fig, ax1 = plt.subplots(figsize=(10,3))
        
        #color = 'tab:red'
        #ax1.set_xlabel('time (s)')
        #ax1.set_ylabel('exp', color=color)
        #ax1.plot(t, data1, color=color)
        #ax1.tick_params(axis='y', labelcolor=color)
        
        try:
            hws[ind][['acc_x', 'acc_y', 'acc_z']].iloc[3500:7500].plot(linewidth=0.75, ax=ax1)
        except:
            continue
        ax2 = ax1.twinx()  # instantiate a second Axes that shares the same x-axis
        
        
        #color = 'tab:blue'
        #ax2.set_ylabel('sin', color=color)  # we already handled the x-label with ax1
        #ax2.plot(t, data2, color=color)
        #ax2.tick_params(axis='y', labelcolor=color)
        
        hws[ind][['humid']].iloc[3500:7500].plot(ax=ax2, legend=False, c="red", linewidth=0.75, label="humidity")
        
        
        #hws[ind][['beacon']].iloc[3500:7500].plot(ax=ax3, legend=False, c="red", linewidth=0.75, label="humidity")
        
        #ax3.spines.right.set_position(("axes", 1.2))
        
        plt.axvline(offset, c="chocolate", linestyle="--", label="begin HW")
        plt.axvline(end_pos.index[ind] + offset - start_pos.index[ind], c="maroon", linestyle="--", label="end HW")
        ax2.legend(["humidity", "begin HW", "end HW"],loc=1)
        ax1.legend(["Acc " + x for x in "xyz"],loc=2)
        ax2.set_ylim(-50,25)
        ax2.set_ylabel("Humidity in %-points changed")
        ax1.set_ylabel("Accelerometer in mm/s²")
        ax1.set_xticklabels([-40, -30, -20, -10, 0, 10, 20, 30, 40, 50, ])
        ax1.set_xlabel("time since beginning of hand wash in s")
        ax3 = ax1.twinx()
        (-hws[ind][['beacon']].iloc[3500:7500]).plot(ax=ax3, legend=False, c="navy", linewidth=1, label="beacon")
        ax3.set_ylim(-5,280)
        ax3.spines.right.set_position(("axes", 1.1))
        ax3.set_ylabel("Beacon signal RSSI in ASU")
        ax3.legend(["Beacon"],loc=4)
        fig.tight_layout()  # otherwise the right y-label is slightly clipped
        plt.savefig(f"plots/exampleHW_{ind}.pdf", bbox_inches="tight")
