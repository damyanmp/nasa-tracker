# NASA Tracker

NASA / space mission tracking CLI — ISS, Artemis, deep space probes, Mars rovers, and upcoming launches.

## Install

Open a **Terminal** (on Mac: press `Cmd + Space`, type "Terminal", press Enter).

Paste this single command and press Enter:

```sh
curl -fsSL https://raw.githubusercontent.com/damyanmp/nasa-tracker/main/install.sh | bash
```

> **What is `curl`?** It's a built-in tool that downloads files from the internet. This command downloads the install script and runs it. You can [read the script](install.sh) before running it.

The installer will:
1. Install `uv` (a fast Python package manager) if you don't have it
2. Download and install the `nasa` command

### After installing

Restart your terminal, then run:

```sh
nasa
```

## Update

Once installed:

```sh
nasa update
```

Or, if the `nasa` command is broken:

```sh
curl -fsSL https://raw.githubusercontent.com/damyanmp/nasa-tracker/main/update.sh | bash
```

Check what you have with `nasa version`.

## Usage

```
nasa                    # interactive TUI dashboard
nasa iss                # ISS position + world map
nasa artemis status     # latest Artemis mission + what's next
nasa artemis missions   # all Artemis missions (flown & planned)
nasa probes             # deep space probe fleet
nasa rovers             # Mars rover status
nasa launches           # upcoming launches
nasa update             # update to the latest version
nasa version            # show installed version
```
