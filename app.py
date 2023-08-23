from flask import Flask, render_template, request
import os
import io
import sys
import yfinance as yf
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import matplotlib
from datetime import date
from datetime import datetime
import talib as ta
import base64

app = Flask(__name__)
matplotlib.use('Agg')

def analyze(symbol):
    symbol = symbol.upper()
    plt.ioff()
    #only takes data starting from last years first day until today
    #if it is a new stock, it will take data from the first day it is listed
    today = date.today()
    stock_data = yf.download(symbol, start=("2022-01-01"), end=today)
    stock_ticker = yf.Ticker(symbol)

    #we check if the stock is new or not
    if len(stock_data) < 300:
        data_old = False
    else:
        data_old = True

    df = pd.DataFrame(stock_data)
    df['DailyReturn'] = df['Close'].pct_change()
    df['Target'] = df['DailyReturn'].apply(lambda x: 1 if x > 0 else 0)
    df = df.dropna()

    #if data is old, use SMA_20, SMA_50, SMA_100
    if data_old:
        df["SMA_20"] = df["Close"].rolling(20).mean()
        df["SMA_50"] = df["Close"].rolling(50).mean()
        df["SMA_100"] = df["Close"].rolling(100).mean()
    # if data is new, use SMA_5, SMA_20
    else:
        df["SMA_5"] = df["Close"].rolling(5).mean()
        df["SMA_20"] = df["Close"].rolling(20).mean()

    #if data is old, use EMA_20, EMA_50, EMA_100
    if data_old:
        df["EMA_20"] = ta.EMA(df["Close"], timeperiod=20)
        df["EMA_50"] = ta.EMA(df["Close"], timeperiod=50)
        df["EMA_100"] = ta.EMA(df["Close"], timeperiod=100)
    # if data is new, use EMA_5, EMA_20
    else:
        df["EMA_5"] =  ta.EMA(df["Close"], timeperiod=5)
        df["EMA_20"] = ta.EMA(df["Close"], timeperiod=20)

    df["RSI"] = ta.RSI(df["Close"])

    fig, axs = plt.subplots(2, 1, gridspec_kw={"height_ratios": [3, 1]}, figsize=(10, 6))
    if data_old:
        axs[0].plot(df['Close'])
        axs[0].plot(df['SMA_20'], color='orange')
        axs[0].plot(df['EMA_20'], color='purple')
    else: 
        axs[0].plot(df['Close'])
        axs[0].plot(df['SMA_5'], color='orange')
        axs[0].plot(df['EMA_5'], color='purple')

    axs[1].axhline(y=70, color='r', linestyle='--')
    axs[1].axhline(y=30, color='g', linestyle='--')
    axs[1].plot(df['RSI'], color='orange')
    
    #Add explanation for colors
    axs[0].legend(['ClosingPrice', 'SMA_20', 'EMA_20'])
    axs[1].legend(['Overbought', 'Oversold', 'RSI'])

    #Add title and axis names
    axs[0].set_title(symbol)
    axs[0].set_xlabel('Date')
    axs[0].set_ylabel('Price')
    axs[1].set_xlabel('Date')
    axs[1].set_ylabel('RSI')
    axs[1].set_ylim([0, 100])

    plt.text(0.37, 0.99, "Last Day Closing Price: " + str(round(df['Close'][-1], 2)), transform=axs[0].transAxes , fontsize=10, verticalalignment='top')

    # Save the figure as a PNG image in memory
    buffer = io.BytesIO()  # Create an in-memory buffer
    plt.savefig(buffer, format='png')
    buffer.seek(0)  # Move the buffer's position to the beginning

    # Get the image data as a byte string
    image_data = buffer.getvalue()

    # Close the figure to free up resources
    plt.close()
    return image_data

@app.route('/', methods=['POST', 'GET'])
def home():
    query = request.form.get('query')
    if not query:
        image_binary = analyze("ATAKP.IS")
        image_base64 = base64.b64encode(image_binary).decode()
        return render_template('index.html', image = image_base64)
    else:
        last_query = query
        image_binary = analyze(query + ".IS")
        image_base64 = base64.b64encode(image_binary).decode()
        return render_template('index.html', image = image_base64)

if __name__ == "__main__":
    app.run(debug=True, host='localhost', port=5002)