from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'chikitam_secret_key'

# データファイルのパス
TASKS_FILE = 'task_progress.csv'
SCHEDULE_FILE = 'schedule.csv'

def load_tasks():
    """タスクを読み込む"""
    if os.path.exists(TASKS_FILE):
        return pd.read_csv(TASKS_FILE).to_dict('records')
    return []

def load_schedule():
    """予定を読み込む"""
    if os.path.exists(SCHEDULE_FILE):
        return pd.read_csv(SCHEDULE_FILE).to_dict('records')
    return []

def save_tasks(tasks):
    """タスクを保存"""
    df = pd.DataFrame(tasks)
    df.to_csv(TASKS_FILE, index=False)

def save_schedule(schedule):
    """予定を保存"""
    df = pd.DataFrame(schedule)
    df.to_csv(SCHEDULE_FILE, index=False)

@app.route('/')
def index():
    """ホームページ"""
    today = datetime.now().strftime('%Y-%m-%d')
    tasks = load_tasks()
    schedule = load_schedule()
    
    today_tasks = [task for task in tasks if task['date'] == today]
    today_schedule = [event for event in schedule if
        (event['start_time'].startswith(today) or event['end_time'].startswith(today))]
    
    return render_template('index.html', 
                         tasks=today_tasks,
                         schedule=today_schedule)

@app.route('/add_task', methods=['POST'])
def add_task():
    """タスクを追加"""
    task_name = request.form.get('task_name')
    if not task_name:
        flash('タスクの内容を入力してにゃ！', 'error')
        return redirect(url_for('index'))
    
    tasks = load_tasks()
    today = datetime.now().strftime('%Y-%m-%d')
    
    new_task = {
        'task_id': len(tasks) + 1,
        'date': today,
        'task': task_name,
        'status': '未着手',
        'progress': 0
    }
    
    tasks.append(new_task)
    save_tasks(tasks)
    
    flash('新しいタスクを追加したにゃ！', 'success')
    return redirect(url_for('index'))

@app.route('/update_task/<int:task_id>', methods=['POST'])
def update_task(task_id):
    """タスクの進捗を更新"""
    tasks = load_tasks()
    for task in tasks:
        if task['task_id'] == task_id:
            # チェックボックスの状態に基づいてステータスを更新
            if 'completed' in request.form:
                task['status'] = '完了'
                task['progress'] = 100
            else:
                task['status'] = request.form.get('status', task['status'])
                # 進捗率はステータスに基づいて自動更新
                if task['status'] == '未着手':
                    task['progress'] = 0
                elif task['status'] == '進行中':
                    task['progress'] = 50
                elif task['status'] == '完了':
                    task['progress'] = 100
            break
    save_tasks(tasks)
    
    flash('タスクの進捗を更新しましたにゃ！', 'success')
    return redirect(url_for('index'))

@app.route('/add_schedule', methods=['POST'])
def add_schedule():
    """予定を追加"""
    title = request.form.get('title')
    start_time = request.form.get('start_time')
    end_time = request.form.get('end_time')
    
    if not all([title, start_time, end_time]):
        flash('予定の内容を全て入力してにゃ！', 'error')
        return redirect(url_for('index'))
    
    schedule = load_schedule()
    new_event = {
        'title': title,
        'start_time': start_time,
        'end_time': end_time
    }
    
    schedule.append(new_event)
    save_schedule(schedule)
    
    flash('新しい予定を追加したにゃ！', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 