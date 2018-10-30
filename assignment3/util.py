import config
import dummy
import gbn
import ss
import threading
import struct

# Factory method to construct transport layer.
def get_transport_layer(sender_or_receiver,
                        transport_layer_name,
                        msg_handler):
    assert sender_or_receiver == 'sender' or sender_or_receiver == 'receiver'
    if sender_or_receiver == 'sender':
        return _get_transport_layer_by_name(transport_layer_name,
                                        config.SENDER_IP_ADDRESS,
                                        config.SENDER_LISTEN_PORT,
                                        config.RECEIVER_IP_ADDRESS,
                                        config.RECEIVER_LISTEN_PORT,
                                        msg_handler)
    if sender_or_receiver == 'receiver':
        return _get_transport_layer_by_name(transport_layer_name,
                                        config.RECEIVER_IP_ADDRESS,
                                        config.RECEIVER_LISTEN_PORT,
                                        config.SENDER_IP_ADDRESS,
                                        config.SENDER_LISTEN_PORT,
                                        msg_handler)


def _get_transport_layer_by_name(name, local_ip, local_port, 
                                 remote_ip, remote_port, msg_handler):
    assert name == 'dummy' or name == 'ss' or name == 'gbn'
    if name == 'dummy':
        return dummy.DummyTransportLayer(local_ip, local_port,
                                     remote_ip, remote_port, msg_handler)
    if name == 'ss':
        return ss.StopAndWait(local_ip, local_port,
                          remote_ip, remote_port, msg_handler)
    if name == 'gbn':
        return gbn.GoBackN(local_ip, local_port,
                       remote_ip, remote_port, msg_handler)


# Convenient class to run a function periodically in a separate
# thread.
class PeriodicClosure:
    def __init__(self, handler, interval_sec):
        self._handler = handler
        self._interval_sec = interval_sec
        self._lock = threading.Lock()
        self._timer = None

    def _timeout_handler(self):
        with self._lock:
            self._handler()
            self.start()

    def start(self):
        self._timer = threading.Timer(self._interval_sec, self._timeout_handler)
        self._timer.start()

    def stop(self):
        with self._lock:
            if self._timer:
                self._timer.cancel()
                
#helper functions which are used in ss.py and gbn.py
def get_message(message):
    if message[6:7] == b'\x00':
        return message[7:]
    return message[6:]
    
def check_ack(message, target):
    message_type = struct.unpack("!H", message[0:2])[0]
    sequence = struct.unpack("!H", message[2:4])[0]
    return (message_type == config.MSG_TYPE_ACK and sequence == target)
    
def generate_packet(message, message_type, sequence):
    if len(message) % 2 != 0:
        message = b'\x00' + message
    sum = message_type + sequence
    part1 = (sum & 0xffff) + (sum >> 16)
    for i in range(0, len(message), 2):
        part2 = (message[i] << 8) + message[i + 1]
        sum2 = part1 + part2
        part1 = (sum2 & 0xffff) + (sum2 >> 16)
    checksum = ~part1 & 0xffff
    return struct.pack("!H", message_type) + struct.pack("!H", sequence) + struct.pack("!H", checksum) + message