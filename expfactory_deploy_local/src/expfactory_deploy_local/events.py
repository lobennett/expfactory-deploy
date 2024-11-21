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

    return rename_dict[exp_name]


def create_events_tsv(data, exp_name):
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

    target_columns = common_columns + additional_columns[exp_name]
    existing_columns = [col for col in target_columns if col in df.columns]
    cleaned_df = df[existing_columns].copy()
    cleaned_df = cleaned_df.dropna(how="all")

    if "trial_id" in cleaned_df.columns:
        start_idx = cleaned_df[
            cleaned_df["trial_id"] == "fmri_wait_block_initial"
        ].index
        if len(start_idx) > 0:
            cleaned_df = cleaned_df.loc[start_idx[0] :].reset_index(drop=True)
    else:
        warnings.warn("No trial_id column found in the dataframe", UserWarning)

    return cleaned_df
