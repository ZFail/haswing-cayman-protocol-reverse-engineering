import serial
import sys
import time

# ================= НАСТРОЙКИ =================
PORT = 'COM12'          # Имя порта: Windows -> 'COMx', Linux/macOS -> '/dev/ttyUSBx'
BAUDRATE = 9600      # Скорость передачи данных
PAUSE_TIMEOUT = 0.01    # Пауза без данных (сек), после которой вставляется \n
READ_TIMEOUT = 0.001    # Таймаут одного чтения (должен быть < PAUSE_TIMEOUT)
# =============================================

def main():
    try:
        ser = serial.Serial(PORT, BAUDRATE, timeout=READ_TIMEOUT)
        print(f"✅ Порт {ser.name} открыт. Скорость: {ser.baudrate} бод.")
        print("⏳ Ожидание данных... (нажмите Ctrl+C для остановки)\n")
    except serial.SerialException as e:
        print(f"❌ Ошибка открытия порта: {e}")
        sys.exit(1)

    last_receive_time = 0.0
    newline_pending = False  # Флаг: был ли активный поток данных

    try:
        while True:
            # Читаем до 1024 байт. Если данных нет, блокирует поток на READ_TIMEOUT
            data = ser.read(1024)
            
            if data:
                # Выводим бинарные данные в hex-формате (без пробелов, компактно)
                sys.stdout.write(data.hex())
                sys.stdout.flush()
                last_receive_time = time.time()
                newline_pending = True
            elif newline_pending and (time.time() - last_receive_time >= PAUSE_TIMEOUT):
                # Таймаут сработал и прошло достаточно времени без данных -> пауза
                print()  # Вставляем перевод строки
                newline_pending = False
                
    except KeyboardInterrupt:
        print("\n\n🛑 Программа остановлена пользователем.")
    finally:
        if ser.is_open:
            ser.close()
            print("🔌 Порт закрыт.")

if __name__ == '__main__':
    main()