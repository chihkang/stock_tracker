# Stock Tracker

從 Google Finance 和 Yahoo Finance 擷取即時股價的 Python 工具，支援多個交易所的股票價格查詢及匯率轉換，並具備智能交易時間判斷功能。

## 功能特點

- 多重數據源支援
  - Google Finance（主要數據源）
  - Yahoo Finance 台灣（備用數據源，支援特殊股票代碼如櫃買中心）
- 智能交易時間管理
  - 自動判斷各市場交易時間
  - 支援美股夏令/冬令時間自動切換
  - 僅在交易時段更新價格
- 即時匯率轉換
  - 自動從 Google Finance 獲取 USD-TWD 匯率
  - 匯率顯示至小數點後兩位
- 投資組合視覺化
  - 資產分配圓餅圖
  - 市場分布圓餅圖
  - 貨幣分布柱狀圖
  - 完整支援繁體中文顯示
- 模組化設計，易於擴充
- 支援多種交易所

## 系統需求

- Python 3.8 或更高版本
- pip (Python 套件管理器)
- venv (Python 虛擬環境工具)
- tzdata (時區資料)
- matplotlib (圖表生成，可選)

## 快速安裝

### 方法一：一鍵安裝（推薦）
```bash
# 移除舊的虛擬環境（如果存在）
rm -rf venv && \
# 創建新的虛擬環境
python3 -m venv venv && \
# 啟動虛擬環境
source venv/bin/activate && \
# 安裝依賴
pip install -r requirements.txt && \
# 安裝專案
pip install -e . && \
# 安裝圖表支援（可選）
pip install matplotlib && \
# 測試執行
python -m stock_tracker portfolio
```

### 方法二：逐步安裝
1. clone或下載專案：
```bash
git clone <repository-url>
cd stock_tracker
```

2. 建立並啟動虛擬環境：
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. 安裝依賴：
```bash
pip install -r requirements.txt
```

4. 安裝圖表支援（可選）：
```bash
pip install matplotlib
```

5. 安裝專案：
```bash
pip install -e .
```

## 使用方法

### 必要檔案設置

在使用程式前，需要在專案根目錄建立 `portfolio.json` 檔案，用於儲存投資組合資訊：

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
  ]
}
```

主要欄位說明：
- `totalValue`: 投資組合總值（TWD）
- `exchange rate`: USD-TWD 匯率
- `stocks`: 股票清單
  - `name`: 股票代號（格式：代號:市場）
  - `price`: 股票價格
  - `quantity`: 持股數量
  - `currency`: 貨幣（TWD 或 USD）
  - `lastUpdated`: 最後更新時間
  - `percentageOfTotal`: 佔投資組合比例

### 命令列介面

程式支援多種操作模式：

1. 更新並顯示完整投資組合：
```bash
python -m stock_tracker portfolio
```

2. 更新投資組合並生成視覺化圖表：
```bash
python -m stock_tracker portfolio --charts
```

3. 指定圖表輸出目錄：
```bash
python -m stock_tracker portfolio --charts --output-dir my_charts
```

4. 查詢特定股票即時價格：
```bash
python -m stock_tracker query TSLA:NASDAQ VTI:NYSEARCA 2330:TPE
```

5. 使用指定的投資組合檔案：
```bash
python -m stock_tracker portfolio --file my_portfolio.json
```

### 圖表功能

執行 `portfolio --charts` 命令會生成三種視覺化圖表：

1. **資產分配圖** (asset_allocation.png)
   - 顯示各個股票佔投資組合的比例
   - 使用圓餅圖呈現
   - 包含詳細的百分比標示

2. **市場分布圖** (market_distribution.png)
   - 顯示不同市場（如 NASDAQ、TPE 等）的投資分布
   - 使用圓餅圖呈現
   - 自動合併相同市場的持股

3. **貨幣分布圖** (currency_distribution.png)
   - 顯示不同貨幣（TWD、USD）的投資比例
   - 使用柱狀圖呈現
   - 包含精確的百分比數值

圖表特點：
- 完整支援繁體中文顯示
- 自動調整字體大小和位置
- 清晰的色彩區分
- 高解析度輸出 (300 DPI)
- 自動保存至指定目錄

### Python 程式中使用

1. 基本查詢功能：
```python
from stock_tracker import get_multiple_stock_prices, format_output

# 查詢多支股票
symbols = ["VTI:NYSEARCA", "TSLA:NASDAQ", "2330:TPE"]
prices = get_multiple_stock_prices(symbols)
format_output(prices)
```

2. 使用投資組合管理：
```python
from stock_tracker import PortfolioManager

# 初始化投資組合管理器
portfolio = PortfolioManager('portfolio.json')

# 更新價格
portfolio.update_prices()

# 顯示投資組合
portfolio.print_portfolio()

# 生成圖表（需要 matplotlib）
portfolio.generate_charts('output_dir')
```

## 資料夾結構

```
stock_tracker/
├── portfolio.json          # 投資組合設定檔（需自行創建）
├── .env                    # 環境變數設定（可選）
├── src/
│   └── stock_tracker/     # 主程式碼
├── tests/                 # 測試檔案
└── README.md             # 說明文件
```

## 配置檔案

### portfolio.json
投資組合設定檔，定義：
- 持有的股票清單
- 每支股票的數量和成本
- 匯率設定
- 更新時間記錄

### .env（可選）
環境變數設定：
```env
BASE_URL=https://www.google.com/finance/quote/
TIMEZONE=Asia/Taipei
USER_AGENT=Mozilla/5.0
REQUEST_TIMEOUT=10
MAX_RETRIES=3
```

## 交易時間管理

### 台灣股市（TPE/TWO）
- 交易時間：週一至週五 09:00-13:30 (UTC+8)
- 非交易時間的價格查詢會使用最後更新的價格

### 美國股市（NASDAQ/NYSE/NYSEARCA）
- 交易時間：週一至週五
  - 夏令時間：21:30-04:00 (UTC+8)
  - 冬令時間：22:30-05:00 (UTC+8)
- 自動根據日期判斷夏令/冬令時間
- 跨日交易自動處理

## 支援的交易所

- NASDAQ: 納斯達克（例如：TSLA:NASDAQ）
- NYSE: 紐約證券交易所（例如：AAPL:NYSE）
- NYSEARCA: NYSE Arca（例如：VTI:NYSEARCA）
- TPE: 台灣證券交易所（例如：2330:TPE）
- TWO: 台灣櫃買中心（例如：00687B.TWO）

## 開發指南

### 安裝開發依賴
```bash
pip install -e .[dev]
```

### 執行測試
```bash
pytest tests/
```

## 常見問題解決

### 1. 無法取得特定股票資訊
- 檢查是否在交易時間內
- 股票代號格式是否正確（例如：2330:TPE 或 00687B.TWO）
- 確認網路連接狀態

### 2. 匯率更新失敗
- 檢查網路連接
- 確認 Google Finance 服務可用性
- 系統會自動使用上次成功更新的匯率

### 3. 交易時間判斷
- 美股時間會自動根據夏令/冬令時間調整
- 可以使用 `format_market_hours()` 查看當前交易時間

### 4. 圖表顯示問題
- 確認已安裝 matplotlib
- 檢查中文字體是否正確安裝
- 確保輸出目錄具有寫入權限

## 更新記錄

### v0.1.3 (2024-10-25)
- 新增投資組合視覺化圖表功能
- 支援繁體中文圖表顯示
- 改進錯誤處理和日誌記錄
- 優化命令列介面

### v0.1.2
- 新增自動判斷夏令/冬令時間功能
- 改進交易時間管理
- 優化匯率顯示格式

### v0.1.1
- 新增 Yahoo Finance 數據源支援
- 新增交易時間檢查功能
- 新增即時匯率轉換

### v0.1.0
- 初始版本
- 支援多股票即時報價
- 支援台灣時區
- 模組化設計

## 授權

MIT License

## 貢獻指南

歡迎提交 Issue 或 Pull Request 來改善專案。提交前請確保：
1. 已完整測試新功能
2. 更新相關文檔
3. 遵循現有代碼風格