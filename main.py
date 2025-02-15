import os
import psycopg2

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # 允许所有前端访问



# ✅ 打印 DATABASE_URL，确保环境变量正确
DATABASE_URL = "postgresql://postgres.eyedijnfvivvinvymjkv:Qweasdzxc123!@aws-0-ca-central-1.pooler.supabase.com:6543/postgres"os.environ["DATABASE_URL"] = DATABASE_URL
print(f"📌 DATABASE_URL: {DATABASE_URL}")


# ✅ 连接 Supabase PostgreSQL
def connect_db():
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL is not set!")
        return None

    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode='prefer')
        print("✅ 数据库连接成功！")
        return conn  # ✅ 必须返回 conn，否则 Flask 无法执行查询
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

        # ✅ 确保 `acupoints` 表存在
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS acupoints (
                id SERIAL PRIMARY KEY,
                meridian TEXT NOT NULL,
                category TEXT NOT NULL,
                name TEXT UNIQUE NOT NULL,
                code TEXT NOT NULL,
                indications TEXT,
                pairing TEXT,
                pairing_code TEXT
            );
        """)

        # ✅ 只在表为空时插入示例数据
        cursor.execute("SELECT COUNT(*) FROM acupoints;")
        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("""
                INSERT INTO acupoints (meridian, category, name, code, indications, pairing, pairing_code)
                VALUES ('肺经', '原穴', '太渊', 'LU9', '咳嗽、气喘', '列缺、尺泽', 'LU7、LU5')
                ON CONFLICT (name) DO NOTHING;
            """)
            print("✅ 已成功插入示例数据")

        conn.commit()
        print("✅ 数据库初始化完成！")

    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
    finally:
        cursor.close()
        conn.close()


# ✅ 主页路由（检查 Flask 是否正常运行）
@app.route('/', methods=['GET', 'HEAD'])
def index():
    if request.method == 'HEAD':
        return '', 200  # 处理 Render 健康检查
    return render_template('index.html')


# ✅ 查询腧穴数据的 API
@app.route('/get_acupoints', methods=['GET'])
def get_acupoints():
    meridian = request.args.get('meridian')
    category = request.args.get('category')

    print(f"📌 Received request: meridian={meridian}, category={category}")

    if not meridian or not category:
        return jsonify({"error": "Missing required parameters: meridian or category"}), 400

    conn = connect_db()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # ✅ 先检查 `acupoints` 表是否存在
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name=%s);", ('acupoints',))
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("❌ `acupoints` 表不存在")
            return jsonify({"error": "Database table does not exist"}), 500

        # ✅ 运行查询
        query = "SELECT name, code, indications, pairing, pairing_code FROM acupoints WHERE meridian=%s AND category=%s"
        cursor.execute(query, (meridian, category))
        data = cursor.fetchall()

        acupoints = [{'name': d[0], 'code': d[1], 'indications': d[2], 'pairing': d[3], 'pairing_code': d[4]} for d in
                     data]

        return jsonify({"status": "success", "acupoints": acupoints})

    except Exception as e:
        print(f"❌ 查询数据库失败: {e}")
        return jsonify({"error": "Database query failed"}), 500
    finally:
        cursor.close()
        conn.close()


# ✅ 运行 Flask 服务器
if __name__ == '__main__':
    initialize_database()  # ✅ 在 Flask 启动前，初始化数据库
    port = int(os.environ.get("PORT", 10000))  # ✅ Render 可能分配端口 10000
    app.run(host='0.0.0.0', port=port, debug=True)
