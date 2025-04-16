import pandas as pd
import schedule
import time
from datetime import datetime, timedelta
import threading
import sys

class AIMentor:
    def __init__(self):
        self.tasks_df = None
        self.schedule_df = None
        self.progress_df = None
        self.load_data()
        self.command_thread = None
        self.is_running = True

    def load_data(self):
        """タスクと予定をCSVから読み込む"""
        self.tasks_df = pd.read_csv('tasks.csv')
        self.schedule_df = pd.read_csv('schedule.csv', sep='\t', header=None, 
                                     names=['id', 'title', 'start_time', 'end_time'])
        self.progress_df = pd.read_csv('task_progress.csv')
        
        # 日付をdatetime型に変換
        self.schedule_df['start_time'] = pd.to_datetime(self.schedule_df['start_time'])
        self.schedule_df['end_time'] = pd.to_datetime(self.schedule_df['end_time'])

    def start(self):
        """AIメンターを開始"""
        print("\nおはよう！今日も頑張るにゃ！\n")
        
        # コマンド入力用のスレッドを開始
        self.command_thread = threading.Thread(target=self.command_loop)
        self.command_thread.daemon = True
        self.command_thread.start()
        
        # スケジュール設定
        schedule.every(5).minutes.do(self.check_upcoming_meetings)
        schedule.every(30).minutes.do(self.check_task_progress)
        
        # メインループ
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)

    def command_loop(self):
        """コマンド入力ループ"""
        while self.is_running:
            print("\nコマンドを入力してください:")
            print("1: 今日のタスクを表示")
            print("2: 今日の予定を表示")
            print("3: タスクの進捗を更新")
            print("4: タスクを追加")
            print("q: 終了")
            
            cmd = input().strip().lower()
            
            if cmd == '1':
                self.show_today_tasks()
            elif cmd == '2':
                self.show_today_schedule()
            elif cmd == '3':
                self.update_task_progress()
            elif cmd == '4':
                self.add_task()
            elif cmd == 'q':
                self.is_running = False
                break

    def show_today_tasks(self):
        """今日のタスクを表示"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_tasks = self.progress_df[self.progress_df['date'] == today]
        
        if today_tasks.empty:
            print("\nタスクがないよ、何をやる？")
            return
            
        print("\n今日のタスクだにゃ！")
        for idx, task in today_tasks.iterrows():
            print(f"・{task['task']} ({task['status']}, 進捗: {task['progress']}%)")

    def show_today_schedule(self):
        """今日の予定を表示"""
        today = datetime.now().date()
        today_schedule = self.schedule_df[
            (self.schedule_df['start_time'].dt.date == today) |
            (self.schedule_df['end_time'].dt.date == today)
        ]
        
        if not today_schedule.empty:
            print("\n今日の予定だにゃ！")
            for idx, event in today_schedule.iterrows():
                start_time = event['start_time'].strftime('%H:%M')
                end_time = event['end_time'].strftime('%H:%M')
                print(f"・{start_time}-{end_time} {event['title']}")
        else:
            print("\n今日の予定はありませんにゃ！")

    def check_upcoming_meetings(self):
        """30分後に会議がある場合、通知する"""
        now = datetime.now()
        today = now.date()
        
        today_schedule = self.schedule_df[
            ((self.schedule_df['start_time'].dt.date == today) |
             (self.schedule_df['end_time'].dt.date == today)) &
            (self.schedule_df['title'].str.contains('MTG|ミーティング|meeting', case=False, na=False))
        ]
        
        for idx, event in today_schedule.iterrows():
            meeting_time = event['start_time']
            
            if timedelta(minutes=25) <= meeting_time - now <= timedelta(minutes=35):
                print(f"\n[リマインド] {meeting_time.strftime('%H:%M')}から{event['title']}の準備は大丈夫にゃ？")

    def check_task_progress(self):
        """タスクの進捗を確認"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_tasks = self.progress_df[self.progress_df['date'] == today]
        
        if not today_tasks.empty:
            print("\nタスクの進捗確認だにゃ！")
            for idx, task in today_tasks.iterrows():
                if task['status'] != '完了':
                    print(f"・{task['task']} ({task['status']}, 進捗: {task['progress']}%)")

    def update_task_progress(self):
        """タスクの進捗を更新"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_tasks = self.progress_df[self.progress_df['date'] == today]
        
        print("\n更新するタスクを選んでください：")
        for idx, task in today_tasks.iterrows():
            print(f"{task['task_id']}: {task['task']} ({task['status']}, 進捗: {task['progress']}%)")
        
        try:
            task_id = int(input("タスクIDを入力: "))
            if task_id not in today_tasks['task_id'].values:
                print("無効なタスクIDですにゃ！")
                return
            
            print("\nステータスを選択してください：")
            print("1: 未着手")
            print("2: 進行中")
            print("3: 完了")
            status_choice = int(input("選択: "))
            
            status_map = {1: '未着手', 2: '進行中', 3: '完了'}
            new_status = status_map.get(status_choice)
            
            if not new_status:
                print("無効な選択ですにゃ！")
                return
            
            progress = int(input("進捗率を入力 (0-100): "))
            if not 0 <= progress <= 100:
                print("進捗率は0から100の間で入力してくださいにゃ！")
                return
            
            # 進捗を更新
            self.progress_df.loc[self.progress_df['task_id'] == task_id, 'status'] = new_status
            self.progress_df.loc[self.progress_df['task_id'] == task_id, 'progress'] = progress
            self.progress_df.to_csv('task_progress.csv', index=False)
            
            print(f"\nタスクの進捗を更新しましたにゃ！")
            print(f"{self.progress_df[self.progress_df['task_id'] == task_id].iloc[0]['task']}: {new_status}, 進捗: {progress}%")
            
        except ValueError:
            print("無効な入力ですにゃ！")

    def add_task(self):
        """新しいタスクを追加"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        print("\n新しいタスクを追加するにゃ！")
        task_name = input("タスクの内容を入力してにゃ: ")
        
        if not task_name:
            print("タスクの内容を入力してにゃ！")
            return
        
        # 新しいタスクIDを生成
        new_task_id = len(self.progress_df) + 1
        
        # 新しいタスクをDataFrameに追加
        new_task = pd.DataFrame({
            'task_id': [new_task_id],
            'date': [today],
            'task': [task_name],
            'status': ['未着手'],
            'progress': [0]
        })
        
        self.progress_df = pd.concat([self.progress_df, new_task], ignore_index=True)
        self.progress_df.to_csv('task_progress.csv', index=False)
        
        print(f"\n新しいタスクを追加したにゃ！")
        print(f"・{task_name} (未着手, 進捗: 0%)")

def main():
    mentor = AIMentor()
    try:
        mentor.start()
    except KeyboardInterrupt:
        print("\nAIメンターを終了しますにゃ！")
        mentor.is_running = False
        sys.exit(0)

if __name__ == "__main__":
    main() 