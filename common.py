from logging import getLogger, DEBUG, INFO, ERROR, WARNING, Formatter, StreamHandler, FileHandler
import sqlite3
import os
import configparser
from contextlib import closing
from datetime import datetime

config = configparser.ConfigParser()
config.read('config.ini')
DATABASE_NAME = config['DATABASE']['db_path']
SERVER_URL = config['SERVER']['ServerUrl']
NEWS_FOLDER = config['NEWSFOLDER']['folder_path']

logger = None  # グローバルロガー変数の定義

# sql文の実行
def execution_sql(sql, params=[]):
    try:
        with closing(sqlite3.connect(DATABASE_NAME)) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return rows
    except Exception as e:
        logger.error(f"(execution_sql): {e}")
        
# iniファイルの読み込み
def read_ini():
    try:
        global DATABASE_NAME, SERVER_URL, NEWS_FOLDER, logger 
        logger = _setup_logger()

        return DATABASE_NAME, SERVER_URL, NEWS_FOLDER, logger 
    except Exception as e:
        logger.error(f"(read_ini): {e}")
        
# LOGファイルの出力設定
def _setup_logger(modname=__name__):
    logger = getLogger(modname)
    logger.setLevel(DEBUG)

    # stream (standard output)
    sh = StreamHandler()
    sh.setLevel(ERROR)
    formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    # logfile
    dt_now = datetime.now()
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    if not os.path.exists("log"):
        os.makedirs("log")
    
    log_file = "log/debug_" + dt_now.strftime("%Y%m%d-%H%M%S") + ".log"
    fh = FileHandler(log_file)
    fh.setLevel(DEBUG)
    fh_formatter = Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(fh_formatter)
    logger.addHandler(fh)
    
    return logger
