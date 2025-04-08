from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import os, shutil
from flask import send_from_directory
from models import db, File
from datetime import datetime, timedelta
import os
from threading import Timer
from flask import flash

# 添加密钥配置
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key')  # 建议使用环境变量

# 修改数据库配置
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///files.db')

# 修改运行配置
if __name__ == '__main__':
    try:
        app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=False)
    except (KeyboardInterrupt, SystemExit):
        print("应用关闭")
# 使用绝对路径
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/<path:folder_path>')
@app.route('/')
def index(folder_path=''):
    try:
        current_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_path)
        if not os.path.exists(current_path):
            return redirect(url_for('index'))
            
        items = []
        # 添加返回上级目录的选项
        if folder_path:
            parent_path = os.path.dirname(folder_path)
            items.append({
                'name': '..',
                'is_dir': True,
                'path': parent_path
            })
            
        for name in os.listdir(current_path):
            path = os.path.join(current_path, name)
            rel_path = os.path.join(folder_path, name) if folder_path else name
            
            # 获取文件或文件夹的剩余时间
            remaining_time = None
            file_info = None  # 初始化 file_info 变量
            
            if os.path.isdir(path):
                # 获取文件夹内所有文件的最短过期时间
                files_in_folder = File.query.filter(
                    File.path.like(f"{rel_path}%"),
                    File.expire_time.isnot(None)
                ).all()
                if files_in_folder:
                    min_expire_time = min(f.expire_time for f in files_in_folder)
                    remaining = min_expire_time - datetime.utcnow()
                    if remaining.total_seconds() > 0:
                        days = remaining.days
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        
                        if days > 0:
                            remaining_time = f"{days}天 {hours}小时"
                        elif hours > 0:
                            remaining_time = f"{hours}小时 {minutes}分钟"
                        else:
                            remaining_time = f"{minutes}分钟"
            else:
                file_info = File.query.filter_by(path=rel_path).first()
                if file_info and file_info.expire_time:
                    remaining = file_info.expire_time - datetime.utcnow()
                    if remaining.total_seconds() > 0:
                        days = remaining.days
                        hours = remaining.seconds // 3600
                        minutes = (remaining.seconds % 3600) // 60
                        
                        if days > 0:
                            remaining_time = f"{days}天 {hours}小时"
                        elif hours > 0:
                            remaining_time = f"{hours}小时 {minutes}分钟"
                        else:
                            remaining_time = f"{minutes}分钟"

            items.append({
                'name': name,
                'is_dir': os.path.isdir(path),
                'path': rel_path,
                'id': file_info.id if file_info else None,
                'remaining_time': remaining_time
            })
        return render_template('index.html', items=items, current_path=folder_path)
    except Exception as e:
        return render_template('index.html', items=[], error=f"访问文件失败: {str(e)}")

@app.route('/create_folder', methods=['POST'])
def create_folder():
    folder_name = request.form.get('folder_name')
    current_path = request.args.get('current_path', '')
    
    if not folder_name:
        return redirect(url_for('index', folder_path=current_path))
    
    try:
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], current_path, folder_name)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"成功创建文件夹: {folder_path}")
            return redirect(url_for('index', folder_path=current_path))
        else:
            # 如果文件夹已存在，返回到当前页面并保持现有内容
            items = []  # 获取当前目录的内容
            current_full_path = os.path.join(app.config['UPLOAD_FOLDER'], current_path)
            
            if current_path:
                parent_path = os.path.dirname(current_path)
                items.append({
                    'name': '..',
                    'is_dir': True,
                    'path': parent_path
                })
            
            for name in os.listdir(current_full_path):
                items.append({
                    'name': name,
                    'is_dir': os.path.isdir(os.path.join(current_full_path, name)),
                    'path': os.path.join(current_path, name) if current_path else name
                })
            
            return render_template('index.html', 
                                 items=items, 
                                 current_path=current_path,
                                 error="文件夹已存在")
            
    except Exception as e:
        return render_template('index.html', 
                             items=[], 
                             current_path=current_path,
                             error=f"创建失败: {str(e)}")

@app.route('/delete/<path:item_name>')
def delete_item(item_name):
    try:
        item_path = os.path.join(app.config['UPLOAD_FOLDER'], item_name)
        if os.path.exists(item_path):
            if os.path.isdir(item_path):
                # 删除文件夹内所有文件的数据库记录
                files_in_folder = File.query.filter(File.path.like(f"{item_name}%")).all()
                for file in files_in_folder:
                    db.session.delete(file)
                shutil.rmtree(item_path)  # 删除文件夹及其内容
            else:
                # 删除单个文件的数据库记录
                file_record = File.query.filter_by(path=item_name).first()
                if file_record:
                    db.session.delete(file_record)
                os.remove(item_path)  # 删除文件
            
            db.session.commit()
            return redirect(url_for('index'))
            
        return render_template('index.html', items=[], error="文件或文件夹不存在")
    except Exception as e:
        return render_template('index.html', items=[], error=f"删除失败: {str(e)}")

@app.route('/view/<path:filename>')
def view_pdf(filename):
    try:
        # 添加路径验证
        if '..' in filename or filename.startswith('/'):
            return "非法访问", 403
            
        file_path = os.path.dirname(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_name = os.path.basename(filename)
        
        # 验证文件是否在允许的目录下
        if not os.path.commonprefix([file_path, app.config['UPLOAD_FOLDER']]) == app.config['UPLOAD_FOLDER']:
            return "非法访问", 403
            
        return send_from_directory(file_path, file_name)
    except Exception as e:
        return str(e), 404

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///files.db'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return render_template('index.html', items=[], error="没有选择文件")
        
        file = request.files['file']
        expire_time = request.form.get('expire_time', None)
        
        if file.filename == '':
            return render_template('index.html', items=[], error="没有选择文件")
            
        if file and file.filename.endswith('.pdf'):
            current_path = request.args.get('current_path', '')
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], current_path)
            os.makedirs(save_path, exist_ok=True)
            file.save(os.path.join(save_path, file.filename))
            
            # 创建文件记录
            new_file = File(
                name=file.filename,
                path=os.path.join(current_path, file.filename)
            )
            
            # 如果设置了过期时间
            if expire_time:
                hours = int(expire_time)
                new_file.expire_time = datetime.utcnow() + timedelta(hours=hours)
            
            db.session.add(new_file)
            db.session.commit()
            
            return redirect(url_for('index', folder_path=current_path))
        else:
            return render_template('index.html', items=[], error="只能上传PDF文件")
            
    except Exception as e:
        return render_template('index.html', items=[], error=f"上传失败: {str(e)}")

@app.route('/set_expire_time/<int:file_id>', methods=['POST'])
def set_expire_time(file_id):
    minutes = request.json.get('minutes')
    file = File.query.get_or_404(file_id)
    file.expire_time = datetime.utcnow() + timedelta(minutes=minutes)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/set_folder_expire_time', methods=['POST'])
def set_folder_expire_time():
    data = request.json
    folder_path = data.get('path')
    minutes = data.get('minutes')
    
    try:
        expire_time = datetime.utcnow() + timedelta(minutes=minutes)
        
        # 创建或更新文件夹记录
        folder_record = File.query.filter_by(path=folder_path).first()
        if not folder_record:
            folder_record = File(
                name=os.path.basename(folder_path),
                path=folder_path,
                expire_time=expire_time
            )
            db.session.add(folder_record)
        else:
            folder_record.expire_time = expire_time

        # 设置文件夹内所有文件的过期时间
        files_in_folder = File.query.filter(
            File.path.like(f"{folder_path}/%")
        ).all()
        
        for file in files_in_folder:
            file.expire_time = expire_time
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        print(f"设置文件夹过期时间失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

# 添加定时任务来检查和删除过期文件
# 修改定时任务相关代码
# 删除原有的 Timer 相关代码，改用以下实现

import threading
import time

def check_expired_files_thread():
    while True:
        try:
            print("检查过期文件...")
            with app.app_context():
                expired_files = File.query.filter(
                    File.expire_time.isnot(None),
                    File.expire_time <= datetime.utcnow()
                ).all()
                
                for file in expired_files:
                    try:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.path)
                        if os.path.exists(file_path):
                            if os.path.isdir(file_path):
                                # 删除文件夹及其内容
                                shutil.rmtree(file_path)
                                print(f"删除过期文件夹: {file.path}")
                            else:
                                # 删除文件
                                os.remove(file_path)
                                print(f"删除过期文件: {file.path}")
                            
                            # 检查父文件夹是否为空，如果为空则删除
                            parent_dir = os.path.dirname(file_path)
                            if parent_dir != app.config['UPLOAD_FOLDER'] and not os.listdir(parent_dir):
                                shutil.rmtree(parent_dir)
                                print(f"删除空文件夹: {os.path.relpath(parent_dir, app.config['UPLOAD_FOLDER'])}")
                                
                        db.session.delete(file)
                    except Exception as e:
                        print(f"删除失败: {str(e)}")
                
                db.session.commit()
        except Exception as e:
            print(f"检查过期文件时出错: {str(e)}")
        
        time.sleep(30)  # 每30秒检查一次

if __name__ == '__main__':
    # 启动检查线程
    check_thread = threading.Thread(target=check_expired_files_thread, daemon=True)
    check_thread.start()
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=True)  # 修改端口为5000
    except (KeyboardInterrupt, SystemExit):
        print("应用关闭")