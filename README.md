# Stock Tracker

A Python tool for retrieving real-time stock prices through market-routed providers, supporting stock price queries across multiple exchanges and currency conversion, with intelligent trading time detection and strict update health reporting.

## Architecture

```mermaid
graph TB
    subgraph "Configuration"
        A[".env File"] --> |Environment Variables| C[Stock Tracker Core]
        B1["GitHub GIST\nportfolio.json"] --> |Primary Source| C
        B2["Local\nportfolio.json"] --> |Fallback Source| C
    end

    subgraph "Data Sources"
        D1["Yahoo Taiwan Provider\n(TPE/TWO)"] --> |Market-routed Data| C
        D2["Yahoo Finance Provider\n(NASDAQ/NYSE/NYSEARCA)"] --> |Market-routed Data| C
        D3["Exchange Rate\nService"] --> |USD-TWD Rate| C
    end

    subgraph "Processing"
        C --> E[Trading Time Manager]
        C --> F[Portfolio Manager]
        C --> G[Data Fetcher]
        
        E --> |Time Validation| F
        G --> |Price Data| F
    end

    subgraph "Output"
        F --> H1[Console Output]
        F --> H2[Chart Generation]
        F --> H3[GIST Update]
        
        H2 --> I1["Asset Allocation\n(Pie Chart)"]
        H2 --> I2["Market Distribution\n(Pie Chart)"]
        H2 --> I3["Currency Distribution\n(Bar Chart)"]
    end

    subgraph "Automation"
        J[GitHub Actions] --> |Trigger| C
        J --> |Schedule| K["Regular Updates\n(Every specified time on weekdays)"]
        K --> |Update| B1
    end

    classDef configNode fill:#f9f,stroke:#333,stroke-width:2px
    classDef dataNode fill:#bbf,stroke:#333,stroke-width:2px
    classDef processNode fill:#bfb,stroke:#333,stroke-width:2px
    classDef outputNode fill:#fbb,stroke:#333,stroke-width:2px
    classDef autoNode fill:#ffb,stroke:#333,stroke-width:2px

    class A,B1,B2 configNode
    class D1,D2,D3 dataNode
    class C,E,F,G processNode
    class H1,H2,H3,I1,I2,I3 outputNode
    class J,K autoNode
```

## Features

- Market-Routed Data Sources
  - Yahoo Taiwan provider for Taiwan symbols such as `2330:TPE` -> `2330.TW`
  - Yahoo Finance provider for US symbols such as `AAPL:NASDAQ` -> `AAPL`
  - Provider routing is based on the exchange suffix instead of sending every symbol through the same fallback chain
- Intelligent Trading Time Management
  - Automatic market trading time detection
  - Support for US stock market DST/ST automatic switching
  - Price updates only during trading hours
- Real-time Currency Conversion
  - Automatic USD-TWD exchange rate through a no-key public JSON exchange-rate endpoint
  - Exchange rates displayed to two decimal places
- Portfolio Visualization
  - Asset allocation pie chart
  - Market distribution pie chart
  - Currency distribution bar chart
  - Full Traditional Chinese display support
- Modular design, easy to extend
- Support for multiple exchanges
- Strict update health reporting
  - `success`: all requested stock prices were updated
  - `partial_success`: some stock prices were updated and written back, but the GitHub Actions job exits non-zero
  - `failed`: no stock prices were updated; only `updateStatus` is written back

## System Requirements

- Python 3.8 or higher
- pip (Python package manager)
- venv (Python virtual environment tool)
- tzdata (timezone data)
- matplotlib (chart generation, optional)

## Quick Installation

1. Clone or download the project:

```bash
git clone <repository-url>
cd stock_tracker
```

2. Installation commands:

```bash
# Remove old virtual environment (if exists)
rm -rf venv && \
# Create new virtual environment
python3 -m venv venv && \
# Activate virtual environment
source venv/bin/activate && \
# Install dependencies
pip install -r requirements.txt && \
# Install project
pip install -e . && \
# Install chart support (optional)
pip install matplotlib && \
# Test execution
python -m stock_tracker portfolio
```

## Usage

### Required Configuration

Before using the program, you need to set up the following:

1. GitHub GIST Configuration (Primary Method):
   Create a `.env` file in the project root directory with your GitHub GIST credentials:

```env
GIST_ID=your_gist_id
GIST_TOKEN=your_github_personal_access_token
BASE_URL=https://www.google.com/finance/quote/
TIMEZONE=Asia/Taipei
USER_AGENT=Mozilla/5.0
REQUEST_TIMEOUT=10
MAX_RETRIES=3
```

2. Local Portfolio File (Fallback Method):
   Create a `portfolio.json` file in the project root directory to store portfolio information:

```json
{
  "totalValue": 6088899.07,
  "exchange rate": "32.08",
  "stocks": [
    {
      "name": "2330:TPE",
      "price": 1060.0,
      "quantity": 1000,
      "currency": "TWD",
      "lastUpdated": "2024-10-24T16:54:35+08:00",
      "percentageOfTotal": 17.41
    },
    {
      "name": "TSLA:NASDAQ",
      "price": 213.65,
      "quantity": 106,
      "currency": "USD",
      "lastUpdated": "2024-10-24T17:30:28+08:00",
      "percentageOfTotal": 11.93
    }
  ],
  "updateStatus": {
    "status": "success",
    "retrieved_at": "2026-05-04T15:20:00+08:00",
    "updatedSymbols": ["2330:TPE", "TSLA:NASDAQ"],
    "failedSymbols": [],
    "exchangeRate": {
      "status": "success",
      "usedPreviousRate": false,
      "rate": "32.08",
      "updatedAt": "2026-05-04T15:19:59+08:00"
    }
  }
}
```

The program will first try to read from the configured GIST, and if unavailable, will fall back to the local portfolio.json file.

### Update Status Metadata

`portfolio.json` includes a top-level `updateStatus` object so the GIST can report the health of the latest automation run:

- `status`: one of `success`, `partial_success`, or `failed`
- `retrieved_at`: when this update attempt ran
- `updatedSymbols`: symbols that received a fresh price during this run
- `failedSymbols`: concise symbol-level failures, using fixed reason codes plus an optional message
- `exchangeRate`: exchange-rate status; when the exchange-rate provider fails, the previous `exchange rate` and `exchange_rate_updated` values are kept and `usedPreviousRate` is `true`

Failure reason codes:

- `price_unavailable`
- `rate_unavailable`
- `provider_http_error`
- `provider_parse_error`
- `unsupported_symbol`
- `api_update_failed`
- `gist_read_failed`
- `gist_write_failed`

### GitHub Actions Integration

The repository includes GitHub Actions workflow for automated portfolio updates:

1. Create GitHub Secrets for your repository:
   - `GIST_ID`: Your GitHub GIST ID
   - `GIST_TOKEN`: Your GitHub Personal Access Token with gist scope

2. The workflow will automatically:
   - Run at scheduled intervals
   - Update portfolio data
   - Generate new charts
   - Update the GIST with latest data

The workflow intentionally uses strict success semantics:

- `success`: all requested stock symbols updated; the job exits `0`
- `partial_success`: at least one symbol updated and the GIST is written, but at least one symbol failed; the job exits non-zero
- `failed`: no symbols updated; only `updateStatus` is written to the GIST, and existing prices, totals, percentages, exchange rate, and `exchange_rate_updated` are preserved; the job exits non-zero

If the exchange-rate provider fails while stock prices are written, the previous exchange rate is reused. `exchange_rate_updated` is not changed, and `updateStatus.exchangeRate.message` records that the old rate was used.

Example workflow file (.github/workflows/update-portfolio.yml):

```yaml
name: Update Portfolio

on:
  schedule:
    - cron: '30 3 * * 1-5'  
    - cron: '30 5 * * 1-5'  
    - cron: '30 21 * * 0-5'
  workflow_dispatch:

env:
  GIST_ID: ${{ secrets.GIST_ID }}
  GIST_TOKEN: ${{ secrets.GIST_TOKEN }}

jobs:
  update-portfolio:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          
      - name: Cache pip packages
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-
            
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -e .
          
      - name: Check environment
        run: |
          echo "Checking environment variables..."
          if [ -n "$GIST_ID" ]; then
            echo "GIST_ID is set"
          else
            echo "GIST_ID is not set"
          fi
          if [ -n "$GIST_TOKEN" ]; then
            echo "GIST_TOKEN is set"
          else
            echo "GIST_TOKEN is not set"
          fi
          echo "Current directory: $(pwd)"
          echo "Directory contents:"
          ls -la
          
      - name: Update portfolio
        run: |
          echo "Starting portfolio update..."
          python -m stock_tracker portfolio -f --debug
        env:
          GIST_ID: ${{ secrets.GIST_ID }}
          GIST_TOKEN: ${{ secrets.GIST_TOKEN }}
          PYTHONPATH: ${{ github.workspace }}/src
          
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: portfolio-logs
          path: |
            logs/*.log
            *.log
```

### Command Line Interface

The program supports multiple operation modes:

1. Update and display complete portfolio:

```bash
python -m stock_tracker portfolio
```

2. Update portfolio and generate visualization charts:

```bash
python -m stock_tracker portfolio --charts
```

3. Specify chart output directory:

```bash
python -m stock_tracker portfolio --charts --output-dir my_charts
```

4. Query specific stock prices in real-time:

```bash
python -m stock_tracker query TSLA:NASDAQ VTI:NYSEARCA 2330:TPE
```

5. Use a specific portfolio file:

```bash
python -m stock_tracker portfolio --file my_portfolio.json
```

[Rest of the content remains the same as the original, including Chart Features, Python Usage, Directory Structure, Trading Time Management, Supported Exchanges, Development Guide, Troubleshooting, and Version History sections]

## License

MIT License

## Contributing

Feel free to submit Issues or Pull Requests to improve the project. Before submitting, please ensure:

1. New features are thoroughly tested
2. Documentation is updated
3. Existing code style is followed
