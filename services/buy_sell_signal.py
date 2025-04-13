import json
import pandas as pd

def generate_signal(closing_prices, SHORT_TERM_SMA, LONG_TERM_SMA):
    df = pd.DataFrame(closing_prices, columns=['close'])
    df['SMA_50'] = df['close'].rolling(window=SHORT_TERM_SMA).mean()
    df['SMA_200'] = df['close'].rolling(window=LONG_TERM_SMA).mean()
    df['signal_binary'] = (df['SMA_50'] > df['SMA_200']).astype(int)
    
    df['crossover'] = df['signal_binary'].diff()

    crossovers = df[df['crossover'].isin([1, -1])].copy()
    print("Crossoversss")
    print(crossovers)
    crossovers['direction'] = crossovers['crossover'].apply(lambda x: "BUY" if x == 1 else "SELL")
    
    print("📈 Crossover data:", crossovers[['close', 'SMA_50', 'SMA_200', 'crossover', 'direction']])
    return crossovers

async def record_crossovers_into_mongodb(df, mongo_db):
    crossovers = df[df['crossover'].isin([1, -1])]
    if crossovers.empty:
        print("❌ No crossovers found in the data [mongodb].")
    else:
        for idx, row in crossovers.iterrows():
            direction = "BUY" if row['crossover'] == 1 else "SELL"
            response = json.dumps({
                "idx": idx,
                "price": row['close'],
                "direction": direction,
                "SMA_50": row['SMA_50'],
                "SMA_200": row['SMA_200'],
                "crossover": row['crossover']
            })
            print("📊 Crossover data:", response)

            mongo_db.crossovers.insert_one(json.loads(response))

async def record_crossovers_into_redis(redis_client, CROSSOVER_SIGNAL_CHANNEL, df):
    crossovers = df[df['crossover'].isin([1, -1])]
    if crossovers.empty:
        print("❌ No crossovers found in the data [redis].")
    else:
        for idx, row in crossovers.iterrows():
            direction = "BUY" if row['crossover'] == 1 else "SELL"
            response = json.dumps({
                "idx": idx,
                "price": row['close'],
                "direction": direction,
                "SMA_50": row['SMA_50'],
                "SMA_200": row['SMA_200'],
                "crossover": row['crossover']
            })
            print("📊 Crossover data:", response)

            subscribers = await redis_client.publish(CROSSOVER_SIGNAL_CHANNEL, response)
            print(f"📡 Published to Redis channel with {subscribers} subscribers.")
