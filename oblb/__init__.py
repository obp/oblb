import collections
import socket
from select import select

# composabable (layers of heirarchy) 
# readable by people and programs 
# exchangeability 
# discoverable

class Socket:
    def fileno(self):
        return self.socket.fileno()

    def wants_read(self):
        pass

    def wants_write(self):
        pass

    def wants_exception(self):
        pass

    def read_ready(self):
        pass

    def write_ready(self):
        pass

    def exception_ready(self):
        pass


class DeadConnection(Socket):
    pass

class TransportSocket(Socket):
    buffer = None

    def read_ready(self):
        print "TransportationSocket.read_Ready"
        if not self.peer.socket:
            return self.exception_ready()
        try:
            self.peer.buffer = self.socket.recv(102400)
        except socket.error:
            return self.exception_ready()
        if not self.peer.buffer:
            self.exception_ready()

        
    def write_ready(self):

        if self.buffer:
            try:
                amount = self.socket.send(self.buffer)
            except socket.error:
                return self.exception_ready()
                
            self.buffer = self.buffer[amount:]
        elif not self.peer.socket:
            self.exception_ready()
            

    def exception_ready(self):
        self.socket.close()
        self.socket = None
        self.__class__ = DeadConnection
        try:
            self.items.remove(self)
        except ValueError:
            pass

    
    def wants_read(self):
        return not self.peer.buffer

    def wants_write(self):
        return self.buffer or not self.peer.socket

    def wants_exception(self):
        return True


class Remote(TransportSocket):
    def __init__(self, peer, target, items):
        self.items = items
        self.peer = peer
        self.target = target
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.host, self.port = self.target.split(':')
        self.port = int(self.port)
        self.socket.connect((self.host, self.port))
        self.buffer = ""


class VirginRemote(Remote):
    def read_ready(self, *args):
        self.__class__ = Remote
        self.read_ready(*args)
    
    def write_ready(self, *args):
        self.__class__ = Remote
        self.write_ready(*args)

    def exception_ready(self, *args):
        self.socket.close()
        self.items.remove(self)
        self.peer.retry()

    
class Local(TransportSocket):
    def __init__(self, counter, items, targets, socket, address):
        self.items = items
        self.counter = counter
        self.socket = socket
        self.targets = list(targets)
        self.address = address
        self.retry()

    def retry(self):
        if not self.targets:
            self.items.remove(self)
            return 
        target_number = self.counter % len(self.targets)
        target = self.targets.pop(target_number)
        self.peer = VirginRemote(self, target, self.items)
        self.counter /= (len(self.targets) + 1)
        self.items.append(self.peer)
        self.buffer = ""

    def pop_target(self):
        return 


class Listener(Socket):
    def __init__(self, address, items, targets):
        self.counter = 0
        self.addresses = address
        self.items = items
        self.targets = targets
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        host, port = address.split(':')
        port = int(port)
        self.socket.bind((host, port))
        self.socket.listen(100)

    def read_ready(self):
        self.counter += 1 
        self.items.append(Local(self.counter, self.items, self.targets,  *self.socket.accept()))

    def exception_ready(self):
        sys.exit(1)

    def wants_read(self):
        return True

    def wants_write(self):
        return False

    def wants_exception(self):
        return True

def main(argv):
    """Usage: oblb source_host:source_port target_host:target_port ... 
    
    oblb is crazy simple.  So simple it has no command line flags.  

    You simply list a series of host:port combinations, the first
    being the address to bind to and the rest being connections to
    forward to.  obln just gets the rest right and does it fast.

    """
    if len(argv) < 3:
        print __doc__
        return 1 

    source = argv[1]
    targets = argv[2:]
    
    items = []
    items.append(Listener(source, items, targets))

    while True:
        reads, writes, exceptions = select(
            [i for i in items if i.wants_read()], 
            [i for i in items if i.wants_write()], 
            [i for i in items if i.wants_exception()])
                
        for write in writes:
            write.write_ready()

        for read in reads:
            read.read_ready()

        for error in exceptions:
            error.exception_ready()
