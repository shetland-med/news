import sqlite3
import os
import requests  
import webbrowser
import configparser
from contextlib import closing
import sys

news_query = """
SELECT
    App_Mgmt.AppCategory, App_Mgmt.Path, News_Mgmt.News_FileName, News_Mgmt.Category,
    News_Mgmt.Title, News_Mgmt.PublicationDate, News_Mgmt.Year
FROM News_Mgmt
JOIN ID_Mgmt
    ON News_Mgmt.ID = ID_Mgmt.NewsID
JOIN App_Mgmt
    ON ID_Mgmt.AppID = App_Mgmt.ID
WHERE
    App_Mgmt.endflag = 0 AND News_Mgmt.endflag = 0
    AND
    DATE(
        substr(PublicationDate, 1, instr(PublicationDate, '-') - 1) || '-' ||
        substr('0' || substr(PublicationDate, instr(PublicationDate, '-') + 1, instr(substr(PublicationDate, instr(PublicationDate, '-') + 1), '-') - 1), -2) || '-' || 
        substr('0' || substr(PublicationDate, instr(substr(PublicationDate, instr(PublicationDate, '-') + 1), '-') + instr(PublicationDate, '-') + 1), -2)
    )<= DATE('now') AND
    DATE('now') <= DATE(
        substr(PublicationDate, 1, instr(PublicationDate, '-') - 1) || '-' || 
        substr('0' || substr(PublicationDate, instr(PublicationDate, '-') + 1, instr(substr(PublicationDate, instr(PublicationDate, '-') + 1), '-') - 1), -2) || '-' || 
        substr('0' || substr(PublicationDate, instr(substr(PublicationDate, instr(PublicationDate, '-') + 1), '-') + instr(PublicationDate, '-') + 1), -2),
        '+' || Deadline || ' days'
    );
"""

from_batch = None

# SQL文を実行
def query_db(query, db_path):
    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
    return rows

# ファイルパスにファイル名が存在するレコードを抽出
def filter_items(data):
    filtered_data = []
    for item in data:
        app_name = item[0]  # AppName
        app_path = item[1]
        if os.path.exists(app_path):
            filtered_data.append(item)
            
    return filtered_data

# iniファイルの読み込み
def read_ini():
    config = configparser.ConfigParser()
    config.read('config.ini')
    server_url = config['SERVER']['ServerUrl']
    database_path = config['DATABASE']['db_path']
    return server_url, database_path

def main():
    global news_query
    server_url, database_path = read_ini()  # iniファイルの読み込み

    # 新着ニュースの取得
    news_data = query_db(news_query, database_path)
    # ファイルパスにファイルが存在するレコードのみを抽出
    filtered_news = filter_items(news_data)
    print(f"Filtered_news: {filtered_news}")

    # フィルタ用アプリ名の取得
    apps_query = "SELECT DISTINCT AppCategory, Path FROM App_Mgmt;"
    apps_data = query_db(apps_query, database_path)
    filtered_apps = filter_items(apps_data)
    print(f"Filtered_apps: {filtered_apps}")

    # JSON形式に格納
    headers = {'Content-Type': 'application/json'}
    data = {'news': filtered_news, 'apps': filtered_apps, 'from_batch': from_batch}

    # サーバ側にPOST
    response = requests.post(f"{server_url}/news", json=data, headers=headers)
    if response.status_code == 200:
        # サーバから返されたユーザのIDを取得
        username = response.json()['username']
        # ブラウザを起動し、HTMLを表示
        webbrowser.open(f"{server_url}/news?username={username}")

if __name__ == "__main__":
    # バッチからの起動かを判別
    if len(sys.argv) > 1:
        if sys.argv[1] == "1":
            from_batch = 1
        else:
            from_batch = 0
    else:
        from_batch = 0
    main()
