from flask import Flask, request, render_template, jsonify, send_file, Blueprint
import sqlite3
import os
import json
from datetime import datetime, timedelta
from contextlib import closing
from common import execution_sql, read_ini
from server import display_newsapp

bp = Blueprint('maintenance', __name__)

DATABASE_NAME, SERVER_URL, NEWS_FOLDER, logger = read_ini()

@bp.route("/admin")
def maintenance_index():
    try:
        # アプリカテゴリの取得
        app_sql = create_app_sql()
        apps_data = execution_sql(app_sql)
        
        # ニュース情報の取得
        news_sql = create_news_sql()
        news_data = execution_sql(news_sql)
        print(f"news_data:{news_data}")
        news_data = create_status(news_data)
        news_data = create_url(news_data)
        
        return render_template('maintenance.html', news_data=news_data, apps_data=apps_data)
    except Exception as e:
        logger.error(f"(maintenance_index): {e}")

@bp.route("/register", methods=["POST"])
def register_news():
    try:
        dic = {}
        for key, value in request.form.items():
            k = str(key.split("_")[1])
            if k not in dic.keys():
                dic[k] = {}
                
            if key.startswith("news"):
                dic[k]["news"] = json.loads(value)
                
        for key in request.files:
            k = str(key.split("_")[1])
            if k not in dic.keys():
                dic[k] = {}        
            
            if key.startswith("file"):
                dic[k]["file"] = request.files[key]
                
                
        
        with closing(sqlite3.connect(DATABASE_NAME)) as conn:
            cursor = conn.cursor()
            for val in dic.values():
                news = val['news']
                file = None
                if "file" in val:
                    file = val["file"]
                    
                # ディレクトリが存在しない場合は作成
                if not os.path.exists(NEWS_FOLDER):
                    os.makedirs(NEWS_FOLDER)
                    
                if file is not None:
                    # 現在の日時を取得
                    now = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    base, extension = os.path.splitext(file.filename)
                    file_name = f"{base}_{now}{extension}"
                    
                    if os.path.exists(os.path.join(NEWS_FOLDER, file_name)):
                        count = 1
                        while os.path.exists(os.path.join(NEWS_FOLDER, file_name)):
                            count += 1
                            file_name = f"{base}_{now}{count}{extension}"
                    
                    # ファイル名をリネーム
                    news['current']['9'] = file_name
                    
                app_id = select_appID(cursor, news['current']['0'])
                if news['newRow']:
                    insert_sql, params = create_insert_sql(news)
                    cursor.execute(insert_sql, params)
                    news_id = cursor.lastrowid
                    id_mgmt_sql = "INSERT INTO ID_Mgmt (NewsID, AppID) VALUES (?, ?)"
                    cursor.execute(id_mgmt_sql, (news_id, app_id))
                else:
                    update_sql, params = create_update_sql(news)
                    cursor.execute(update_sql, params)
                    id_mgmt_sql = "Update ID_Mgmt SET AppID = ? Where NewsID = ?"
                    cursor.execute(id_mgmt_sql, (app_id, news['current']['8']))
                    
                # ファイルのアップロード
                if file:
                    # ファイル名と日付を結合
                    filename = os.path.join(NEWS_FOLDER, file_name)
                    file.save(filename)
                    
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"(register_news): {e}")
        return jsonify({"status": "error", "message": str(e)})
    
# アプリIDの取得
def select_appID(cursor, category):
    try:
        app_id_sql = "Select id from App_Mgmt Where AppCategory = ?"
        cursor.execute(app_id_sql, (category,))
        app_id = cursor.fetchone()[0]

        return app_id
    except Exception as e:
        logger.error(f"(select_appID): {e}")
        
# ステータスの追加
def create_status(news_data):
    try:
        data = []
        for row in news_data:
            # 指定した日付
            specified_date_str = row[4]
            specified_date = datetime.strptime(specified_date_str, "%Y-%m-%d")
            
            li = list(row)
            li[4] = specified_date.strftime("%Y-%m-%d")

            # 公開期間の日数を加える
            days_to_add = row[5]
            end_date = specified_date + timedelta(days=days_to_add)

            # 現在の日付を取得
            current_date = datetime.now()

            # 非表示フラグ
            hidden_flg = row[7]

            # 現在日付が公開期間内かどうかを判断
            if specified_date < current_date < end_date and hidden_flg == 0:
                li.append("掲載中")
            elif end_date < current_date or hidden_flg == 1:
                li.append("掲載終了")
            else:
                li.append("")

            data.append(li)

        return data
    except Exception as e:
        logger.error(f"create_status:{e}")

# アプリカテゴリ用SQL文の作成
def create_app_sql():
    try:
        sql = """
        SELECT AppCategory From App_Mgmt;
        """
        return sql
    except Exception as e:
        logger.error(f"(create_app_sql): {e}")

# 登録済みニュースの取得用SQL文の作成
def create_news_sql():
    try:
        sql = """
        SELECT App_Mgmt.AppCategory, News_Mgmt.Category, News_Mgmt.Title, News_Mgmt.Year, News_Mgmt.PublicationDate, 
        News_Mgmt.Deadline, News_Mgmt.News_FileName, News_Mgmt.EndFlag, News_Mgmt.ID, News_Mgmt.Old_News_FileName
        FROM News_Mgmt 
        JOIN ID_Mgmt 
        ON News_Mgmt.ID = ID_Mgmt.NewsID 
        JOIN App_Mgmt 
        ON ID_Mgmt.AppID = App_Mgmt.ID; 
        """
        return sql
    except Exception as e:
        logger.error(f"(create_news_sql): {e}")

# ニュース登録用SQL文の作成
def create_insert_sql(news):
    try:
        sql = """
        INSERT INTO News_Mgmt (Category, Title, Year, PublicationDate, Deadline, EndFlag, Old_News_FileName)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (news['current']['1'], news['current']['2'], news['current']['3'], news['current']['4'], news['current']['5'], news['current']['7'], news['current']['9'])
        return sql, params
    except Exception as e:
        logger.error(f"(create_insert_sql): {e}")
        return None, None

# ニュース更新用SQL文の作成
def create_update_sql(news):
    try:
        sql = """
        UPDATE News_Mgmt SET Category = ?, Title = ?, Year = ?, PublicationDate = ?, Deadline = ?, EndFlag = ?, Old_News_FileName = ?
        WHERE ID = ?
        """
        params = (news['current']['1'], news['current']['2'], news['current']['3'], news['current']['4'], news['current']['5'], news['current']['7'], news['current']['9'], news['current']['8'])
        
        print(sql)
        print(params)
        return sql, params
    except Exception as e:
        logger.error(f"(create_update_sql): {e}")
        return None, None


# リンク押下時、新規タブに表示
@bp.route('/open/<filename>')
def open_file(filename):
    try:
        logger.debug(os.path.join(NEWS_FOLDER, filename))
        return send_file(os.path.join(NEWS_FOLDER, filename), as_attachment=False)
    except Exception as e:
        logger.error(f"open_file: {e}")

# URLの作成
def create_url(news_data):
    try:
        li = []
        for data in news_data:
            data = list(data)
            data[6] = SERVER_URL + "/open/" + data[6]
            if data[9] is not None:
                data[9] = SERVER_URL + "/open/" + data[9]
            li.append(data)

        return li
    except Exception as e:
        logger.error(f"(create_url): {e}")
        
# 本番掲載ボタン押下時の処理
@bp.route("/update_production", methods=["POST"])
def update_production_news():
    try:
        news = json.loads(request.form['news'])
        file = request.files.get('file', None)

        with closing(sqlite3.connect(DATABASE_NAME)) as conn:
            cursor = conn.cursor()

            # ファイルのアップロード処理
            if file:
                now = datetime.now().strftime('%Y%m%d%H%M%S%f')
                base, extension = os.path.splitext(file.filename)
                file_name = f"{base}_{now}{extension}"

                if not os.path.exists(NEWS_FOLDER):
                    os.makedirs(NEWS_FOLDER)

                if os.path.exists(os.path.join(NEWS_FOLDER, file_name)):
                    count = 1
                    while os.path.exists(os.path.join(NEWS_FOLDER, file_name)):
                        count += 1
                        file_name = f"{base}_{now}{count}{extension}"

                news['6'] = file_name
                file.save(os.path.join(NEWS_FOLDER, file_name))

            update_sql = """
                UPDATE News_Mgmt 
                SET Category = ?, Title = ?, Year = ?, PublicationDate = ?, Deadline = ?, EndFlag = ?, News_FileName = ?, Old_News_FileName = ?
                WHERE ID = ?
            """
            params = (news['1'], news['2'], news['3'], news['4'], news['5'], news['7'], news['6'], "", news['8'])
            cursor.execute(update_sql, params)
            conn.commit()

        return jsonify({"status": "success"})
    except Exception as e:
        logger.error(f"(update_production_news): {e}")
        return jsonify({"status": "error", "message": str(e)})

@bp.route('/news/<mode>')
def move_news(mode):
    try:
        return display_newsapp(mode)
    except Exception as e:
        logger.error(f"(move_news): {e}")
