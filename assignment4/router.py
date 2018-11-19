import os.path
import socket
import table
import threading
import util
import struct

_CONFIG_UPDATE_INTERVAL_SEC = 5

_MAX_UPDATE_MSG_SIZE = 1024
_BASE_ID = 8000

def _ToPort(router_id):
    return _BASE_ID + router_id

def _ToRouterId(port):
    return port - _BASE_ID

class Router:
    def __init__(self, config_filename):
        # ForwardingTable has 3 columns (DestinationId,NextHop,Cost). It's
        # threadsafe.
        self._forwarding_table = table.ForwardingTable()
        # Config file has router_id, neighbors, and link cost to reach
        # them.
        self._config_filename = config_filename
        self._router_id = None
        # Socket used to send/recv update messages (using UDP).
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.config = {}

    def handler(self, data, addr):
        data_format = '!h' + str((len(data) - 2) // 2) + 'h'
        data = struct.unpack(data_format, data)
        messages = []
        for i in range(data[0]):
            messages.append((data[2 * i + 1], data[2 * i + 2]))
        received_hop_id = _ToRouterId(addr[1])
        self.update_neighbour_cost(messages, received_hop_id)

    def start(self):
        #Start a periodic closure to update config.
        self._config_updater = util.PeriodicClosure(self.load_config, _CONFIG_UPDATE_INTERVAL_SEC)
        self._config_updater.start()
        # TODO: init and start other threads.
        self._message_sender = util.PeriodicClosure(self.send_message, _CONFIG_UPDATE_INTERVAL_SEC)
        self._message_sender.start()
        threads = []
        while True:
            data, addr = self._socket.recvfrom(_MAX_UPDATE_MSG_SIZE)
            t = threading.Thread(target=self.handler, args=(data, addr,))
            threads.append(t)
            t.start()

    def stop(self):
        if self._config_updater:
            self._config_updater.stop()
        # TODO: clean up other threads.
        if self._message_sender:
            self._message_sender.stop()

    def load_config(self):
        assert os.path.isfile(self._config_filename)
        initial_costs = {}
        with open(self._config_filename, 'r') as f:
            router_id = int(f.readline().strip())
            # Only set router_id when first initialize.
            if not self._router_id:
                self._socket.bind(('localhost', _ToPort(router_id)))
                self._router_id = router_id
            # TODO: read and update neighbor link cost info.
            for line in f:
                data = line.split(',')
                if len(data) == 2:
                    neighbor_id = int(data[0].strip())
                    c_cost = int(data[1].strip())
                    initial_costs[neighbor_id] = c_cost
                elif len(data) == 1:
                    neighbor_id = int(data[0].strip())
                    initial_costs[neighbor_id] = 0

        if not self.config or self.config != initial_costs:
            self.config = initial_costs
            self.send_initial_data_to_neighbour(self.config)

    def send_initial_data_to_neighbour(self, config):
        entries = self._forwarding_table.snapshot()
        for c_id in config.keys():
            ext =0
            for i in range (len(entries)):
                entry = entries[i]
                if entry[0]==c_id:
                    ext = 1
                    if entry[2] != config[c_id]:
                        entries[i] = (c_id, self._router_id, config[c_id])
                    else:
                        continue
            if ext == 0:
                entries.append((c_id, self._router_id, config[c_id]))
        self._forwarding_table.reset(entries)
        print('The initial entries of router_id ', self._router_id, 'are: ')
        for entry in entries:
            print('neighbor id: ', entry[0], 'link cost: ', entry[2])
        self.send_message()

    # update entries
    def update_neighbour_cost(self, messages, hop_id):
        need_to_send_to_neighbour = 0
        entries = self._forwarding_table.snapshot()
        # c_ means current
        for c_entry in entries:
            if hop_id == c_entry[0]:
                neighbout_cost = c_entry[2]

        for message in messages:
            c_id = message[0]
            if c_id is not self._router_id:
                # check if c_id exsits in entries, 0 --> no , 1 --> yes
                exsits = 0
                for i in range (len(entries)):
                    entry = entries[i]
                    if c_id == entry[0]:
                        exsits = 1
                        if message[1] + neighbout_cost < entry[2]:
                            need_to_send_to_neighbour = 1
                            entries[i] = (c_id, hop_id, message[1] + neighbout_cost)
                        elif hop_id == entry[1]:
                            cost = entry[2]
                            if c_id not in self.config.keys() or message[1] + neighbout_cost < self.config[c_id]:
                                entries[i] = (c_id, hop_id, message[1] + neighbout_cost)
                            else:
                                entries[i] = (c_id,self._router_id, self.config[c_id])
                            if cost != entry[2]:
                                need_to_send_to_neighbour = 1
                if exsits == 0:
                    need_to_send_to_neighbour = 1
                    entries.append((c_id, hop_id, message[1] + neighbout_cost))
        self._forwarding_table.reset(entries)
        if need_to_send_to_neighbour == 1:
            print('The entries of router_id ',self._router_id,' are: ')
            for entry in entries:
                print('neighbor id: ', entry[0], 'link cost: ', entry[2])
            self.send_message()
        else:
            print('The entries of router_id ',self._router_id,' remains unchanged.')

    #send cost information to neighbours
    def send_message(self):
        for c_id in self.config.keys():
            messages = []
            entries = self._forwarding_table.snapshot()
            for entry in entries:
                messages.append((entry[0], entry[2]))

            #message-->(neighbour_id, cost)
            #messages-->a list of message
            data = struct.pack('!h', len(messages))
            for m in messages:
                data += struct.pack('!h', m[0]) + struct.pack('!h', m[1])

            self._socket.sendto(data, ('localhost', _ToPort(c_id)))
