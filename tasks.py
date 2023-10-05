from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import webbrowser
import os
from sqlalchemy import inspect

app = Flask(__name__)

# Alterando o caminho do banco de dados para a pasta de documentos do usuário
db_path = os.path.join(os.path.expanduser('~'), 'Documents', 'tarefas.db')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SECRET_KEY'] = 'alguma_chave_secreta'

db = SQLAlchemy(app)

class Tarefa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descricao = db.Column(db.String(80))
    concluido = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)

def table_exists(name):
    inspector = inspect(db.engine)
    return name in inspector.get_table_names()

def ensure_database_exists():
    with app.app_context():
        if not table_exists("tarefa"):
            db.create_all()
            print("Database tables created!")
        else:
            print("Database tables already exist!")

ensure_database_exists()

@app.route('/')
def index():
    tarefas = Tarefa.query.order_by(Tarefa.order.asc()).all()
    return render_template('index.html', tarefas=tarefas)

@app.route('/adicionar', methods=['POST'])
def adicionar():
    descricao = request.form.get('descricao')
    if descricao:
        last_task = Tarefa.query.order_by(Tarefa.order.desc()).first()
        next_order = (last_task.order + 1) if last_task else 0
        new_task = Tarefa(descricao=descricao, order=next_order)
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/start-task', methods=['POST'])
def start_task():
    data = request.get_json(force=True)
    task_id = data.get('taskId')
    start_time = data.get('startTime')
    if not task_id or not start_time:
        return {"error": "Missing taskId or startTime"}, 400
    task = Tarefa.query.get(int(task_id))
    if not task:
        return {"error": "Task not found"}, 404
    try:
        time_obj = datetime.strptime(start_time, "%H:%M")
        task.start_time = time_obj
    except ValueError:
        return {"error": "Invalid time format"}, 400
    db.session.commit()
    return {"message": "Start time updated successfully"}, 200

@app.route('/toggle/<int:id>', methods=['GET'])
def toggle(id):
    tarefa = Tarefa.query.get(id)
    tarefa.concluido = not tarefa.concluido
    if tarefa.concluido and tarefa.start_time:
        tarefa.end_time = datetime.now()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/reiniciar-tarefas', methods=['POST'])
def reiniciar_tarefas():
    try:
        Tarefa.query.update({Tarefa.start_time: None, Tarefa.end_time: None, Tarefa.concluido: False})
        db.session.commit()
    except Exception as e:
        return {"error": str(e)}, 500
    return {"message": "Tarefas reiniciadas com sucesso"}, 200

@app.route('/apagar/<int:id>', methods=['GET'])
def apagar(id):
    tarefa = Tarefa.query.get(id)
    db.session.delete(tarefa)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/update-order', methods=['POST'])
def update_order():
    order_data = request.json.get('order')
    if not order_data:
        return {"error": "No order data provided"}, 400
    for index, task_id in enumerate(order_data):
        task = Tarefa.query.get(int(task_id))
        if task:
            task.order = index
    db.session.commit()
    return {"message": "Order updated successfully"}, 200

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True)
