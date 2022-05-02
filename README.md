# Vedro Interactive

[![Codecov](https://img.shields.io/codecov/c/github/nikitanovosibirsk/vedro-interactive/master.svg?style=flat-square)](https://codecov.io/gh/nikitanovosibirsk/vedro-interactive)
[![PyPI](https://img.shields.io/pypi/v/vedro-interactive.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-interactive/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/vedro-interactive?style=flat-square)](https://pypi.python.org/pypi/vedro-interactive/)
[![Python Version](https://img.shields.io/pypi/pyversions/vedro-interactive.svg?style=flat-square)](https://pypi.python.org/pypi/vedro-interactive/)

## Installation

### 1. Install package

```shell
$ pip3 install vedro-interactive
```

### 2. Enable plugin

```python
# ./vedro.cfg.py
import vedro
import vedro_interactive

class Config(vedro.Config):

    class Plugins(vedro.Config.Plugins):

        class Interactive(vedro_interactive.Interactive):
            enabled = True
```

## Usage

### Run tests

```shell
$ vedro run -r silent -I
```
