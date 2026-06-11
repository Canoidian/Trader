import os
import sys
import time
import logging
import random
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from krakentrader.api import get_tradable_pairs, get_historical_ohlcv
from krakentrader.analysis import calculate_sma, calculate_rsi, calculate_volatility

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'model.pkl')

def create_dataset():
    # Find all USD pairs
    all_pairs = list(get_tradable_pairs(['ZUSD', 'USD']).keys())
    sample_pairs = random.sample(all_pairs, min(40, len(all_pairs)))
    
    X = []
    y = []
    
    logging.info(f"Downloading historical data for {len(sample_pairs)} pairs to train ML model...")
    for pair in sample_pairs:
        try:
            ohlcv = get_historical_ohlcv(pair)
            if not ohlcv or len(ohlcv) < 50:
                continue
            closes = [float(row[4]) for row in ohlcv]
            
            # Generate features for each time step
            for i in range(50, len(closes) - 10):
                current_price = closes[i]
                future_prices = closes[i+1:i+11]
                max_future = max(future_prices)
                
                # We want to predict if the coin will pump by 1.5% in the next 10 minutes
                label = 1 if max_future > current_price * 1.015 else 0
                
                # Features
                slice_14 = closes[i-14:i+1]
                slice_30 = closes[i-30:i+1]
                
                sma_14 = calculate_sma(slice_14, 14)
                sma_30 = calculate_sma(slice_30, 30)
                rsi = calculate_rsi(slice_14, 14)
                volat = calculate_volatility(slice_14)
                
                if sma_14 is None or sma_30 is None or rsi is None:
                    continue
                    
                # Normalize features so they are comparable across different coins
                sma_14_diff = (current_price - sma_14) / sma_14
                sma_30_diff = (current_price - sma_30) / sma_30
                
                features = [sma_14_diff, sma_30_diff, rsi, volat]
                X.append(features)
                y.append(label)
                
        except Exception as e:
            logging.error(f"Error processing {pair}: {e}")
            
    return np.array(X), np.array(y)

def train_model():
    X, y = create_dataset()
    if len(X) < 100:
        logging.error("Not enough data to train model.")
        return
        
    logging.info(f"Training Random Forest on {len(X)} samples... Positive cases: {sum(y)}")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)
    
    accuracy = clf.score(X_test, y_test)
    logging.info(f"Model trained! Test Accuracy: {accuracy*100:.2f}%")
    
    joblib.dump(clf, MODEL_PATH)
    logging.info(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
