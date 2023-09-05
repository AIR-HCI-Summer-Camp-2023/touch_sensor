import json
import socket
import sys
import serial
import numpy as np
import time

class ArrayReader:
    def __init__(self):
        pass

    def get_serial_data_pull(self, serial, m, n, max_delay):
        # serial: 串口对象
        # m, n: 数据格式
        # max_delay: 最大延迟 (秒)

        m_data = np.zeros((n, m), dtype=np.uint16)  # 初始化数据
        packet_bytes = m * n * 2

        retry = 0
        while serial.in_waiting < packet_bytes:  # 等待数据读取
            retry += 1
            time.sleep(0.001)
            if retry > max_delay:
                break

        bytes_received = serial.in_waiting  # 获取缓冲区中的字节数

        if bytes_received >= packet_bytes:
            data_bytes = serial.read(packet_bytes)
            m_data = np.frombuffer(data_bytes, dtype=np.uint16).reshape((n, m))
            remaining_bytes = bytes_received - packet_bytes

            if remaining_bytes > 0:
                dummy_data = serial.read(remaining_bytes)
                print('dummy read.')

        return m_data


def main():
    # 打开串口
    s = serial.Serial(port="COM6", baudrate=115200, bytesize=8, stopbits=1, parity='N', timeout=0.1)
    s.reset_input_buffer()
    s.reset_output_buffer()
    # 设置缓冲区大小
    input_buffer_size = 65536
    output_buffer_size = 256
    s.set_buffer_size(rx_size=input_buffer_size, tx_size=output_buffer_size)
    # print(f"Serial Port Status: {s.name}, {s.is_open}, InputBufferSize: {input_buffer_size}, OutputBufferSize: {output_buffer_size}, Timeout: {s.timeout}")

    localIP = "127.73.73.1"  # 73.73.73.0表示监听本机拥有的所有IP
    localPort = 4000  # 开始监听本地3000端口
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.bind((localIP, localPort))

    try:
        while True:
            cmd = bytes([65, 13, 10])  # cmd format,65 13 10对应的ASCII字符分别是A \r \n
            s.write(cmd)  # 发送命令
            A = get_serial_data_pull(s, 64, 64, 1000)  # 读取数组数据

            try:
                data, address = UDPClientSocket.recvfrom(4096)  # 缓冲区上限定义
            except socket.timeout:
                continue
            else:
                UDPClientSocket.sendto(bytes(json.dumps({'n': 1, 'd': A.tolist()}), encoding="utf8"), address)  # UDP发送

    except KeyboardInterrupt:
        pass

    # 关闭串口
    s.close()
