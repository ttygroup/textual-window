"""Config file for Nox sessions
By Edward Jazzhands - 2025

NOTE ABOUT NOX CONFIG:
If you are doing dev work in some kind of niche environment such as a Docker
container or on a server, you might not have symlinks available to you.
In that case, you can set `nox.options.reuse_existing_virtualenvs = True

Setting `nox.options.reuse_existing_virtualenvs` to True will make Nox
reuse environments between runs, preventing however many GB of data from
being written to your drive every time you run it. (Note: saves environments
between runs of Nox, not between sessions of the same run).

If you do not need to reuse existing virtual environments, you can set
`nox.options.reuse_existing_virtualenvs = False` and `DELETE_VENV_ON_EXIT = True`
to delete the virtual environments after each session. This will ensure that
you do not have any leftover virtual environments taking up space on your drive.
Nox would just delete them when starting a new session anyway.
"""

import nox
import pathlib
import shutil

# PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]
PYTHON_VERSIONS = ["3.9"]
MAJOR_TEXTUAL_VERSIONS = [5.1]

##############
# NOX CONFIG #
##############

nox.options.reuse_existing_virtualenvs = True
nox.options.stop_on_first_error = True
DELETE_VENV_ON_EXIT = False

if nox.options.reuse_existing_virtualenvs and DELETE_VENV_ON_EXIT:
    raise ValueError(
        "You cannot set both `nox.options.reuse_existing_virtualenvs`"
        "and `DELETE_VENV_ON_EXIT` to True (Technically this would not cause "
        "an error, but it would be pointless)."
    )

################
# NOX SESSIONS #
################

@nox.session(
    venv_backend="uv",
    python=PYTHON_VERSIONS,
)
@nox.parametrize("ver", MAJOR_TEXTUAL_VERSIONS)
def tests(session: nox.Session, ver: int) -> None:

    session.run_install(
        "uv",
        "sync",
        "--quiet",
        "--reinstall",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
        external=True,
    )

    # Running pip install after syncing will override any
    # packages that were installed by the sync command.
    # Calculate the next minor version for the upper bound
    major, minor = str(ver).split(".")
    next_minor = f"{major}.{int(minor)+1}"
    session.run_install(
        "uv", "pip", "install",
        f"textual>={ver},<{next_minor}.0",
        external=True,
    )
    session.run("uv", "pip", "show", "textual")
    # EXPLANATION: This will install the latest patch release for the specified minor version series (e.g., 5.1.x, 5.3.x, etc.)
    # by using textual>={ver},<{next_minor}.0. To test a new minor version, just add it to MAJOR_TEXTUAL_VERSIONS.
    # The last `uv pip show textual` is just for logging purposes.

    # These are all assuming you have corresponding
    # sections in your pyproject.toml for configuring each tool:
    session.run("ruff", "check", "src")       
    session.run("mypy", "src")                
    session.run("basedpyright", "src")
    session.run("pytest", "tests", "-vvv") 

    # This code here will make Nox delete each session after it finishes.
    # This might be preferable to allowing it all to accumulate and then deleting
    # the folder afterwards (for example if testing would use dozens of GB of data and
    # you don't have the disk space to store it all temporarily).
    session_path = pathlib.Path(session.virtualenv.location)
    if session_path.exists() and session_path.is_dir() and DELETE_VENV_ON_EXIT:
        shutil.rmtree(session_path)
