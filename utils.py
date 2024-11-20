import config
from db import Database

def find_configs(tf: str) -> list:
    res = db.execute_query(f'select * from configs where tf = "{tf}"')
    configs = []
    for row in res:
        config = {
            "id": row[0],
            "user_id": row[1],
            "account_id": row[2],
            "coin": row[3],
            "sl_on": row[4],
            "tp_on": row[5],
            "sl": row[6],
            "tp": row[7],
            "filter_ema": row[8],
            "fast_ema": row[9],
            "slow_ema": row[10],
            "filter_ema_on": row[11],
            "enable_long": row[12],
            "enable_short": row[13],
            "low_rsi": row[14],
            "high_rsi": row[15],
            "rsi_protection_for_long": row[16],
            "rsi_protection_for_short": row[17],
            "rsi_tp_long": row[18],
            "rsi_tp_short": row[19],
            "force_rsi_tp_for_long": row[20],
            "force_rsi_tp_for_short": row[21]
        }
        configs.append(config)
    return configs


db = Database(config.db_name)
db.connect()