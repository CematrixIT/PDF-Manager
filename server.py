from waitress import serve
from app import app, check_expired_files_thread
import threading
import os

if __name__ == '__main__':
    # 添加环境变量配置
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    # 启动检查线程
    check_thread = threading.Thread(target=check_expired_files_thread, daemon=True)
    check_thread.start()
    
    print(f"服务器已启动，访问 http://{host}:{port}")
    serve(app, host=host, port=port, threads=4)  # 添加线程数配置