# Riverscapes

EXPERIMENTAL. Takes the Riverscapes Graphql API code out of riverscapes-tools for simplicity. 

## Using UV

When you clone this repo you can get it set up quickly using [uv](https://github.com/astral-sh/uv). Uv is a tool that helps manage python virtual environments and dependencies. It is an alternative to `pipenv` and `poetry`.

Make sure you have `uv` installed. See the [installation instructions from uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation) for your operating system. 

Then you can set up the project with the following commands:

```bash
# In the root of the repository
uv sync
```

Now in VSCode you should have a `.venv` folder in the root with the correct python environment set up. If you don't see it immediately try reloading the window or restarting VSCode. You're looking for a version of python at the path: `.venv/bin/python`.

## Codespace instructions

1. Create the codespace labelled "Riverscapes API Codespace"
2. In VSCode Load the `RiverscapesAPI.code-workspace` workspace
3. In VSCode make sure to select the appropriate version of python (should show as `3.12.9 ('.venv')`)