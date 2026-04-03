# TradeMind Lite

TradeMind Lite is an open-source U.S. stock technical analysis system that combines indicator analysis, candlestick pattern recognition, trend and pressure-level analysis, HTML reporting, and both CLI and Web workflows.

Current version: `Beta 0.3.4`

## Disclaimer

TradeMind Lite is a research and learning tool. Its analysis results are for reference only and must not be treated as investment advice, trading instructions, or risk-control guidance. Markets are risky, and all trading decisions remain your own responsibility.

## What This Project Does

TradeMind Lite focuses on technical analysis for U.S. equities and ETFs. The system can:

- analyze one or multiple tickers in batch
- calculate core indicators such as RSI, MACD, KDJ, Bollinger Bands, and volume-based signals
- detect candlestick patterns
- generate trading advice from combined signals
- estimate support/resistance and trend strength
- run built-in backtest calculations as part of the analysis pipeline
- generate HTML reports
- provide both an interactive terminal workflow and a browser-based workflow

## Highlights

- Dual interface: interactive CLI and Web UI
- Batch analysis: analyze multiple symbols in one run
- Watchlist support: grouped watchlists stored in JSON
- HTML reports: saved locally under `reports/stocks`
- Trend analysis: pressure levels, trend state, and ADX-related output
- Open source: distributed under GPL-3.0

## Screenshots

### Main Menu

<div align="center">
  <img src="https://github.com/user-attachments/assets/e2b1dcf3-f0e4-47a5-ae20-26b4f71ac95d" alt="TradeMind main menu" width="900" />
</div>

### Web Analysis Workflow

<div align="center">
  <img src="https://github.com/user-attachments/assets/9ea15bdb-7936-4dce-93e6-c6d6be9fcff1" alt="TradeMind web analysis screen" width="900" />
</div>

### Generated Report View

<div align="center">
  <img src="https://github.com/user-attachments/assets/c4b00dd6-8632-43d4-8f8c-2bf191c0ac43" alt="TradeMind HTML report" width="900" />
</div>

### Watchlist Editor

<div align="center">
  <img src="https://github.com/user-attachments/assets/df1786f7-27d6-47be-9437-57f2623a2220" alt="TradeMind watchlist editor" width="900" />
</div>

## Quick Start

If you only want the shortest working path:

```bash
git clone https://github.com/yagami1997/TradeMind.git
cd TradeMind
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python trademind.py
```

On Windows PowerShell, activate the environment with:

```powershell
venv\Scripts\Activate.ps1
```

## System Requirements

- Python `3.8+`
- Windows, macOS, or Linux
- Internet access for market data retrieval
- A modern browser for Web mode and HTML reports

## Installation Guide

The project is source-first. There is no packaged installer in this repository, so the recommended workflow is to create a virtual environment and install from `requirements.txt`.

### 1. Clone the Repository

```bash
git clone https://github.com/yagami1997/TradeMind.git
cd TradeMind
```

### 2. Create a Virtual Environment

#### Windows

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this once in a user shell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Upgrade `pip`

```bash
python -m pip install --upgrade pip
```

If your shell maps `python` to Python 2 or an unavailable interpreter, use `python3` instead.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Core runtime dependencies include:

- `rich` for the terminal UI
- `Flask` and `flask-cors` for the Web UI
- `yfinance`, `pandas`, `numpy`, and `scipy` for data and analysis
- `matplotlib`, `seaborn`, and `plotly` for reports and visualization

### 5. Verify the Environment

```bash
python --version
pip --version
```

Optional sanity check:

```bash
python -c "import rich, flask, yfinance, pandas, numpy; print('Environment OK')"
```

### Platform Notes

#### Windows

- Install Python from the official Python website and make sure `Add Python to PATH` is checked.
- If you use Command Prompt instead of PowerShell, activate the environment with:

```cmd
venv\Scripts\activate.bat
```

#### macOS

- If `python3` is missing, install it with Homebrew:

```bash
brew install python
```

- If some compiled packages fail, install Xcode command line tools:

```bash
xcode-select --install
```

#### Ubuntu / Debian

Install Python and common build tools first:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential git
```

## Running the Application

TradeMind Lite provides one main launcher and two shortcut entry scripts.

### Main Launcher

```bash
python trademind.py
```

This opens the main menu, where you can choose:

- `1` for CLI mode
- `2` for Web mode
- `q` to quit

### Launch CLI Mode Directly

```bash
python trademind.py --cli
```

Or use the shortcut:

```bash
python trademind_cli.py
```

### Launch Web Mode Directly

```bash
python trademind.py --web
```

You can also specify host and port:

```bash
python trademind.py --web --host 0.0.0.0 --port 3336
```

Or use the shortcut:

```bash
python trademind_web.py
```

## CLI Usage Guide

CLI mode is useful if you prefer terminal-driven analysis and quick report generation.

### CLI Menu Options

The CLI menu includes:

- analyze a single stock
- batch analyze multiple stocks
- view available watchlists
- open recent reports
- adjust analysis-related menu settings exposed by the CLI

### Analyze a Single Symbol

1. Start CLI mode.
2. Choose option `1`.
3. Enter a symbol such as `AAPL`.
4. Wait for the analysis to finish.
5. TradeMind Lite generates an HTML report and opens it in your browser.

### Analyze Multiple Symbols

1. Start CLI mode.
2. Choose option `2`.
3. Enter multiple symbols separated by spaces, for example:

```text
AAPL MSFT GOOGL NVDA
```

4. Wait for the analysis batch to complete.
5. The generated report is saved to `reports/stocks`.

### View Watchlists

Watchlists are loaded from:

`config/users/default/watchlists.json`

You can use CLI mode to inspect the available groups, or edit the JSON file directly if you want to manage symbols manually.

### View Historical Reports

TradeMind Lite stores generated HTML reports in:

`reports/stocks`

From CLI mode, you can browse recent reports and open them in your browser.

## Web Usage Guide

Web mode is the most convenient workflow for normal daily use.

### Starting the Web UI

Run:

```bash
python trademind.py --web
```

By default, the application starts a local server on port `3336`. In normal conditions, it will open the browser automatically.

If the browser does not open automatically, visit:

```text
http://localhost:3336
```

### Typical Web Workflow

1. Start Web mode.
2. Open the browser page.
3. Enter one or more symbols, or use an existing watchlist.
4. Start the analysis.
5. Wait for the progress indicator to finish.
6. Open the generated report from the results area or the recent reports list.

### Watchlist Management in Web Mode

The Web UI includes watchlist editing and import workflows. User watchlist data is stored under:

- `config/users/default/watchlists.json`
- `config/users/default/groups_order.json`
- `config/users/default/watchlist_edited.json`

This means your watchlist changes are persisted locally in the project directory.

## Output and File Locations

Important runtime directories:

- `reports/stocks`: generated HTML stock analysis reports
- `logs`: runtime logs for the analyzer, CLI, and Web server
- `config/users/default`: default user watchlists and ordering data
- `results`: additional generated artifacts used by the project

## How the Analysis Works

At a high level, TradeMind Lite does the following during analysis:

1. Downloads market data with `yfinance`.
2. Calculates technical indicators.
3. Detects candlestick patterns.
4. Generates trading advice and signal output.
5. Runs built-in backtest calculations on the generated signals.
6. Performs trend and pressure-level analysis.
7. Builds an HTML report and saves it locally.

## Data Source and Rate Limits

TradeMind Lite currently relies on Yahoo Finance data through `yfinance`.

This is practical and convenient, but it also means:

- requests can be rate-limited
- certain regions or networks may have access issues
- delayed or incomplete responses can happen

If data retrieval starts failing:

1. wait and retry later
2. reduce request frequency and batch size
3. verify that the symbol exists on Yahoo Finance
4. update `yfinance`
5. check whether your network or proxy setup is blocking Yahoo endpoints

Update command:

```bash
pip install --upgrade yfinance
```

## Troubleshooting

### `ModuleNotFoundError` when starting the app

The most common cause is that dependencies were not installed into the active virtual environment.

Fix:

```bash
pip install -r requirements.txt
```

Then retry:

```bash
python trademind.py
```

### Web UI does not open

- check whether the server is already running on the selected port
- open `http://localhost:3336` manually
- try a different port:

```bash
python trademind.py --web --port 5000
```

### Report was not generated

- check whether `reports/stocks` exists
- make sure the project directory is writable
- inspect log files under `logs`

### Stock data cannot be downloaded

- verify the symbol
- check your network
- retry later in case of Yahoo-side rate limiting
- update `yfinance`

### Environment activation fails on Windows

Use one of the correct activation commands:

```powershell
venv\Scripts\Activate.ps1
```

```cmd
venv\Scripts\activate.bat
```

## Project Structure

```text
TradeMind/
├── trademind.py              # Main launcher
├── trademind_cli.py          # CLI shortcut entry
├── trademind_web.py          # Web shortcut entry
├── trademind/                # Core package
│   ├── core/                 # Indicators, signals, patterns, trend logic
│   ├── backtest/             # Backtest engine
│   ├── data/                 # Data loading and watchlist helpers
│   ├── reports/              # HTML report generation
│   └── ui/                   # CLI and Web UI code
├── config/                   # Local user/watchlist configuration
├── reports/                  # Generated reports
├── logs/                     # Runtime logs
├── tests/                    # Test suite
├── docs/                     # Additional documentation
└── project_management/       # Development and decision records
```

## Release Notes

For detailed version history, see [RELEASE_NOTES.md](RELEASE_NOTES.md).

Recent release focus in `Beta 0.3.4`:

- UI color improvements
- ADX-related data display fixes
- report rendering and presentation improvements

## Development Notes

This repository also contains project-management and development-process documentation. That material is useful if you want to understand the evolution of the system, but it is separate from the normal user workflow.

## License

This project is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for the full text.

In short:

- you may study, modify, and redistribute the code
- derivative distributions must comply with GPL-3.0 obligations
- the software is provided as-is, without warranty

## Author Note

TradeMind Lite was originally written for my friends in China, so the software itself was designed as a Chinese-language product first. To make forking and secondary development easier for Chinese users, the development and project-management materials in this repository are also primarily written in Chinese. At this time, I do not plan to release official English or Japanese editions of the software, and I also do not plan to maintain an English edition of the development documentation.

Last updated: `2026-04-03 05:35:56 PDT`
