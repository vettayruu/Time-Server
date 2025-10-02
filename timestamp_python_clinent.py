import asyncio
import websockets
import json
import time
import ssl
from datetime import datetime
import threading


class TimeSyncWSS:
    def __init__(self, server_url):
        # 将 http:// 转换为 wss://，并添加端口
        self.server_url = server_url.replace('http://', 'wss://').replace(':80', ':8443')
        if ':' not in self.server_url.split('//')[1]:
            self.server_url += ':8443'

        self.time_offset = 0
        self.is_synced = False
        self.websocket = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.running = True

        print(f"WSS服务器地址: {self.server_url}")

    async def connect_websocket(self):
        """连接到WSS服务器"""
        try:
            # 创建SSL上下文，忽略自签名证书验证
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            # 连接WebSocket
            self.websocket = await websockets.connect(
                self.server_url,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10
            )

            print("已连接到WSS时间服务器")
            self.reconnect_attempts = 0

            # 请求时间
            await self.websocket.send(json.dumps({"command": "getTime"}))

            return True

        except Exception as error:
            print(f"WSS连接失败: {error}")
            return False

    async def handle_messages(self):
        """处理服务器消息"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    if 'serverTime' in data:
                        now = int(time.time() * 1000)  # 毫秒时间戳
                        self.time_offset = data['serverTime'] - now
                        self.is_synced = True

                        print(f"安全时间同步完成, 偏移量: {self.time_offset}ms")
                        if data.get('secure'):
                            print("✓ 使用安全连接")

                    if data.get('type') == 'broadcast':
                        print(f"收到广播: 连接的客户端数量 {data.get('connectedClients', 0)}")

                    elif data.get('type') == 'shutdown':
                        print("服务器即将关闭")
                        break

                except json.JSONDecodeError as e:
                    print(f"解析服务器消息出错: {e}")

        except websockets.exceptions.ConnectionClosed:
            print("与WSS服务器断开连接")
            self.is_synced = False

        except Exception as e:
            print(f"处理消息时出错: {e}")

    async def start_connection(self):
        """启动连接和消息处理"""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                if await self.connect_websocket():
                    await self.handle_messages()

                if self.running:  # 如果不是主动停止，则尝试重连
                    self.reconnect_attempts += 1
                    print(f"尝试重新连接 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
                    await asyncio.sleep(5)

            except Exception as e:
                print(f"连接过程中出错: {e}")
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    await asyncio.sleep(5)

    def get_server_time(self):
        """获取同步后的服务器时间戳"""
        current_time = int(time.time() * 1000)
        return current_time + int(self.time_offset)

    async def sync_with_server(self):
        """手动同步时间"""
        if self.websocket and not self.websocket.closed:
            await self.websocket.send(json.dumps({"command": "getTime"}))

    def stop(self):
        """停止连接"""
        self.running = False
        if self.websocket:
            asyncio.create_task(self.websocket.close())


# 同步包装器，用于在普通函数中使用异步类
class TimeSyncWSSSync:
    def __init__(self, server_url):
        self.time_sync = TimeSyncWSS(server_url)
        self.loop = None
        self.thread = None
        self.start_async()

    def start_async(self):
        """在单独线程中启动异步事件循环"""

        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.time_sync.start_connection())

        self.thread = threading.Thread(target=run_loop, daemon=True)
        self.thread.start()

        # 等待连接建立
        max_wait = 10  # 最多等待10秒
        wait_time = 0
        while not self.time_sync.is_synced and wait_time < max_wait:
            time.sleep(0.1)
            wait_time += 0.1

    def get_server_time(self):
        return self.time_sync.get_server_time()

    def is_synced(self):
        return self.time_sync.is_synced

    def stop(self):
        self.time_sync.stop()


# 使用示例
async def main_async():
    """异步主函数"""
    time_sync = TimeSyncWSS('http://192.168.197.52/time')

    # 启动连接任务
    connection_task = asyncio.create_task(time_sync.start_connection())

    # 等待初始同步
    max_wait = 10
    wait_time = 0
    while not time_sync.is_synced and wait_time < max_wait:
        await asyncio.sleep(0.1)
        wait_time += 0.1

    if time_sync.is_synced:
        print('=== WSS 同步完成，开始持续输出时间戳 ===')

        try:
            # 输出时间戳
            for i in range(60):  # 运行60秒
                timestamp = time_sync.get_server_time()
                last_five = str(timestamp)[-5:]
                current_time = datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M:%S')

                print(f"[{current_time}] WSS Timestamp: {timestamp} | Last 5: {last_five}")
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n程序被中断")
        finally:
            time_sync.stop()
            connection_task.cancel()
    else:
        print('WSS时间同步失败')
        time_sync.stop()


def main_sync():
    """同步主函数（更简单的使用方式）"""
    time_sync = TimeSyncWSSSync('http://192.168.197.52/time')

    if time_sync.is_synced():
        print('=== WSS 同步完成，开始持续输出时间戳 ===')

        try:
            while True:
                timestamp = time_sync.get_server_time()
                last_five = str(timestamp)[-5:]
                current_time = datetime.fromtimestamp(timestamp / 1000).strftime('%H:%M:%S')

                print(f"[{current_time}] WSS Timestamp: {timestamp} | Last 5: {last_five}")
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n程序被中断")
        finally:
            time_sync.stop()
    else:
        print('WSS时间同步失败')


if __name__ == "__main__":
    # 安装依赖提示
    try:
        import websockets
    except ImportError:
        print("请先安装websockets库:")
        print("pip install websockets")
        exit(1)

    # 选择运行方式
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'async':
        print("使用异步方式运行...")
        asyncio.run(main_async())
    else:
        print("使用同步方式运行...")
        main_sync()