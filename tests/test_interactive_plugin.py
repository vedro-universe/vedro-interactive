from vedro.core import Plugin

from vedro_interactive import Interactive, InteractivePlugin


def test_interactive_plugin():
    plugin = InteractivePlugin(Interactive)
    assert isinstance(plugin, Plugin)
