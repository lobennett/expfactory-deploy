import argparse
import datetime
import os
import sys
import pandas as pd
import json

from pathlib import Path

from .utils import generate_experiment_context

import web
from web.contrib.template import render_jinja

web.config.debug = False

package_dir = os.path.dirname(os.path.abspath(__file__))

urls = ("/", "serve", "/serve", "serve", "/decline", "decline", "/reset", "reset")
app = web.application(urls, globals())
session = web.session.Session(
    app,
    web.session.DiskStore(Path(package_dir, "sessions")),
    initializer={"incomplete": None},
)

parser = argparse.ArgumentParser(description="Start a local deployment of a battery")
group = parser.add_mutually_exclusive_group()
group.add_argument(
    "exp_config",
    metavar="EXP_config",
    type=Path,
    help="Path to a single experiment or path to a configuration file. Configuration file should be a single path to an experiment per line.",
    nargs="?",
)
group.add_argument(
    "-e",
    "--exps",
    help="Comma delimited list of paths to experiments. Mutually exclusive with exp_config",
    type=lambda x: [Path(y) for y in x.split(",")],
)
parser.add_argument(
    "-gi",
    "--group_index",
    help="Inject a group_index variable into the experiment context.",
)

parser.add_argument(
    "-sub",
    "--subject-id",
    help="Include subject ID in filename of experiment outfile.",
)
parser.add_argument(
    "-ses",
    "--session-id",
    help="Include session ID in filename of experiment outfile",
)
parser.add_argument(
    "-run",
    "--run-id",
    help="Include run ID in filename of experiment outfile",
    default=1,
)


experiments = []

template_dir = Path(package_dir, "templates")
static_dir = Path(package_dir, "static/")
experiments_dir = Path(static_dir, "experiments/")
render = render_jinja(template_dir, encoding="utf-8")


def run(args=None):
    args = parser.parse_args(args)

    if args.exps is not None:
        experiments = args.exps
    elif args.exp_config is not None:
        if args.exp_config.is_file():
            with open(args.exp_config) as fp:
                experiments = [Path(x.strip()) for x in fp.readlines()]
        else:
            experiments = [args.exp_config]
    else:
        print("No valid experiment configuration provided.")
        parser.print_help()
        sys.exit(1)

    # Filter out non-existent experiments
    experiments = [e.resolve() for e in experiments if e.exists()]
    for e in experiments:
        if not e.exists():
            print(f"{e.absolute()} does not exist. Ignoring.")

    if len(experiments) == 0:
        print("No Experiments Found")
        sys.exit(1)

    experiments_dir.mkdir(parents=True, exist_ok=True)

    for experiment in experiments:
        experiment_name = experiment.stem or experiment.name
        symlink_target = experiments_dir / experiment_name

        if symlink_target.resolve() == experiments_dir.resolve():
            print(
                f"Invalid experiment name derived from {experiment}: symlink target cannot be the experiments directory itself."
            )
            continue

        try:
            os.symlink(experiment, symlink_target)
        except FileExistsError:
            if symlink_target.is_symlink() or symlink_target.is_file():
                symlink_target.unlink()
                os.symlink(experiment, symlink_target)
            elif symlink_target.is_dir():
                print(f"Cannot overwrite directory: {symlink_target}")
                continue
            else:
                print(f"Unexpected file type for {symlink_target}")
                continue

    # Create the AppConfig instance with parsed arguments and available experiments
    config = AppConfig(args, experiments)
    config.show_args()

    # Initialize the application with AppConfig in the context
    app.add_processor(web.loadhook(lambda: setattr(web.ctx, "config", config)))

    # Clear sys.argv if necessary before running the app
    sys.argv = []
    app.run()


def serve_experiment(experiment):
    exp_name = experiment.stem
    context = generate_experiment_context(
        Path(experiments_dir, exp_name), "/", f"/static/experiments/{exp_name}"
    )
    if web.config.get("group_index", None):
        context["group_index"] = web.config.group_index
    return render.deploy_template(**context)


class reset:
    def GET(self):
        session.kill()
        return '<html><body>Reset session, <a href="/">back to / </a></body></html>'


class serve:
    def GET(self):
        experiments = web.ctx.config.experiments
        if session.get("experiments") == None:
            session.experiments = [*experiments]
        if set(experiments) != set(session.experiments):
            session.experiments = [*experiments]
            session.incomplete = [*experiments]
        if session.get("incomplete") == None:
            session.incomplete = [*experiments]

        if len(session.incomplete) == 0:
            return render.finished()
        exp_to_serve = session.incomplete[-1]
        return serve_experiment(exp_to_serve)

    def POST(self):
        # get completion date
        date = datetime.datetime.utcnow().strftime("%y-%m-%d-%H:%M")
        json_output_file, bids_output_file = web.ctx.config.get_filename(date)

        with open(json_output_file, "ab") as fp:
            json_data = web.data()
            fp.write(json_data)
        web.header("Content-Type", "application/json")

        loaded_json_data = json.loads(json_data)
        trialdata = loaded_json_data["trialdata"]
        dict_trialdata = json.loads(trialdata)
        df = pd.DataFrame(dict_trialdata)
        df.to_csv(bids_output_file, index=False)

        # TODO: Maybe create events file from here directly?

        return "{'success': true}"


class decline:
    def GET(self, name):
        app.stop()


class AppConfig:
    def __init__(self, args, experiments):
        # Ensure subject_id starts with 's'
        self.subject_id = args.subject_id
        if self.subject_id and not self.subject_id.startswith("s"):
            self.subject_id = f"sub-{self.subject_id}"

        # Ensure session_id starts with 'ses' if necessary
        self.session_id = args.session_id
        if self.session_id and not self.session_id.startswith("ses-"):
            self.session_id = f"ses-{self.session_id}"

        self.run_id = args.run_id
        self.group_index = args.group_index
        self.experiments = experiments

        if len(self.experiments) == 1:
            task_id = os.path.basename(self.experiments[0])

            if "_rdoc" in task_id.lower():
                task_id = task_id.replace("_rdoc", "")

            self.task_id = task_id

        if self.session_id and self.subject_id:
            self.bids_outpath = (
                f"{self.subject_id}_{self.session_id}_run-{self.run_id}_events"
            )
        else:
            self.bids_outpath = None

    def get_filename(self, date):
        sub_raw_out = os.path.join("../output/raw", self.subject_id)
        sub_bids_out = os.path.join("../output/bids", self.subject_id)

        if not os.path.exists(sub_raw_out):
            os.makedirs(sub_raw_out)

        if not os.path.exists(sub_bids_out):
            os.makedirs(sub_bids_out)

        sub_ses_raw_out = os.path.join(sub_raw_out, self.session_id)
        if not os.path.exists(sub_ses_raw_out):
            os.makedirs(sub_ses_raw_out)

        sub_ses_bids_out = os.path.join(sub_bids_out, self.session_id)
        if not os.path.exists(sub_ses_bids_out):
            os.makedirs(sub_ses_bids_out)

        raw_out = os.path.join(sub_ses_raw_out, f"{self.bids_outpath}__{date}.json")
        bids_out = os.path.join(sub_ses_bids_out, f"{self.bids_outpath}.csv")

        return (raw_out, bids_out)

    def show_args(self):
        """
        Displays configuration (arguments)in the AppConfig instance.
        """

        config_data = {
            "subject_id": self.subject_id,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "bids_outpath": self.bids_outpath,
            "group_index": self.group_index,
            "experiments": [str(exp) for exp in self.experiments],
        }

        # Optionally, return the dictionary or print the values:
        print("\nAppConfig:")
        for key, value in config_data.items():
            print(f"{key}: {value}")
        print("\n")


if __name__ == "__main__":
    run()
