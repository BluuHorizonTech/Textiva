# Textiva

> **Type less. Say more.**

A tiny text expander for Windows that turns shortcuts into full text — **anywhere you type**.

Type:

```text
brb + Tab
```

Get:

```text
Be right back
```

## Features

* Expand text anywhere
* Trigger with **Tab, Space, Enter, or punctuation**
* Lightweight & simple
* Easy `triggers.json` configuration
* Windows startup support

## Quick Start

```bash
pip install keyboard pywin32
python text_expander.py
```

For best compatibility, run as **Administrator**.

### Add your shortcuts

`triggers.json`

```json
{
  "brb": "Be right back",
  "sp": "Hey!",
  "@@": "you@email.com",
  "sig": "Best regards,\nYour Name"
}
```

That's it. 

## Start with Windows

```bash
python text_expander.py --install-startup
```

Remove it with:

```bash
python text_expander.py --uninstall-startup
```

```bash
# Install the only dependency
pip install keyboard

# Run as Administrator (right-click → Run as admin)
python text_expander.py

# Install to startup (auto-runs hidden on every login)
python text_expander.py --install-startup

# Remove from startup
python text_expander.py --uninstall-startup
```

## For Developers

### Requirements
```bash
pip install keyboard pyinstaller
```

### Run from source
```bash
python main.py
```

### Build exe manually
```bash
pyinstaller typeflow.spec
```

### Release a new version
```bash
# 1. Bump version
echo "1.2.3" > version.txt
git add version.txt
git commit -m "chore: bump version to 1.2.3"

# 2. Tag it — this triggers the pipeline automatically
git tag v1.2.3
git push origin main --tags
```

The GitHub Actions pipeline will automatically:
- Build `TypeFlow.exe`
- Build `TypeFlow-Setup-1.2.3.exe`  
- Create a GitHub Release with both files attached
- Generate a changelog from your commit messages

---

## Like Textiva?

If Textiva saves you a few keystrokes (or a few headaches 😄), you can buy me a coffee:

<p align="center">

<a>
  <img src="https://img.buymeacoffee.com/button-api/?text=Buy%20me%20a%20coffee&emoji=%E2%98%95&slug=yourusername&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff" />
</a><br>
Buy Me a Coffee is coming soon for India.
Until then, feel free to email me and say hi. 👋

</p>

⭐ **Star the repo** if you find it useful!

---

Made with ☕ and fewer keystrokes.
