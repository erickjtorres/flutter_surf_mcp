# Flutter Surf MCP

Flutter Surf MCP is a MCP server that allows interactions with Flutter applications through client LLMs. It provides tools to inspect, control, and automate Flutter applications programmatically.

## Features

- Connect to running Flutter applications via VM Service
- Retrieve and inspect widget tree state
- Click on widgets
- Enter text into input fields
- Find widgets by text, key, or type
- Scroll widgets into view
- Perform scrolling actions with customizable parameters
- Toggle debug paint features

## Requirements

- Python 3.7+
- A running Flutter application with VM service enabled
- UV package manager (or pip)
- Claude AI with MCP support

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/flutter_surf_mcp.git
cd flutter_surf_mcp
```

2. Install dependencies:

```bash
uv pip install -r requirements.txt
```

## Configuration

To use Flutter Surf MCP with Claude, add the following configuration to your Claude AI settings:

```json
{
  "mcpServers": {
      "flutter_mcp": {
          "command": "[uv_directory]",
          "args": [
              "--directory",
              "[path]/flutter_surf_mcp",
              "run",
              "flutter_mcp.py"
          ]
      }
  }
}
```