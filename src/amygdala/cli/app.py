"""Typer app root."""

import typer

from amygdala.cli.commands.capture import capture
from amygdala.cli.commands.clean import clean
from amygdala.cli.commands.config import config_app
from amygdala.cli.commands.diff import diff
from amygdala.cli.commands.init import init
from amygdala.cli.commands.install import install
from amygdala.cli.commands.serve import serve
from amygdala.cli.commands.status import status
from amygdala.cli.commands.uninstall import uninstall

app = typer.Typer(
    name="amygdala",
    help="AI coding assistant memory system.",
    no_args_is_help=True,
)

app.command("init")(init)
app.command("capture")(capture)
app.command("status")(status)
app.command("diff")(diff)
app.command("install")(install)
app.command("uninstall")(uninstall)
app.command("serve")(serve)
app.command("clean")(clean)
app.add_typer(config_app)


def main() -> None:
    app()
