import pandas as pd
import json
import warnings


def rename_exp_name(exp_name):
    rename_dict = {
        "ax_cpt_rdoc__fmri": "axCPT",
        "cued_task_switching_rdoc__fmri": "cuedTaskSwitching",
        "flanker_rdoc__fmri": "flanker",
        "go_nogo_rdoc__fmri": "goNogo",
        "n_back_rdoc__fmri": "nBack",
        "operation_only_rdoc__fmri": "operationOnly",
        "operation_span_rdoc__fmri": "operationSpan",
        "simple_span_rdoc__fmri": "simpleSpan",
        "spatial_cueing_rdoc__fmri": "spatialCueing",
        "spatial_task_switching_rdoc__fmri": "spatialTaskSwitching",
        "stop_signal_rdoc__fmri": "stopSignal",
        "stroop_rdoc__fmri": "stroop",
        "visual_search_rdoc__fmri": "visualSearch",
    }

    return rename_dict.get(exp_name, exp_name)


def create_events_tsv(data, exp_name):
    # Load data if data is a string
    if isinstance(data, str):
        with open(data, "r") as f:
            data = f.read()

    # Convert bytes to string if data is in bytes
    if isinstance(data, bytes):
        data = data.decode("utf-8")

    # Parse the string as JSON
    data = json.loads(data)

    if isinstance(data["trialdata"], str):
        trialdata = json.loads(data["trialdata"])
    else:
        trialdata = data["trialdata"]

    df = pd.DataFrame(trialdata)

    if "survey" in exp_name:
        return df

    # Instead get the first elapsed of the row after fmri_wait_block_trigger_end
    start = df.loc[df["trial_id"] == "fmri_wait_block_trigger_end"].index[0] + 1
    start = df.loc[start]["time_elapsed"]
    df["time_elapsed"] = df["time_elapsed"] - start
    # filter for rows with non negative time_elapsed
    df = df[df["time_elapsed"] >= 0]

    # Columns to keep
    common_columns = [
        "trial_id",
        "condition",
        "correct_trial",
        "response",
        "rt",
        "include_subject",
        "block_num",
        "time_elapsed",
        "stimulus_duration",
        "trial_duration",
        "diff",
    ]

    additional_columns = {
        "axCPT": [],
        "cuedTaskSwitching": [
            "cue",
            "task",
            "task_condition",
            "cue_condition",
            "CTI",
        ],
        "flanker": [],
        "goNogo": [],
        "nBack": ["delay"],
        "operationOnly": [
            "rt_each_spatial_location_response_grid",
            "rt_moving_each_spatial_location_response_grid",
            "spatial_sequence",
            "moving_order_spatial_location",
            "grid_symmetry",
        ],
        "operationSpan": [
            "rt_each_spatial_location_response_grid",
            "rt_moving_each_spatial_location_response_grid",
            "spatial_sequence",
            "moving_order_spatial_location",
            "grid_symmetry",
        ],
        "simpleSpan": [
            "rt_each_spatial_location_response_grid",
            "rt_moving_each_spatial_location_response_grid",
            "spatial_sequence",
            "moving_order_spatial_location",
        ],
        "spatialCueing": [],
        "spatialTaskSwitching": [],
        "stopSignal": ["SSD"],
        "stroop": [],
        "visualSearch": ["target_present", "num_stimuli"],
    }

    target_columns = common_columns + additional_columns.get(exp_name, [])
    existing_columns = [col for col in target_columns if col in df.columns]
    cleaned_df = df[existing_columns].copy()
    cleaned_df = cleaned_df.dropna(how="all")
    cleaned_df = cleaned_df.reset_index(drop=True)
    return cleaned_df


if __name__ == "__main__":
    df = create_events_tsv("./test_data/axCPT_24-11-25-21_58.json", "axCPT")
    df.to_csv("./test_data/axCPT_24-11-25-21_58.tsv", sep="\t", index=False)
    print(df)
