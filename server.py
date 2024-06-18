from flask import Flask, request, render_template, jsonify, send_file, Blueprint
from logging import getLogger, DEBUG, INFO, ERROR, WARNING, Formatter, StreamHandler, FileHandler
import sqlite3
import os
import configparser
import json
from datetime import datetime, timedelta
from maintenance import bp
from common import logger, read_ini, execution_sql

app = Flask(__name__)
app.register_blueprint(bp)

@app.route('/news', methods=['POST', 'GET'])
def index():
    try:
        # POSTされたデータを格納
        if request.method == "POST":
            data = request.get_json()
            print(f"post data: {data}")
            # 環境変数'username'を取得
            #username = os.environ.get('username')
            username = "0bf"
            
            print(f"username: {username}")
            with open(f"temp//data_{username}.json", 'w') as f:
                json.dump(data, f)
            # ユーザのIDをクライアントに返す
            return jsonify({'username': username}), 200

        # 目次ページを作成
        elif request.method == "GET":

            username = request.args.get('username')
            with open(f"temp//data_{username}.json", 'r') as f:
                data = json.load(f)
            os.remove(f"temp//data_{username}.json")
            print(f"json data on GET: {data}")  # JSONデータを取得して表示

            # 過去掲載ニュースの取得
            filter_app_list = []
            # eVDI起動時はフィルターをかけた状態でニュースを抽出
            if data['from_batch'] == 1:
                for val in data['apps']:
                    filter_app_list.append(val[0])
                    
            previous_data = get_news(0, filter_app_list)
            previous_data_filtered = filter_items(previous_data)
            previous_data_filtered = create_url(previous_data_filtered)

            # フィルタ用アプリ名の取得
            apps_query = "SELECT DISTINCT AppCategory, Path FROM App_Mgmt;"
            apps_data = execution_sql(apps_query)

            # eVDI起動時
            if data['from_batch'] == 1:
                return render_template('index.html', news_data=data['news'], apps_data=apps_data, filter_apps=filter_app_list, previous_news_data=previous_data_filtered)
            # ショートカットからの起動時
            else:
                return render_template('index.html', news_data=data['news'], apps_data=apps_data, filter_apps=[], previous_news_data=previous_data_filtered)
    except Exception as e:
        logger.error(f"(index): {e}")

# フィルタ検索の処理
@app.route('/search', methods=['POST'])
def search():
    try:
        # 選択されたアプリ名の取得
        selected_apps = request.get_json()
        logger.info("(search) AppName Search Start...")
        logger.debug(f"(search) selected_apps: {selected_apps}")

        # 選択されたアプリ名に紐づくニュースを取得
        previous_data = get_news(0, selected_apps)
        new_news_data = get_news(1, selected_apps)

        # ファイルパスにファイルが存在するレコードのみを抽出
        previous_data_filtered = filter_items(previous_data)
        new_news_data_filtered = filter_items(new_news_data)

        # フィルタ用アプリ名の取得処理
        apps_query = "SELECT DISTINCT AppCategory, Path FROM App_Mgmt;"
        apps_data = execution_sql(apps_query)
        apps_data_filtered = filter_items(apps_data)

        return jsonify({
            'filtered_previous_data': previous_data_filtered,
            'filtered_new_data': new_news_data_filtered,
            'filtered_apps': apps_data_filtered
        }), 200
    except Exception as e:
        logger.error(f"(search): {e}")

# URLの作成
def create_url(news_data):
    try:
        li = []
        for data in news_data:
            data = list(data)
            data[2] = app.config['SERVER_URL'] + "/open/" + data[2]
            li.append(data)

        return li
    except Exception as e:
        logger.error(f"create_url: {e}")
        
# リンク押下時、新規タブに表示
@bp.route('/open/<filename>')
def open_file(filename):
    try:
        logger.debug(os.path.join(app.config['NEWS_FOLDER'], filename))
        return send_file(os.path.join(app.config['NEWS_FOLDER'], filename), as_attachment=False)
    except Exception as e:
        logger.error(f"open_file: {e}")

# 掲載用ニュースの取得処理
def get_news(news_type, filter_app_list=[]):
    try:
        if news_type == 1:
            sql = create_new_news(filter_app_list)
        else:
            sql = create_previous_news(filter_app_list)
        logger.debug(f"(get_news) sql: {sql}")
        rows = execution_sql(sql)
        return rows
    except Exception as e:
        logger.error(f"(get_news): {e}")


# 過去掲載ニュースのSQL文を作成
def create_previous_news(filter_app_list):
    try:
        sql = """
        SELECT App_Mgmt.AppCategory, App_Mgmt.Path, News_Mgmt.News_FileName, News_Mgmt.Category,
        News_Mgmt.Title, News_Mgmt.PublicationDate, News_Mgmt.Year
        FROM News_Mgmt
        JOIN ID_Mgmt
        ON News_Mgmt.ID = ID_Mgmt.NewsID
        JOIN App_Mgmt
        ON ID_Mgmt.AppID = App_Mgmt.ID
        WHERE TRUE
        """
        if filter_app_list:
            sql += " AND AppCategory IN ('" + "','".join(filter_app_list) + "')"
        return sql + ";"
    except Exception as e:
        logger.error(f"(create_previous_news): {e}")


# 新着ニュースのSQL文を作成
def create_new_news(filter_app_list):
    try:
        sql = """
        SELECT App_Mgmt.AppCategory, App_Mgmt.Path, News_Mgmt.News_FileName, News_Mgmt.Category,
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
        )
        """
        if filter_app_list:
            sql += " AND AppName IN ('" + "','".join(filter_app_list) + "')"
        return sql
    except Exception as e:
        logger.error(f"(create_new_news): {e}")

# ファイルパスにファイル名が存在するレコードを抽出
def filter_items(data):
    try:
        filtered_data = []
        for item in data:
            app_name = item[0]  # AppName
            app_path = item[1]  # Path
            if os.path.exists(app_path):
                filtered_data.append(item)
        return filtered_data
    except Exception as e:
        logger.error(f"(filter_items): {e}")

if __name__ == "__main__":
    # アプリケーションの起動時に一度だけ ini ファイルを読み込む
    app.config['DATABASE_NAME'], app.config['SERVER_URL'], app.config['NEWS_FOLDER'], logger = read_ini()
    app.run(debug=True)

