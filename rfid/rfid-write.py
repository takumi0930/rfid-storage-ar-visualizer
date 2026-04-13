import MFRC522
import time

running = True
block = 8 # read block
key = [0xFF]*6 # default key

rfid = MFRC522.MFRC522()

print("Please place your RFID card on the reader...")
print("Press Ctrl-C to stop.")

try:
    while running:
        (status, _) = rfid.MFRC522_Request(rfid.PICC_REQIDL)
        
        if status == rfid.MI_OK: 
            (status, uid) = rfid.MFRC522_SelectTagSN()
            
            if status == rfid.MI_OK:
                uid_str = ''.join(f"{i:02x}" for i in uid)
                
                write_text = input(f"Please enter product_id to write to {uid_str} (up to 16 characters):\n")[:16]
                write_data= [0x00]*16
                for i, c in enumerate(write_text.encode()):
                    write_data[i] = c
                
                status = rfid.MFRC522_Auth(rfid.PICC_AUTHENT1A, block, key, uid)
                
                if status == rfid.MI_OK:
                    
                    # write text to rfid
                    rfid.MFRC522_Write(block, write_data)
                    
                    # read written text
                    _, read_data = rfid.MFRC522_Read(block)
                        
                    if read_data:
                        read_text = ''.join(chr(b) for b in read_data).rstrip('\x00')
                        print(f"uid:{uid_str}\nproduct_id:{read_text}\n")
                    else:
                        print(f"uid:{uid_str}\nproduct_id:(null)\n")
                    
                    rfid.MFRC522_StopCrypto1()
                    
                    time.sleep(1.8)
                    
                else:
                    print("Auth failed")
                    rfid.MFRC522_StopCrypto1()
        
        time.sleep(0.2)

except KeyboardInterrupt:
    print("program finish")
