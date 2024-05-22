import asyncio
import nest_asyncio
import time
import pickle
import uuid
import sqlite3
import struct
import numpy as np
from functools import partial
nest_asyncio.apply()
from datetime import datetime

from loguru import logger
import bleak
from bleak import BleakClient
from bleak.exc import BleakError
import sys
sys.setrecursionlimit(10000)

name = str(uuid.uuid4())
conn = sqlite3.connect('sensors.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS bangle_gyro
             (name TEXT, position TEXT, receive_time TEXT, ax FLOAT, ay FLOAT, az FLOAT)''')
c.execute('''CREATE TABLE IF NOT EXISTS bangle_accel
             (name TEXT, position TEXT, receive_time TEXT, ax FLOAT, ay FLOAT, az FLOAT)''')
c.execute('''CREATE TABLE IF NOT EXISTS bangle_bme
             (name TEXT, position TEXT, receive_time TEXT, dx INTEGER, dy INTEGER, dz INTEGER)''')

with open("imu.csv", "w") as f:
    f.write("timestamp,acc_x,acc_y,acc_z,gyro_x,gyro_y,gyro_z\n")

with open("bme.csv", "w") as f:
    f.write("timestamp,temp,press,humid\n")


class DataCollector:

    def __init__(self):
        self.is_connected = False
        self.last_packet_time = None
        self.bangle_position1 = "RHR"
        self.bangle_position2 = "RHR"
        self.client1_connected = False
        self.client2_connected = False

    def imu_handler1(self, sender, data):
        receive_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        conn = sqlite3.connect('sensors.db')
        c = conn.cursor()

        accel_raw_x = np.frombuffer(data[:4], dtype=np.float32, count=1)[0]
        accel_raw_y = np.frombuffer(data[4:8], dtype=np.float32, count=1)[0]
        accel_raw_z = np.frombuffer(data[8:12], dtype=np.float32, count=1)[0]
        gyro_raw_x = np.frombuffer(data[12:16], dtype=np.float32, count=1)[0]
        gyro_raw_y = np.frombuffer(data[16:20], dtype=np.float32, count=1)[0]
        gyro_raw_z = np.frombuffer(data[20:24], dtype=np.float32, count=1)[0]

        with open("imu.csv", "a") as f:
            f.write(f"{str(receive_time)},{accel_raw_x},{accel_raw_y},{accel_raw_z},{gyro_raw_x},{gyro_raw_y},{gyro_raw_z}\n")


    def bme_handler1(self, sender, data):
        receive_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        mag_raw_x = np.frombuffer(data[:4], dtype=np.float32, count=1)[0]
        mag_raw_y = np.frombuffer(data[4:8], dtype=np.float32, count=1)[0]
        mag_raw_z = np.frombuffer(data[8:12], dtype=np.float32, count=1)[0]
        with open("bme.csv", "a") as f:
            f.write(f"{str(receive_time)},{mag_raw_x},{mag_raw_y},{mag_raw_z}\n")

    def button_handler(self, sender, data):
        receive_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        button = np.frombuffer(data[:1], dtype=bool, count=1)[0]
        print("button", button)


    async def connect(self, address):
        try:
            print("Connecting...")
            async with BleakClient(address) as self.client:
                x = await self.client.is_connected()
                logger.info("Connected: {0}".format(x))
                self.is_connected = True
        except BleakError:
            logger.info("Device not found. Retrying...")
            asyncio.sleep(1.0)

    async def connect_client1(self, address):
        self.client1 = BleakClient(address, disconnected_callback=self.client1_disconnect)
        await self.client1.connect()
        svcs = await self.client1.get_services()
        print("Services:", svcs)
        for service in svcs:
            print(service)
        for service in self.client1.services:
            print("[Service] {0}: {1} {2}".format(service.uuid, service.description,
                                                        [(e.uuid, e.properties) for e in service.characteristics]))


        await self.client1.start_notify("0000a000-0000-1000-8000-00805f9b34fb", self.imu_handler1)
        await self.client1.start_notify("0000b000-0000-1000-8000-00805f9b34fb", self.bme_handler1)
        await self.client1.start_notify("0000c000-0000-1000-8000-00805f9b34fb", self.button_handler)
        print("CONNECTED")
        self.client1_connected = True

    def client1_disconnect(self, client):
        self.client1_connected = False

    async def run(self, addresses, debug=False):
        # Create Connection Dictionary
        # Create UUIDs per Connection
        # Execute notify with partial functions pre filled with UUID
        while True:
            if not self.client1_connected:
                try:
                    await self.connect_client1(addresses[0])
                except:
                    pass
            await asyncio.sleep(1.0)

    async def disc(self):
        await self.client1.disconnect()


loop = asyncio.get_event_loop()
dc = DataCollector()




try:
    loop.run_until_complete(dc.run(["CD:D7:16:C8:74:5F"]))
except KeyboardInterrupt:
    loop.run_until_complete(dc.disc())
    conn.close()

scanner = bleak.BleakScanner()
devices = loop.run_until_complete(scanner.discover(return_adv=True))
print(devices)