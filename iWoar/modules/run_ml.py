import seaborn as sns
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from glob import glob

from tqdm.auto import tqdm
from imblearn.over_sampling import RandomOverSampler

from sklearn.model_selection import LeaveOneOut
from sklearn.model_selection import train_test_split as tts

from sklearn.ensemble import RandomForestClassifier as RFC
from sklearn.svm import SVC
from sklearn.metrics import *



results_list = []
pers_res_list = []
dummy_res_dict  = {}
pers_dummy_res_dict = {}
rs = RandomOverSampler()
clfs = []

def run(l_dfs):
    n_repetitions = 5
    n_estimators = 250
    for k in tqdm(range(n_repetitions)):
        for window_size in [125, 250]: 
            run_loso(l_dfs, sensors=['acc_x', 'acc_y', 'acc_z'], n_estimators=n_estimators, window_size=window_size)
            run_loso(l_dfs, sensors=['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y','gyro_z'], n_estimators=n_estimators, window_size=window_size)
            run_loso(l_dfs, sensors=['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y','gyro_z','temp'], n_estimators=n_estimators, window_size=window_size)
            run_loso(l_dfs, sensors=['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y','gyro_z','press'], n_estimators=n_estimators, window_size=window_size)
            run_loso(l_dfs, sensors=['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y','gyro_z','humid'], n_estimators=n_estimators, window_size=window_size)
            run_loso(l_dfs, sensors=['acc_x', 'acc_y', 'acc_z', 'humid', "press", 'temp'], n_estimators=n_estimators, window_size=window_size)
            run_loso(l_dfs, sensors=sensors, n_estimators=n_estimators, window_size=window_size)
    results_spl_df = pd.DataFrame(results_list, columns=["part.", "window size", "n_estimators", "f1", "acc","sensors"])
    dummy_df = pd.DataFrame(dummy_res_dict["250"], columns=["part.", "strategy", "acc", "f1"])
    dummy_df["window size"] = 250
    dummy2_df = pd.DataFrame(dummy_res_dict["125"], columns=["part.", "strategy", "acc", "f1"])
    dummy2_df["window size"] = 125
    dummy_df = pd.concat([dummy_df, dummy2_df]).reset_index(drop=True)
    pers_dummy_df = pd.DataFrame(pers_dummy_res_dict["125"], columns=["part.", "strategy", "acc", "f1"])
    pers_dummy_df.max()

    pers_dummy_df = pd.DataFrame(pers_dummy_res_dict["250"], columns=["part.", "strategy", "acc", "f1"])
    pers_dummy_df.max()
    pers_res_df = pd.DataFrame(pers_res_list, columns=["part.", "window size", "n_estimators", "f1", "acc","sensors"])
    results_spl_df.to_csv("results_loso.csv")
    pers_res_df.to_csv("results_personalized.csv")
    
np.random.seed(42)


# Function to create windows
def create_windows(df, window_size, label_column, sensors=["acc_x"]):
    windows = []
    labels = []
    for start in range(0, len(df) - window_size + 1, window_size):
            window = df.iloc[start:start + window_size]
            windows.append(window[sensors])
            labels.append(window[label_column].mode().iloc[0])  # Taking the most frequent label in the window
    
    return windows, labels

# Function to calculate basic features
def calculate_basic_features(window):
    features = {}
    for column in window.columns:
        if column not in ['id', 'time']:  # Exclude non-numeric columns
            mean = window[column].mean()
            features[f'{column}_mean'] = mean
            features[f'{column}_std'] = window[column].std()
            features[f'{column}_max'] = window[column].max()
            features[f'{column}_min'] = window[column].min()
            features[f'{column}_slope'] = window[column].iloc[-1] - window[column].iloc[0]
            features[f'{column}_median'] = window[column].quantile()
            features[f'{column}_iqr'] = window[column].quantile(0.75) - window[column].quantile(0.25)
            features[f'{column}_avgCross'] = np.sum((window[column].to_numpy()[:-1]>mean) != (window[column].to_numpy()[1:]>mean))
            features[f'{column}_skewness'] = skew(window[column].to_numpy())
            features[f'{column}_kurtosis'] = kurtosis(window[column].to_numpy())
            if (np.isnan(features[f'{column}_skewness'])):
                features[f'{column}_skewness'] = 0
            if (np.isnan(features[f'{column}_kurtosis'])):
                features[f'{column}_kurtosis'] = 0
    return features


def run_loso(dfs, window_size=150, sensors=["acc_x"], n_estimators=250, personalize=False):
    global Xs, ys
    Xs, ys = [], []
    #print("creating labels")
    for i, df in enumerate(dfs):
        conf_str = str(window_size) + str(i)
        win, lab = winlab_dict.get(conf_str, (None, None))

        if win is None:
            win, lab = create_windows(df, window_size, "binlabel", sensors=all_sensors)
            winlab_dict[conf_str] = (win, lab)

        feat_df = winlab_dict.get(conf_str+"feat", None)
        if feat_df is None:
            feat = [calculate_basic_features(window) for window in win]
            feat_df = pd.DataFrame(feat)
            winlab_dict[conf_str+"feat"] = feat_df
        # filter feature list
        active_features = [le for le in feat_df.columns if True in [se in le for se in sensors]]
        X = feat_df[active_features]
        #print(X.shape)
        y = pd.Series(lab)
        Xs.append(X)
        ys.append(y)
    #print(sensors, active_features)
    Xs = np.array(Xs, dtype=object)
    ys = np.array(ys, dtype=object)
    cv = LeaveOneOut()
    #print("Training & testing cross-validation")
    train_dummies = dummy_res_dict.get(str(window_size), None) is None
    if train_dummies:
        d_res_l = []
    
    for i, (train_ind, test_ind) in enumerate(cv.split(Xs)):
        X_tr = pd.concat(Xs[train_ind])
        y_tr = pd.concat(ys[train_ind])
        #print(X_tr.shape, y_tr.shape)
        X_te =  pd.concat(Xs[test_ind])
        y_te =  pd.concat(ys[test_ind])
        scaler = StandardScaler().set_output(transform="pandas")
        X_tr = scaler.fit_transform(X_tr)
        X_res, y_res = rs.fit_resample(X_tr, y_tr)
        model = RFC(n_estimators=n_estimators, n_jobs=14, oob_score=f1_score)
        model.fit(X_res, y_res)
        clfs.append(model)
        preds = model.predict(scaler.transform(X_te))
        f1 = f1_score(y_te, preds)
        acc = accuracy_score(y_te, preds)
        print(f"{sensors} - F1: {f1}, ACC: {acc}")
        #ConfusionMatrixDisplay.from_predictions(y_te, preds)
        results_list.append([i, window_size, n_estimators, f1, acc, str(sensors)])
        run_personalized(i, X_te, y_te, window_size, n_estimators, sensors, train_dummies)
        
        if train_dummies:
             for entry in trainDummies(y_tr, y_te, i):
                 d_res_l.append(entry)
    if train_dummies:
        dummy_res_dict[str(window_size)] = d_res_l


def trainDummies(y_tr, y_te, i):
    strategies = ['stratified', 'most_frequent', 'prior', 'uniform', 'constant']
    constant_value = 1
    res_l = []
    for strategy in strategies:
        if strategy == 'constant':
            dummy_clf = DummyClassifier(strategy=strategy, constant=constant_value)
        else:
            dummy_clf = DummyClassifier(strategy=strategy)
        dummy_clf.fit(y_tr, y_tr)
        y_pred = dummy_clf.predict(y_te)

        # Evaluate using different metrics (choose the one that makes sense for your problem)
        accuracy = accuracy_score(y_te, y_pred)
        f1 = f1_score(y_te, y_pred)
        res_l.append([i, strategy, accuracy, f1])
    return res_l


def run_personalized(i, X, y, window_size, n_estimators, sensors, train_dummies):
    X_train, X_te, y_train, y_te = tts(X, y, stratify=y, test_size=0.33)
    scaler = StandardScaler().set_output(transform="pandas")
    X_train = scaler.fit_transform(X_train)
    X_res, y_res = rs.fit_resample(X_train, y_train)
    model = RFC(n_estimators=n_estimators, n_jobs=14)
    model.fit(X_res, y_res)
    preds = model.predict(scaler.transform(X_te))
    f1 = f1_score(y_te, preds)
    acc = accuracy_score(y_te, preds)
    #print(f"Personalized: F1: {f1}, ACC: {acc}")
    #ConfusionMatrixDisplay.from_predictions(y_te, preds)
    pers_res_list.append([i, window_size, n_estimators, f1, acc, str(sensors)])
    if train_dummies:
        p_res_l = pers_dummy_res_dict.get(str(window_size), [])
        for entry in trainDummies(y_train, y_te, i):
             p_res_l.append(entry)
        pers_dummy_res_dict[str(window_size)] = p_res_l


def run_split():
    X = pd.concat(Xs)
    y = pd.concat(ys)
    X_tr, X_te, y_tr, y_te = tts(X,y, stratify=y)
    model = RFC()
    X_res, y_res = rs.fit_resample(X_tr, y_tr)
    model.fit(X_res, y_res)
    preds = model.predict(X_te)
    f1 = f1_score(y_te, preds)
    #print(f"F1: {f1}, ACC: {accuracy_score(y_te, preds)}")
    #ConfusionMatrixDisplay.from_predictions(y_te, preds)


sensors = ['acc_x', 'acc_y', 'acc_z', 'gyro_x', 'gyro_y',
       'gyro_z','temp', 'press', 'humid']
