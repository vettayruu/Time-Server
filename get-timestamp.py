import requests
import time
import threading
from datetime import datetime

class TimeSync:
    def __init__(self, server_url):
        self.server_url = server_url
        self.time_offset = 0
        self.sync_with_server()
        
        # 每60秒同步一次
        self.sync_timer = threading.Timer(60.0, self._sync_periodically)
        self.sync_timer.daemon = True
        self.sync_timer.start()
    
    def sync_with_server(self):
        """与服务器同步时间"""
        try:
            start_time = time.time() * 1000  # 毫秒
            response = requests.get(self.server_url, timeout=5)
            end_time = time.time() * 1000
            
            if response.status_code == 200:
                data = response.json()
                server_time = data['serverTime']
                network_delay = (end_time - start_time) / 2
                self.time_offset = server_time - (end_time - network_delay)
                
                print(f"TimeSync: offset(ms)= {self.time_offset:.2f}")
                return True
            else:
                print(f"TimeSync failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"TimeSync failed: {e}")
            return False
    
    def _sync_periodically(self):
        """定期同步"""
        self.sync_with_server()
        self.sync_timer = threading.Timer(60.0, self._sync_periodically)
        self.sync_timer.daemon = True
        self.sync_timer.start()
    
    def get_server_time(self):
        """获取同步后的服务器时间戳（毫秒）"""
        current_time = time.time() * 1000
        return int(current_time + self.time_offset)
    
    def get_server_datetime(self):
        """获取同步后的服务器时间（datetime对象）"""
        timestamp = self.get_server_time() / 1000
        return datetime.fromtimestamp(timestamp)

# 使用示例
if __name__ == "__main__":
    # 创建时间同步实例
    time_sync = TimeSync("http://192.168.197.52/time")
    
    # 等待初始同步完成
    time.sleep(1)
    
    # 获取同步后的时间戳
    print(f"Current server timestamp: {time_sync.get_server_time()}")
    print(f"Current server time: {time_sync.get_server_datetime()}")
    
    # 持续显示时间（可选）
    try:
        while True:
            print(f"\rServer time: {time_sync.get_server_datetime().strftime('%Y-%m-%d %H:%M:%S')}", end='')
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nProgram stopped.")