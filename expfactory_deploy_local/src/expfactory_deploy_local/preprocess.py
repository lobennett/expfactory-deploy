import json
import polars as pl


def rename_task(task_name: str) -> str:
    """Rename a task to a BIDS-compliant name.

    Args:
        task_name (str): The name of the task to rename.

    Returns:
        str: The BIDS-compliant name of the task.
    """
    task_rename_mappings = {
        "ax_cpt_rdoc__fmri": "axCPT",
        "cued_task_switching_rdoc__fmri": "cuedTS",
        "flanker_rdoc__fmri": "flanker",
        "go_nogo_rdoc__fmri": "goNogo",
        "n_back_rdoc__fmri": "nBack",
        "operation_only_span_rdoc__fmri": "opOnlySpan",
        "operation_span_rdoc__fmri": "opSpan",
        "simple_span_rdoc__fmri": "simpleSpan",
        "spatial_cueing_rdoc__fmri": "spatialCueing",
        "spatial_task_switching_rdoc__fmri": "spatialTS",
        "stop_signal_rdoc__fmri": "stopSignal",
        "stroop_rdoc__fmri": "stroop",
        "visual_search_rdoc__fmri": "visualSearch",
    }
    return task_rename_mappings.get(task_name, task_name)


def create_events_file(data: str, bids_datafile: str) -> pl.DataFrame:
    """Create a BIDS events file from the raw data.

    Args:
        data (str): The raw data as a JSON string.
        bids_datafile (str): The path to the BIDS events file to save.

    Returns:
        pl.DataFrame: The BIDS events data as a Polars DataFrame.
    """
    data = json.loads(data)
    trialdata = json.loads(data["trialdata"])

    flattened_data = []
    for trial in trialdata:
        flat_trial = {}
        for key, value in trial.items():
            if isinstance(value, (dict, list)):
                flat_trial[key] = json.dumps(value)
            else:
                flat_trial[key] = value
        flattened_data.append(flat_trial)

    df = pl.DataFrame(flattened_data)
    start_trial = df.filter(pl.col("trial_id") == "fmri_wait_block_trigger_start")
    start_trial_end = start_trial.select("time_elapsed").to_series()[0]

    # Create a mask that becomes True at fmri_wait_block_trigger_end
    # and stays True thereafter
    mask = (pl.col("trial_id") == "fmri_wait_block_trigger_end").cum_max()
    events_df = df.filter(mask)
    events_df = events_df.with_columns(
        (pl.col("time_elapsed") - start_trial_end - pl.col("block_duration")).alias(
            "onset"
        )
    )

    events_df.write_csv(bids_datafile, separator="\t")
    print(f"Saved events datafile to: {bids_datafile}")
    return events_df
