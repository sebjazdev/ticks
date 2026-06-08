# python3 -m pip install shiny yfinance matplotlib pandas datetime
from shiny import App, render, ui, reactive
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date

# Define the list of available tickers
AVAILABLE_TICKERS = ['CADTHB=X', 'USDTHB=X', 'EURTHB=X', 'USDCAD=X', 'EURCAD=X', 'CADUSD=X', 'CADEUR=X', # FIAT
                     'BTC-USD', 'ETH-USD', 'XRP-USD', # CRYPTO
                     'PLTR', 'OPAI.PVT', 'ANTH.PVT', # AI
                     '^GSPC', '^SPX', 'SPY', 'IVV', 'VOO', 'VFIAX', # S&P 500
                     '^IXIC', '^NDX', 'QQQ', 'QQQM',  # NASDAQ
                     '^DJI', # DOW JONES
                     'VT', 'VTI', 'VGT', 'VYM', 'BLK', # VANGUARD
                     'BLK', # BLACKROCK
                     'DOL.TO', 'DLMAF', # DOLLARAMA
                     'ATD.TO', # COUCHETARD
                     'WMT', 'TGT', 'COST', 'BJ', 'KR', 'DG', # RETAIL
                     'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'META', 'AMZN', 'MSFT'] # TECH

# UI Definition
app_ui = ui.page_fluid(
    ui.panel_title(title="", window_title="Yahoo Finance Tickers"),
    ui.layout_sidebar(
        ui.sidebar(
            ui.input_date("start_date", ui.tags.b("Select Start Date"), value="2026-01-01"),
            # ui.input_checkbox("select_all", ui.tags.b("Select All/None"), value=False),
            ui.input_checkbox_group("tickers", ui.tags.b("Select Tickers"), choices={t: t for t in AVAILABLE_TICKERS}) # selected=AVAILABLE_TICKERS
        ),
        ui.output_plot("stock_plot"),
        ui.markdown("""
                    - FIAT        'CADTHB=X', 'USDTHB=X', 'EURTHB=X', 'USDCAD=X', 'EURCAD=X', 'CADUSD=X', 'CADEUR=X'
                    - CRYPTO      'BTC-USD', 'ETH-USD', 'XRP-USD'
                    - AI          'PLTR', 'OPAI.PVT', 'ANTH.PVT'
                    - S&P500      '^GSPC', '^SPX', 'SPY', 'IVV', 'VOO', 'VFIAX'
                    - NASDAQ      '^IXIC', '^NDX', 'QQQ', 'QQQM'
                    - DOWJONES    '^DJI'
                    - VANGUARD    'VT', 'VTI', 'VGT', 'VYM', 'BLK'
                    - BLACKROCK   'BLK'
                    - DOLLARAMA   'DOL.TO', 'DLMAF'
                    - COUCHETARD  'ATD.TO'
                    - RETAIL      'WMT', 'TGT', 'COST', 'BJ', 'KR', 'DG'
                    - TECH        'TSLA', 'NVDA', 'GOOGL', 'AAPL', 'META', 'AMZN', 'MSFT'
                     """)
    )
)

# Server Logic
def server(input, output, session):
    @reactive.Effect
    @reactive.event(input.select_all)
    def _():
        ui.update_checkbox_group("tickers", selected=AVAILABLE_TICKERS if input.select_all() else [])

    @reactive.Calc
    def data():
        selected_tickers = input.tickers()
        if not selected_tickers:
            return None
        
        start_date = input.start_date()
        end_date = date.today()
        
        # Fetches the closing prices for all specified tickers
        try:
            # list() ensures it's a list for yfinance
            df = yf.download(list(selected_tickers), start=start_date, end=end_date)
            
            if df.empty:
                return None
                
            # Handle different return structures of yfinance
            if len(selected_tickers) > 1:
                if 'Close' in df.columns.levels[0]:
                    return df['Close']
                else:
                    # In some versions/cases it might not be a MultiIndex if only one attribute is returned
                    return df['Close'] if 'Close' in df.columns else df
            else:
                # Single ticker case
                if 'Close' in df.columns:
                    return df['Close']
                return df

        except Exception as e:
            print(f"Error downloading data: {e}")
            return None

    @render.plot
    def stock_plot():
        df = data()
        selected_tickers = list(input.tickers())
        
        if df is None or len(selected_tickers) == 0:
            fig, ax = plt.subplots()
            ax.text(0.5, 0.5, "No tickers selected or no data available", ha='center', va='center')
            return fig

        # Ensure df is a DataFrame for consistent iteration
        if isinstance(df, pd.Series):
            df = df.to_frame()
            # If single ticker, the column name might be 'Close' or the ticker itself
            # We rename it to the ticker name for the loop below
            df.columns = [selected_tickers[0]]

        fig, ax = plt.subplots(figsize=(10, 10))

        for ticker in selected_tickers:
            if ticker not in df.columns:
                continue
                
            prices = df[ticker].dropna()
            if prices.empty:
                continue
            
            # MAX Calculation
            max_val = prices.max()
            max_date = prices.idxmax()
            
            # TODAY Most recent available
            today_val = prices.iloc[-1]
            today_date = prices.index[-1]

            # Plot the line
            line, = ax.plot(prices.index, prices, label=ticker, linewidth=1.0)
            color = line.get_color()

            # Highlight MAX
            ax.scatter(max_date, max_val, color='red', zorder=5, s=40)
            ax.annotate(
                f"Max {ticker} : {max_date:%Y-%m-%d}, {max_val:.2f}", 
                (max_date, max_val), 
                xytext=(5, 10), 
                textcoords="offset points", 
                ha='right',
                fontweight='bold', 
                color='red',
                fontsize=8
            )
            
            # Highlight TODAY
            ax.scatter(today_date, today_val, color='blue', zorder=5, s=40)
            ax.annotate(
                f"Today {ticker} : {today_date:%Y-%m-%d}, {today_val:.2f}", 
                (today_date, today_val), 
                xytext=(5, -15), 
                textcoords="offset points",
                ha='right',
                fontweight='bold', 
                color='blue',
                fontsize=8
            )
            
        ax.set_title('Yahoo Finance Tickers', fontsize=10, fontweight='bold')
        ax.set_xlabel('Date', fontsize=10, fontweight='bold')
        ax.set_ylabel('Value', fontsize=10, fontweight='bold')
        ax.tick_params(axis='both', labelsize=8)
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend(loc='upper left')
        plt.tight_layout()
        
        return fig

app = App(app_ui, server)
