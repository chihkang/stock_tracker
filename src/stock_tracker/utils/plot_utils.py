import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import os
# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # Mac 系統
# plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # Windows 系統
plt.rcParams['axes.unicode_minus'] = False  # 讓負號正確顯示
# 關閉 matplotlib 的 debug 訊息
plt.set_loglevel('WARNING')

def create_portfolio_plots(portfolio_data, output_dir='plots'):
    """生成投資組合視覺化圖表"""
    os.makedirs(output_dir, exist_ok=True)
    stocks = portfolio_data['stocks']
    
    # 準備資料
    names = [stock['name'] for stock in stocks]
    percentages = [stock['percentageOfTotal'] for stock in stocks]
    
    # 資產分配圓餅圖
    plt.figure(figsize=(10, 8))
    plt.pie(percentages, labels=names, autopct='%1.1f%%')
    plt.title('資產分配')
    plt.savefig(f'{output_dir}/asset_allocation.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # 市場分布
    market_dist = defaultdict(float)
    for stock in stocks:
        market = stock['name'].split(':')[1]
        market_dist[market] += stock['percentageOfTotal']
    
    markets = list(market_dist.keys())
    market_values = list(market_dist.values())
    
    plt.figure(figsize=(10, 8))
    plt.pie(market_values, labels=markets, autopct='%1.1f%%')
    plt.title('市場分布')
    plt.savefig(f'{output_dir}/market_distribution.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # 貨幣分布柱狀圖
    currency_dist = defaultdict(float)
    for stock in stocks:
        currency_dist[stock['currency']] += stock['percentageOfTotal']
    
    currencies = list(currency_dist.keys())
    currency_values = list(currency_dist.values())
    
    plt.figure(figsize=(10, 6))
    plt.bar(currencies, currency_values)
    plt.title('貨幣分布')
    plt.ylabel('佔比 (%)')
    
    for i, v in enumerate(currency_values):
        plt.text(i, v, f'{v:.1f}%', ha='center')
    
    plt.savefig(f'{output_dir}/currency_distribution.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    return {
        'asset_allocation': f'{output_dir}/asset_allocation.png',
        'market_distribution': f'{output_dir}/market_distribution.png',
        'currency_distribution': f'{output_dir}/currency_distribution.png'
    }