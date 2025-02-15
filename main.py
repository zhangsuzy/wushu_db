import os
import psycopg2
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域访问

# ✅ 获取数据库 URL
DATABASE_URL = os.environ.get("DATABASE_URL")
print(f"📌 DATABASE_URL: {DATABASE_URL}")


# ✅ 连接 PostgreSQL 数据库
def connect_db():
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL is not set!")
        return None
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='prefer')
        print("✅ 数据库连接成功！")
        return conn
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return None


# ✅ 初始化数据库
def initialize_database():
    conn = connect_db()
    if conn is None:
        print("❌ 无法初始化数据库，因为连接失败")
        return
    try:
        cursor = conn.cursor()

        # 创建新的穴位数据库表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acupoints (
                id SERIAL PRIMARY KEY,
                meridian TEXT NOT NULL,
                condition TEXT NOT NULL,
                method TEXT NOT NULL,
                technique TEXT NOT NULL,
                acupoints TEXT NOT NULL
            );
        """)
        conn.commit()
        print("✅ 数据库初始化完成！")
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
    finally:
        cursor.close()
        conn.close()


# ✅ 主页路由（用于测试 Flask 是否正常运行）
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


# ✅ 查询腧穴数据的 API
@app.route('/get_acupoints', methods=['GET'])
def get_acupoints():
    meridian = request.args.get('meridian')
    condition = request.args.get('condition')
    method = request.args.get('method')

    print(f"📌 Received request: meridian={meridian}, condition={condition}, method={method}")

    if not meridian or not condition or not method:
        return jsonify({"error": "缺少必要参数: meridian, condition, method"}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"error": "数据库连接失败"}), 500
    try:
        cursor = conn.cursor()

        if method == "四针法":
            query = """
                SELECT technique, acupoints FROM acupoints 
                WHERE meridian=%s AND condition=%s AND (method='二针法' OR method='四针法')
            """
            cursor.execute(query, (meridian, condition))
        else:
            query = """
                SELECT technique, acupoints FROM acupoints 
                WHERE meridian=%s AND condition=%s AND method=%s
            """
            cursor.execute(query, (meridian, condition, method))

        data = cursor.fetchall()
        results = [{'technique': d[0], 'acupoints': d[1]} for d in data]

        return jsonify({"status": "success", "results": results})
    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
        return jsonify({"error": "数据库查询失败"}), 500
    finally:
        cursor.close()
        conn.close()


# ✅ 运行 Flask 服务器
if __name__ == '__main__':
    initialize_database()
    port = int(os.environ.get("PORT", 9999))  # ✅ Render 可能分配端口 9999
    app.run(host='0.0.0.0', port=port, debug=True)
