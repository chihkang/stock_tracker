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
- 模組化設計，易於擴充
- 支援多種交易所

## 系統需求

- Python 3.8 或更高版本
- pip (Python 套件管理器)
- venv (Python 虛擬環境工具)
- tzdata (時區資料)

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

4. 安裝專案：
```bash
pip install -e .
```

## 使用方法

### 命令列介面

更新並顯示完整投資組合：
```bash
python -m stock_tracker portfolio
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

## 數據來源

### Google Finance
- 主要數據來源
- 支援：
  - 大多數股票的即時報價
  - 即時匯率資訊
  - 主要市場指數

### Yahoo Finance 台灣
- 備用數據來源
- 特別支援：
  - 台灣櫃買市場特殊股票代碼
  - 當 Google Finance 無法取得資料時自動切換

## 支援的交易所

- NASDAQ: 納斯達克（例如：TSLA:NASDAQ）
- NYSE: 紐約證券交易所（例如：AAPL:NYSE）
- NYSEARCA: NYSE Arca（例如：VTI:NYSEARCA）
- TPE: 台灣證券交易所（例如：2330:TPE）
- TWO: 台灣櫃買中心（例如：00687B.TWO）

## 匯率轉換

- 自動從 Google Finance 獲取 USD-TWD 即時匯率
- 匯率顯示至小數點後兩位
- 自動轉換美股價格至新台幣
- 每次更新價格時自動更新匯率

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

## 更新記錄

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