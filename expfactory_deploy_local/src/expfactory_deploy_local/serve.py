import argparse
import datetime
import json
import os
import sys
import urllib
from pathlib import Path
import socket

from .events import create_events_tsv, rename_exp_name
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
    "-raw",
    "--raw_dir",
    help="Directory to save raw files to. Default is ./raw.",
    type=Path,
    default=Path(os.getcwd(), "raw"),
)

parser.add_argument(
    "-bids",
    "--bids_dir",
    help="Directory to save BIDS events.tsv file to. Default is ./bids.",
    type=Path,
    default=Path(os.getcwd(), "bids"),
)

parser.add_argument(
    "-sub",
    "--subject_id",
    help="Subject ID to use for BIDS formatting",
    type=str,
    default=None,
)

parser.add_argument(
    "-ses",
    "--session_id",
    help="Session ID to use for BIDS formatting",
    type=str,
    default=None,
)

experiments = []

template_dir = Path(package_dir, "templates")
static_dir = Path(package_dir, "static/")
experiments_dir = Path(static_dir, "experiments/")
render = render_jinja(template_dir, encoding="utf-8")


def is_port_available(port):
    """Check if a port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("0.0.0.0", port))
            return True
        except socket.error:
            return False


def find_available_port(start_port=8080, max_attempts=20):
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    raise RuntimeError(
        f"No available ports found between {start_port} and {start_port + max_attempts - 1}"
    )


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
        print("Found arguments:")
        print(args)
        print()
        parser.print_help()
        sys.exit()

    dne = [
        print(f"{e.absolute()} Does not exist. Ignoring")
        for e in experiments
        if not e.exists()
    ]
    experiments = [e.absolute() for e in experiments if e.exists()]

    if len(experiments) == 0:
        print("No Experiments Found")
        sys.exit()

    for experiment in experiments:
        try:
            os.mkdir(experiments_dir)
        except FileExistsError:
            pass
        try:
            os.symlink(experiment, Path(experiments_dir, experiment.stem))
        except FileExistsError:
            os.unlink(Path(experiments_dir, experiment.stem))
            os.symlink(experiment, Path(experiments_dir, experiment.stem))

    web.config.update({"experiments": experiments})
    if args.group_index is not None:
        web.config.update({"group_index": args.group_index})

    # Adding new flags for output directories and subject info to web config
    web.config.update(
        {
            "raw_dir": args.raw_dir,
            "bids_dir": args.bids_dir,
            "subject": args.subject_id,
            "session": args.session_id,
        }
    )

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.bids_dir.mkdir(parents=True, exist_ok=True)

    # Use fixed port 8080
    port = 8080
    print(f"Starting server on port {port}")
    sys.argv = ["", f"{port}"]
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
        experiments = web.config.experiments
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
        exp_name = rename_exp_name(session.incomplete.pop().stem)
        date = datetime.datetime.now(datetime.UTC).strftime("%y-%m-%d-%H:%M")

        output_file = os.path.join(web.config.raw_dir, f"{exp_name}_{date}.json")

        with open(output_file, "ab") as fp:
            data = web.data()
            fp.write(data)

        if "survey" in exp_name:
            bids_file = os.path.join(
                web.config.bids_dir,
                f"sub-{web.config.subject}_ses-{web.config.session}_task-{exp_name}.tsv",
            )
        else:
            bids_file = os.path.join(
                web.config.bids_dir,
                f"sub-{web.config.subject}_ses-{web.config.session}_task-{exp_name}_events.tsv",
            )
        df = create_events_tsv(data, exp_name)
        df.to_csv(bids_file, index=False)
        web.header("Content-Type", "application/json")
        return "{'success': true}"


class decline:
    def GET(self, name):
        app.stop()


if __name__ == "__main__":
    run()
