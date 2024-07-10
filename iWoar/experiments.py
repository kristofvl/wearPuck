import modules.prepare
import modules.run_ml

all_dfs = modules.prepare.load_all_recs()

labeled_dfs = modules.prepare.apply_labels(all_dfs)

#modules.prepare.visualize_hws(labeled_dfs)

modules.run_ml.run(labeled_dfs)
