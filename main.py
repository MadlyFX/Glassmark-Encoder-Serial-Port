import socketio
import time
import serial
import json
import threading
import serial.tools.list_ports
import _thread

sio = socketio.Client()
camera = '0'
number = '0'
pingTime = 0

sending = False
newPort = 0

ser = serial.Serial()

connectiondelay = 2;

portSetOld = set()


def my_background_task():
    global ser
    while True:
        reading = ser.readline()
        if reading:
            y = json.loads(reading)
            print(y["pos"])
            sio.emit('encoderReport', y["pos"])


def wait_for_encoder_boot():
    global ser
    global camera
    global number
    isJson = False
    if ser.is_open:
        while True:
            x = ser.readline()
            print(ser.readline())
            if x == b"######\r\n":
                print("Encoder Connected")
                ser.write(b"$g") #Write the status get command until it returns something valid
                print("Sent interrupt")
            try:
                json.loads(x)
            except:
                ser.write(b"$g")  # Write the status get command until it returns something valid
                print("Sent interrupt")
                pass
            else:
                print(x)
                y = json.loads(x)
                camera = y["cam"][1]
                number = y["num"][1]
                sio.connect('http://localhost:3000')
                break


def poll_ports():
    global portSetOld
    global newPort
    global ser
    global connectiondelay
    connected = False

    t = threading.Timer(1, poll_ports)

    portsSet = set(serial.tools.list_ports.comports())

    if portsSet.difference(portSetOld):
        newPort = portsSet.difference(portSetOld)  # Save the new port
        print(list(newPort)[0].name)

        ser.port = list(newPort)[0].name
        ser.baudrate = 115200
        ser.timeout = 5

        result = False
        while result is False:
            try:
                ser.open()
                result = True
            except:
                print("Waiting for OS to release COM port...")
                pass

        t.cancel()  # done polling

        connected = True
        wait_for_encoder_boot()

    if not connected:
        portSetOld = portsSet
        print("Waiting. Connect encoder...")
        t.start()


def fill_ports(): #fill both sets so the comparison doesn't fail on the first try
    ports = set(serial.tools.list_ports.comports())
    global portSetOld
    portSetOld = ports


def main():
    fill_ports()
    poll_ports()


main()

@sio.event
def connect():
    global ser
    print('connection established')
    sio.emit('connectReport', {'cam': camera, 'num': number, 'type': 'E'})
    time.sleep(0.5)
    ser.write(b"$s") #Start streaming mode, automatically gets values from encoder
    sio.start_background_task(my_background_task)


@sio.event
def disconnect():
    print('disconnected from server')


@sio.on('change_assignment')
def on_message(data):
    global camera
    global number
    sio.emit('connectReport', {'cam': data["assnLetter"].strip('"'), 'num': data["assnNumber"].strip('"'), 'type': 'E'})
    camera = data["assnLetter"].strip('"')
    number = data["assnNumber"].strip('"')

    numberFormatted = "$n" + number
    ser.write(numberFormatted.encode())

    time.sleep(0.5) #wait a bit for the encoder to write

    cameraFormatted = "$c" + camera
    ser.write(cameraFormatted.encode())


@sio.on('blackout')
def on_message(data):
    cameraFormatted = "$b" + str(data)
    print("Blackout")
    ser.write(cameraFormatted.encode())

@sio.on('flashLED')
def on_message(data):
    flashLEDformatted = "$f" + str(data)
    ser.write(flashLEDformatted.encode())
