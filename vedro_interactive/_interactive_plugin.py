import os
from enum import Enum, auto
from traceback import format_exception
from types import TracebackType
from typing import Any, Callable, Type, Union

import vedro
from rich import box
from rich.console import Console
from rich.prompt import Prompt as _Prompt
from rich.style import Style
from rich.table import Table
from rich.text import TextType
from vedro.core import Dispatcher, Plugin, PluginConfig
from vedro.events import (
    ArgParsedEvent,
    ArgParseEvent,
    ScenarioFailedEvent,
    ScenarioPassedEvent,
    ScenarioRunEvent,
    StartupEvent,
    StepFailedEvent,
    StepPassedEvent,
    StepRunEvent,
)

__all__ = ("Interactive", "InteractivePlugin",)


class Prompt(_Prompt):
    prompt_suffix = " ~ "


class WaitFor(Enum):
    NOTHING = auto()
    NEXT_STEP = auto()
    WHEN_STEP = auto()
    SCENARIO_END = auto()


def make_console() -> Console:
    return Console(highlight=False, force_terminal=True)


def make_prompt(prompt: TextType, **kwargs: Any) -> Any:
    return Prompt.ask(prompt, **kwargs)


class InteractivePlugin(Plugin):
    def __init__(self, config: Type["Interactive"], *,
                 console_factory: Callable[[], Console] = make_console,
                 prompt_factory: Callable[..., Any] = make_prompt) -> None:
        super().__init__(config)
        self._console_factory = console_factory
        self._prompt_factory = prompt_factory
        self._console: Console = None  # type: ignore
        self._interactive: bool = False
        self._wait_for = WaitFor.NOTHING

    def subscribe(self, dispatcher: Dispatcher) -> None:
        dispatcher.listen(ArgParseEvent, self.on_arg_parse) \
            .listen(ArgParsedEvent, self.on_arg_parsed) \
            .listen(StartupEvent, self.on_startup) \
            .listen(ScenarioRunEvent, self.on_scenario_run, priority=999) \
            .listen(StepRunEvent, self.on_step_run) \
            .listen(StepPassedEvent, self.on_step_passed) \
            .listen(StepFailedEvent, self.on_step_failed) \
            .listen(ScenarioPassedEvent, self.on_scenario_end, priority=999) \
            .listen(ScenarioFailedEvent, self.on_scenario_end, priority=999)

    def on_arg_parse(self, event: ArgParseEvent) -> None:
        event.arg_parser.add_argument("-I", "--interactive",
                                      action="store_true",
                                      default=self._interactive,
                                      help="Interactive mode")

    def on_arg_parsed(self, event: ArgParsedEvent) -> None:
        self._interactive = event.args.interactive

    def _create_legend(self) -> Table:
        table = Table(title="=== Interactive Mode ===",
                      title_style=Style(color="white", italic=True, bold=True),
                      border_style=Style(color="magenta"),
                      box=box.SIMPLE)
        table.add_column("Command", min_width=20)
        table.add_column("Description", min_width=35)

        table.add_row("(n)ext", "go before next step")
        table.add_row("(w)hen", "go before when step")
        table.add_row("(e)nd", "go before scenario end")
        table.add_row("(q)uit", "exit()")

        return table

    def on_startup(self, event: StartupEvent) -> None:
        if not self._interactive:
            return
        self._console = self._console_factory()
        self._console.print(self._create_legend())

    def on_scenario_run(self, event: ScenarioRunEvent) -> None:
        if not self._interactive:
            return
        subject = event.scenario_result.scenario.subject
        self._console.out(f"→ Scenario «{subject}»", style=Style(color="cyan"))

    def _ask_command(self) -> None:
        while self._interactive:
            try:
                result = self._prompt_factory("  ├", console=self._console)
            except KeyboardInterrupt:
                self._interactive = False
                return

            if result in ("n", "next"):
                self._wait_for = WaitFor.NEXT_STEP
                return
            elif result in ("w", "when"):
                self._wait_for = WaitFor.WHEN_STEP
                return
            elif result in ("e", "end"):
                self._wait_for = WaitFor.SCENARIO_END
                return
            elif result in ("q", "quit"):
                self._wait_for = WaitFor.NOTHING
                self._interactive = False
                self._console.out("  └─ exit()")
                exit(1)

    async def on_step_run(self, event: StepRunEvent) -> None:
        if not self._interactive:
            return
        self._console.out("  ┌ ", end="")
        self._console.out(f"> {event.step_result.step_name}", style=Style(color="grey50"))

        if self._wait_for == WaitFor.SCENARIO_END:
            return
        elif self._wait_for == WaitFor.WHEN_STEP:
            if not event.step_result.step_name.lower().startswith("when"):
                return
            self._wait_for = WaitFor.NOTHING

        self._ask_command()

    async def on_step_passed(self, event: StepPassedEvent) -> None:
        if not self._interactive:
            return
        self._console.out("  └ ", end="")
        self._console.out(f"✔ {event.step_result.step_name}", style=Style(color="green"))

    def _print_exception(self, exception: BaseException, traceback: TracebackType) -> None:
        root = os.path.dirname(vedro.__file__)
        while traceback.tb_next is not None:
            filename = os.path.abspath(traceback.tb_frame.f_code.co_filename)
            if os.path.commonpath([root, filename]) != root:
                break
            traceback = traceback.tb_next

        formatted = format_exception(type(exception), exception, traceback)
        self._console.out("".join(formatted), style=Style(color="yellow"))

    async def on_step_failed(self, event: StepFailedEvent) -> None:
        if not self._interactive:
            return
        self._console.out("  └ ", end="")
        self._console.out(f"✗ {event.step_result.step_name}", style=Style(color="red"))

        exc_info = event.step_result.exc_info
        if exc_info:
            self._print_exception(exc_info.value, exc_info.traceback)

    def on_scenario_end(self, event: Union[ScenarioPassedEvent, ScenarioFailedEvent]) -> None:
        if not self._interactive:
            return
        if self._wait_for == WaitFor.SCENARIO_END:
            self._ask_command()


class Interactive(PluginConfig):
    plugin = InteractivePlugin
