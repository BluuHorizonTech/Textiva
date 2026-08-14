# TypeFlow

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

## Like TypeFlow?

If TypeFlow saves you a few keystrokes (or a few headaches 😄), you can buy me a coffee:

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
