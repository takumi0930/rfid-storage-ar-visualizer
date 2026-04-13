import os
from flask import Flask, render_template,jsonify,request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from datetime import datetime
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


app = Flask(__name__)

# 絶対パスでデータベースを指定（Flask実行ディレクトリに依存しない）
db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "instance", "mydatabase.db")

# instanceフォルダが存在しない場合は作成
os.makedirs(os.path.dirname(db_path), exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# 外部キー制約を有効にする
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


# 商品情報テーブル
class ProductInformation(db.Model):
    __tablename__ = 'product_information'

    product_id = db.Column(db.String(50), nullable=False, primary_key=True)
    product_name = db.Column(db.String(200), nullable=False)
    model_url = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<ProductInformation {self.product_id}{self.product_name}{self.model_url}>'

# 現在格納中のRFID情報テーブル
class StoredProducts(db.Model):
    __tablename__ = 'stored_products'

    uid = db.Column(db.String(50), nullable=False,  primary_key=True)
    product_id = db.Column(db.String(200), db.ForeignKey('product_information.product_id'), nullable=False)

    product_information = db.relationship('ProductInformation', backref='stored_products')

    def __repr__(self):
        return f'<StoredProducts {self.uid}{self.product_id}>'

# DB初期化
with app.app_context():
  db.create_all()


#RFIDデータ受信API
@app.route('/api/log',methods=['POST'])
def api_log():
    data = request.get_json()
    if data.get('tagDetected'):
        
        uid = data.get('uid')
        product_id = data.get('product_id')
        
        if not uid or not product_id:
            return jsonify({'error':'uid or product_id is required'}),400
        
        try:
            # 既存データを全削除
            StoredProducts.query.delete()
            db.session.commit()

            # 新規登録
            product = StoredProducts(uid=uid, product_id=product_id)
            db.session.add(product)
            db.session.commit()

            socketio.emit('db_update', {
                'tagDetected':True,
                'uid': uid,
                'product_id': product_id,
            })

            return jsonify({'message':'logs saved'}),200

        except IntegrityError:
            db.session.rollback()
            return jsonify({
                'error': 'Foreign key constraint failed. '
                        f'Product ID "{product_id}" does not exist in product_information.'
            }), 400

        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500

        except Exception as e:
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    
    else:
        try:
            # 既存データを全削除
            StoredProducts.query.delete()
            db.session.commit()

            socketio.emit('db_update', {
                'tagDetected':False
            })

            return jsonify({'message':'logs saved'}),200
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500

        except Exception as e:
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/get_model/<product_id>')
def get_model(product_id):
    product = ProductInformation.query.filter_by(product_id=product_id).first()
    if product:
        return jsonify({
            'product_name': product.product_name,
            'model_url': product.model_url
        })
    else:
        return jsonify({'error': 'Product not found'}), 404


@app.route('/')
def index():
    products = StoredProducts.query.all()
    return render_template('index.html', products=products)


if __name__ == '__main__':
  socketio.run(app, host='0.0.0.0', port=5000, debug=False, ssl_context=('cert.pem', 'key.pem'))
