import logging
import struct

import roaster_helper_libs


# Bluezero modules
from bluezero import async_tools
from bluezero import peripheral
from queue import Queue



class BLEPeripheral( ):

    IKAWA_SERVICE = 'C92A6046-6C8D-4116-9D1D-D20A8F6A245F'
    UUID_RECEIVE = "948C5059-7F00-46D9-AC55-BF090AE066E3"
    UUID_SEND = "851A4582-19C1-4E6C-AB37-E7A03766BA16"  ### Here we receive the commands from APP
    UUID_CLIENT_CONFIGURATION = "00002902-0000-1000-8000-00805f9b34fb"


    def publish(self):
        self.RoasterPeripheral.publish()


    def crc16(self, bArr, i):
        for i2 in bArr:
            i3 = (i2 & 255) ^ (i & 255)
            i4 = i3 ^ ((i3 << 4) & 255)
            i = ((((i >> 8) & 255) | ((i4 << 8) & 65535)) ^ (i4 >> 4)) ^ ((i4 << 3) & 65535)

        return int(i & 65535).to_bytes(2, byteorder='big')


    def receive_test(self, value):
        print("receive_test")
        print(value)

    def notify_callback(self,notifying, characteristic):

        if self.notify_setup == False:
            print("notify callback")
            if notifying:
                print("Notifying... TO BE IMPLEMENTED well")
                self.notify_setup = True
                async_tools.add_timer_ms(50, self.update_value, characteristic)
        else:
            print ("Already notifying")
            #async_tools.add_timer_seconds(1, self.update_value, characteristic)

    def receive_ikawaapp_command(self,value, characteristic):
        """
        Called when a central writes to our write characteristic.

        :param value: data sent by the central
        :param options:

        Data Frame Format (BYTES)
        [0] 0x7E FRAME_BYTE

        [1] Missatge N Bytes (Si originalment tenia un 125 o 126, posa un 125 i el seguent byte: 125 -> 93, 126 -> 94)

        [N-2]CRC 1byte
        [N-1]CRC 1byte

        [N]0x7E FRAME_BYTE

        """


        if (len(self.long_message) == 0):
            print("Message Received from APP %d bytes" % len(value))
        else:
            print("CONTINUE Message Received from APP %d bytes" % len(value))

        #for i in range(0,3):
            #print (self.RoasterPeripheral.characteristics[i].is_notifying)
            #print (self.RoasterPeripheral.characteristics[i])

        # Print received message
        for p in value:
            print(hex(p), end=' ')
        print()

        if value[0] != 126:  ## Check frame byte
            if (len(self.long_message) == 0):
                print("Error: Invalid Frame Byte")
                return

        if value[-1] != 126:  ## Check frame byte
            # print ("Error: Missing ending Frame Byte. TODO: Implement longer messages")
            self.long_message = self.long_message + value
            return

        if len(self.long_message) > 0:

            value = self.long_message + value

            print("End of long message, len %d" % (len(self.long_message)))
            for p in value:
                print(hex(p), end=' ')
            print()

        self.long_message = bytearray()  # Clear long message
        message_orig = value[1:-1]  ## Remove frame byte
        message = bytearray()

        ## Un-escape the message
        try:
            i = 0
            while i < len(message_orig):
                if message_orig[i] == 125:
                    escaped = True
                    # print ("%d unescape %d-%s, %d-%s"%(i, message_orig[i],hex(message_orig[i]), message_orig[i+1], hex(message_orig[i+1])))
                    message.append(message_orig[i + 1] + 32)
                    i += 1
                else:
                    message.append(message_orig[i])

                i += 1

        except Exception as e:
            print("Error: Unescaping received message")
            print(e)

        # keep CRC
        crc_value = message[-2:]
        # remove CRC from message
        message = message[:-2]

        # calculate CRC
        message_crc = self.crc16(message, 65535)  # remove CRC to calculate message CRC

        # Check CRC
        if message_crc != crc_value:
            print("Error: CRC Error")
            message_crc = self.crc16(message, 43690)  # remove CRC to calculate message CRC
            if message_crc == crc_value:
                print("It's a CORRECT FIRMWARE CRC")
                ### Firware manager , does not use protobuf, just straight bytes

                return
                """i = this.currentCommandValue;
                if (i == 0) {
                this.hardwareVersion = arrayList.get(0).byteValue() & 15;
                Log.d(TAG, "Hardware version: " + this.hardwareVersion);
                Log.d(TAG, "Bootloader version: " + (arrayList.get(0).byteValue() >> 4));
                Log.d(TAG, "Updating " + this.isUpdating);
                return"""

        ## CRC is Ok proceed
        respType=self.roaster.process_command_from_app(message)
        if respType is not None:
            try:
                self.send_message_queue.put(respType.SerializeToString())  ## add message to queue (no FRAME end no ACK)
            except Exception as e:
                print("Error: Invalid Message Serialize ProtoBuf")
                print(e)



    def update_value(self,characteristic):
        """
        Example of callback to send notifications

        :param characteristic:
        :return: boolean to indicate if timer should continue
        """


        if self.send_message_queue.empty() == False:
            try:
                message_orig = self.send_message_queue.get()
                message_orig = message_orig + self.crc16(message_orig, 65535)

                message = bytearray()

                ## Escape
                for i in range(len(message_orig)):
                    if message_orig[i] == 125:
                        message.append(125)
                        message.append(93)

                    else:
                        if message_orig[i] == 126:
                            message.append(125)
                            message.append(94)
                        else:
                            message.append(message_orig[i])

                message = bytearray([126]) + message + bytearray([126])

                print("Send: ", end="")
                for i in range(0, len(message)):
                    print(hex(message[i]), end=' ')
                print(" : len %d" % (len(message)))

                message_size_limit = 6
                for i in range(0, len(message), message_size_limit):
                    if i>0:
                        print("Multi send %d" % i)
                    sub_list = message[i:min(i + message_size_limit, len(message))]
                    bytes_array = bytearray(sub_list)
                    characteristic.set_value(bytes_array)  ## Send message


                #characteristic.set_value(message)  ## Send message

                send_update = False

            except Exception as e:
                print(characteristic)
                print("Error: Invalid Message")
                print(e)

        return characteristic.is_notifying

    def configuration_read(self, value, characteristic):
        print("Configuration Read")
    def configuration_write(self, value, characteristic):
        print("Configuration write")

    def configuration_notify(self, value, characteristic):
        print("Configuration notify")
    def __init__(self,adapter_address,roaster):
        self.notify_setup = False
        self.roaster = roaster
        self.advertised_name="IKAWA"
        self.adapter_address =adapter_address


        self.send_update = False
        self.long_message = bytearray()
        self.send_message_queue = Queue(maxsize=100)

        print ("Init BLE Peripheral %s"%adapter_address)

        # Create peripheral
        self.RoasterPeripheral = peripheral.Peripheral(adapter_address,
                                           local_name=self.advertised_name,
                                           appearance=0x0340)
        # Add service
        self.RoasterPeripheral.add_service(srv_id=1, uuid=self.IKAWA_SERVICE, primary=True)

        # Add characteristics
        self.RoasterPeripheral.add_characteristic(srv_id=1, chr_id=1, uuid=self.UUID_RECEIVE,
                                      value=[], notifying=False,
                                      # May not exactly match :standard, but
                                      # including read for tutorial
                                      flags=[ 'notify'],
                                      read_callback=None,
                                      write_callback=self.receive_test,
                                      notify_callback=self.notify_callback
                                      )

        self.RoasterPeripheral.add_characteristic(srv_id=1, chr_id=2, uuid=self.UUID_SEND,
                                      value=[], notifying=False,
                                      flags=['write'],
                                      read_callback=None,
                                      write_callback=self.receive_ikawaapp_command,
                                      notify_callback=None,
                                      )

        self.RoasterPeripheral.add_characteristic(srv_id=1, chr_id=3, uuid=self.UUID_CLIENT_CONFIGURATION,
                                      value=[], notifying=False,
                                      flags=['read', 'notify', 'write'],
                                      read_callback=self.configuration_read,
                                      write_callback=self.configuration_write,
                                      notify_callback=self.configuration_notify,
                                      )

        """for i in range(0,3):
            if (self.RoasterPeripheral.characteristics[i].is_notifying):
                print ("Set notify callback %d"%i)
                self.notify_callback(True,self.RoasterPeripheral.characteristics[i])
                break"""

