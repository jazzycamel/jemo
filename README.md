# Jemo
A Python application than emulates Belkin WeMo devices for use with Amazon Alexa.

This project was originally based (heavily!) on [FauxMo](https://github.com/n8henrie/fauxmo).
The major difference is that Jemo uses [PyQt6](https://riverbankcomputing.com/software/pyqt/intro)
rather than [asyncio](https://docs.python.org/3/library/asyncio.html) as the framework for 
managing asynchronous network IO. Other differences include using YAML rather than JSON
for the configuration file format.

## Usage
Jemo uses [Poetry](https://python-poetry.org) to manage Python and dependencies. The
environment is created as follows:

```shell
$ poetry install
```

To run the application, first create a config file based on `config.yaml` and then
run the following command:

```shell
$ poetry run python src/cli.py -c <path to config file>
```

To set up Alexa:

1. Open the Amazon Alexa webapp to the [Smart Home](http://alexa.amazon.com/#smart-home) page
2. With Jemo running, click "Discover devices"
3. Ensure that your Jemo devices have been discovered and appear with their names in the web interface
4. Test by saying "Alexa, turn on [device name]"

## Build an executable
A single file executable can be created using PyInstaller by running the following command:

```shell
$ poetry run pyinstaller jemo.spec
```

This will create an executable in the `dist/` directory.

## pre-commit
### Setup
```shell
$ poetry run pre-commit install --install-hooks -t pre-commit -t pre-push
```

### Run manually
```shell
# Run the tools that would run before a git push, on only changed files
pre-commit run --hook-stage push

# Run a single tool on all files
pre-commit run --hook-stage manual <tool-id> --all-files

# Run a single tool on specific files
pre-commit run --hook-stage manual <tool-id> --files <files>
```