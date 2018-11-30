import time
import config
import udt
import util
import struct

# Go-Back-N reliable transport protocol.
class GoBackN:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_ip, local_port,
               remote_ip, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_ip, local_port, remote_ip, remote_port, self)
        self.msg_handler = msg_handler
        self.current_id = 0
        self.next_seq = 0
        self.window_size = config.WINDOW_SIZE
        self.packets_wait_sending = [None] * self.window_size
        # make sure role has a value even though local_port is missing
        self.role = "sender"
        if local_port == config.RECEIVER_LISTEN_PORT:
            self.role = "receiver"
        self._time = None
        self.required_seq = 0
        self.prepare_packet = util.generate_packet(b'', 3, self.required_seq)
        
    def get_next_id(self):
        return self.current_id % self.window_size+self.next_seq - self.current_id
        
    def base_is_next(self):
        return self.current_id == self.next_seq

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, msg):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        next_id=self.get_next_id()
        if next_id < self.window_size:
            self.packets_wait_sending[next_id] = util.generate_packet(msg, config.MSG_TYPE_DATA, self.next_seq)
            self.network_layer.send(self.packets_wait_sending[next_id])
            if self.base_is_next():
                self._time = time.time()
            self.next_seq = self.next_seq + 1
            return True
        if self._time and (time.time() - self._time > config.TIMEOUT_MSEC/1000):
            next_id=self.get_next_id()
            self._time = time.time()
        return False

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        msg = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.
        if self.role =="sender":
            if not util.is_message_corrupted(msg) and (struct.unpack("!H", msg[0:2])[0])==config.MSG_TYPE_ACK:
                self.current_id =  struct.unpack("!H", msg[2:4])[0] + 1
                if self.base_is_next():
                    self._time = None
                else:
                    self._time = time.time()
        else:
            if not util.is_message_corrupted(msg) and (struct.unpack("!H",msg[2:4])[0]) == self.required_seq:
                data = util.get_message(msg)
                try:
                    self.msg_handler(data.decode("utf-8"))
                    self.prepare_packet = util.generate_packet(b'', config.MSG_TYPE_ACK, self.required_seq)
                except:
                    print("message is corrupted")
                self.required_seq += 1
            self.network_layer.send(self.prepare_packet)

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this
        # class.
        if self.role == "sender":  # clear receiver's expected sequence number?
            while self.current_id < self.next_seq:
                time.sleep(config.TIMEOUT_MSEC/1000)
                for packet in self.packets_wait_sending[(self.current_id % self.window_size):(self.get_next_id())]:
                    self.network_layer.send(packet)
                pass
        self.network_layer.shutdown()
