def format_output(prices: dict) -> None:
    """
    格式化輸出股票價格資訊
    
    Args:
        prices: 股票價格資訊字典
    """
    print("\n股票價格資訊:")
    print("-" * 80)
    print(f"{'股票代號':<15} {'價格':<15} {'時間戳記(UTC+8)'}")
    print("-" * 80)
    
    for symbol, data in prices.items():
        formatted_price = f"{data['currency']} {data['price']:.2f}"
        print(f"{symbol:<15} {formatted_price:<15} {data['timestamp']}")
    print("-" * 80)