SELECT
    symbol,
    DATE(timestamp) AS trade_date,
    open,
    high,
    low,
    close,
    volume
FROM UNIFLOW.RAW.stock_data