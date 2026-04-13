import MFRC522
import time
import requests
import urllib3

running = True
block = 8 # read block
key = [0xFF]*6 # default key
FLASK_SERVER = "https://172.20.10.12:5000/api/log"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("start RFID tag reading.")
print("Press Ctrl-C to stop.\n")

rfid = MFRC522.MFRC522()

fail_count = 0           # 連続失敗回数
FAIL_THRESHOLD = 3       # 3回連続失敗で「不検出」扱い

try:
    while running:

        (status, _) = rfid.MFRC522_Request(rfid.PICC_REQIDL)

        # 検出を試みる
        if status == rfid.MI_OK: 
            (status, uid) = rfid.MFRC522_SelectTagSN()
            
            if status == rfid.MI_OK:
                status = rfid.MFRC522_Auth(rfid.PICC_AUTHENT1A, block, key, uid)
                
                if status == rfid.MI_OK:
                    _, data = rfid.MFRC522_Read(block)
                    
                    if data:   
                        # 検出成功
                        fail_count = 0

                        uid_str = ''.join(f"{i:02x}" for i in uid)
                        product_id = ''.join(chr(b) for b in data).rstrip('\x00')
                        payload = {'tagDetected':True, 'uid':uid_str, 'product_id':product_id}

                        response = requests.post(FLASK_SERVER, json=payload, verify=False)
                    
                        if response.status_code == 200:
                            print("DETECTED:", payload)
                        
                        rfid.MFRC522_StopCrypto1()
                        time.sleep(1)
                        continue
                    
                    rfid.MFRC522_StopCrypto1()
                    
                else:
                    rfid.MFRC522_StopCrypto1()
            
        # 検出失敗
        fail_count += 1

        # 失敗回数が閾値を越えた場合
        if fail_count >= FAIL_THRESHOLD:
            fail_count = 0
            payload = {'tagDetected':False}
            response = requests.post(FLASK_SERVER, json=payload, verify=False)
            
            if response.status_code == 200:
                print("LOST:", payload)
            
        time.sleep(1)

except KeyboardInterrupt:
    print("program finish.")
