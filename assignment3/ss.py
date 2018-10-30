import udt
import util
import config
import time
import struct

# Stop-And-Wait reliable transport protocol.
class StopAndWait:
    # "msg_handler" is used to deliver messages to application layer
    # when it's ready.
    def __init__(self, local_ip, local_port, 
               remote_ip, remote_port, msg_handler):
        self.network_layer = udt.NetworkLayer(local_ip, local_port,
                                          remote_ip, remote_port, self)
        self.msg_handler = msg_handler
        # wait for call 0 is 0, wait for call 1 is 1; wait for ack0 is 2, wait for ack1 is 3
        # initial state: wait for call 0
        self.current_state = 0
        self.next_ack_message = None
        # make sure role has a value even though local_port is missing
        self.role = "sender"
        if local_port == config.RECEIVER_LISTEN_PORT:
            self.role = "receiver"
        self.received_packet= None
        # we need a timer in Stop-And-Wait protocol, it will run when
        self._time = None
        
    def send_packet_message(self, message, sequence):
        prepare_packet = util.generate_packet(message, config.MSG_TYPE_DATA, sequence)
        self.network_layer.send(prepare_packet)
        
    def wait_for_ack(self, sequence):
        # if time out
        if time.time() - self._time > config.TIMEOUT_MSEC:
            self.send_packet_message(self.next_ack_message, sequence)
            #get the current time
            self._time = time.time()
            return False
        elif not self.received_packet is None:
                if not (util.check_ack(self.received_packet, sequence)):
                    return False
                else:
                    #clear the time
                    self._time = None
                    self.current_state = self.current_state + 1
                    return True
        else:
            return False

    # "send" is called by application. Return true on success, false
    # otherwise.
    def send(self, message):
        # TODO: impl protocol to send packet from application layer.
        # call self.network_layer.send() to send to network layer.
        if self.current_state < 2:
            self.send_packet_message(message, int (self.current_state / 2))
            #get the current time
            self._time = time.time()
            self.next_ack_message = message
            return True
        else: 
            self.wait_for_ack(int(self.current_state / 2))
            return False

    # "handler" to be called by network layer when packet is ready.
    def handle_arrival_msg(self):
        message = self.network_layer.recv()
        # TODO: impl protocol to handle arrived packet from network layer.
        # call self.msg_handler() to deliver to application layer.
        if self.role == "receiver":
            if (struct.unpack("!H", message[2:4])[0])!= self.current_state:
                if (self.current_state  != 1):
                    self.send_packet_message(b'',1) 
                else:
                    self.send_packet_message(b'',0) 
            else:
                data = util.get_message(message)
                try:
                    self.msg_handler(data.decode("utf-8"))
                    self.send_packet_message(b'',self.current_state)
                except:
                    print("message is corrupted")
                    self.send_packet_message(b'',self.current_state)
        else:
            self.received_packet = message

    # Cleanup resources.
    def shutdown(self):
        # TODO: cleanup anything else you may have when implementing this
        # class.
        while self.current_state ==1 or self.current_state ==3:
            while not self.wait_for_ack(int(self.current_state / 2)):
                time.sleep(config.MSG_LOST_PROB)
                pass
        self.network_layer.shutdown()

