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

    def read_ready(self, items):
        print "Read ready", self

    def write_ready(self, items):
        print "Write ready", self

    def exection_ready(self, items):
        print "Exception ready", self

class TransportSocket(Socket):
    buffer = None

    def read_ready(self):
        self.buffer = self.socket.recv(1024*1024)
        if not self.buffer:
            self.socket.close()
            self.peer.socket.close()
            self.items.remove(self)
            self.items.remove(self.peer)
            return 
        bytes = self.peer.socket.send(self.buffer)
        self.buffer = self.buffer[bytes:]
        if not self.buffer:
            self.buffer = None

        
    def write_ready(self):
        if self.peer.buffer is not None:
            if self.socket.send(self.peer.buffer):
                self.peer.buffer = None

    def exception_ready(self):
        self.socket.close()
        self.peer.socket.close()
        self.items.remove(self)
        self.items.remove(peer)
    
    def wants_read(self):
        return self.buffer is None

    def wants_write(self):
        return self.peer.buffer is not None

    def wants_exception(self):
        return True


class Remote(TransportSocket):
    def __init__(self, peer, target):
        self.peer = peer
        self.target = target
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM)
        self.host, self.port = self.target.split(':')
        self.port = int(self.port)
        self.socket.connect((self.host, self.port))
        self.buffer = None


class VirginRemote(Remote):
    def read_ready(self, *args):
        self.__class__ = Remote
        self.read_ready(*args2)
    
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
        self.peer = Remote(self, self.targets.pop(self.counter % len(self.targets)))
        if len(self.targets) > 1:
            self.counter /= len(self.targets) - 1
        self.items.append(self.peer)
        self.buffer = None

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
        self.socket.listen(5)

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
                
        for read in reads:
            read.read_ready()

        for write in writes:
            write.write_ready()

        for error in exceptions:
            error.exception_ready()
