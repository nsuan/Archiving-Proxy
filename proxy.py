__doc__ = """Tiny HTTP Proxy.
This module implements GET, HEAD, POST, PUT and DELETE methods
on BaseHTTPServer, and behaves as an HTTP proxy.

Any help will be greatly appreciated.		SUZUKI Hisao
"""

__version__ = "1.0"

import BaseHTTPServer, select, socket, SocketServer, urlparse, time, os, string
from config import *

class ProxyHandler (BaseHTTPServer.BaseHTTPRequestHandler):
    __base = BaseHTTPServer.BaseHTTPRequestHandler
    __base_handle = __base.handle

    server_version = "TinyHTTPProxy/" + __version__
    rbufsize = 0                        # self.rfile Be unbuffered

    def handle(self):
	try:
        	(ip, port) =  self.client_address
	except:
		(ip, port, yeah, ok) =  self.client_address
        if hasattr(self, 'allowed_clients') and ip not in self.allowed_clients:
            self.raw_requestline = self.rfile.readline()
            if self.parse_request(): self.send_error(403)
        else:
            self.__base_handle()

    def _connect_to(self, netloc, soc, timeout=5):
        i = netloc.find(':')
        if i >= 0:
            host_port = netloc[:i], int(netloc[i+1:])
        else:
            host_port = netloc, 80
        #print "\t" "connect to %s:%d" % (host_port[0], host_port[1])
	tup = None
	try:
		tup = socket.getaddrinfo(host_port[0], host_port[1], socket.AF_INET6, socket.SOCK_STREAM)
		tup.append(socket.getaddrinfo(host_port[0], host_port[1], socket.AF_INET, socket.SOCK_STREAM))
	except:
		tup = socket.getaddrinfo(host_port[0], host_port[1], socket.AF_INET, socket.SOCK_STREAM)

	for res in tup:
		af, socktype, proto, canonname, sa = res
		sock = None
		try:
			
			sock = socket.socket(af, socktype, proto)
			if timeout is not None:
				sock.settimeout(timeout)
			else:
				sock.settimeout(10)
			try:
				sock.bind((localbind,0))
			except:
				pass
			sock.connect(sa)
			return sock

        	except:
			raise
	            	try: 
				msg = arg[1]
			except: 
				msg = arg
				self.send_error(503, msg)
				return None

    def do_CONNECT(self):
        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if self._connect_to(self.path, soc):
                self.log_request(200)
                self.wfile.write(self.protocol_version +
                                 " 200 Connection established\r\n")
                self.wfile.write("Proxy-agent: %s\r\n" % self.version_string())
                self.wfile.write("\r\n")
                self._read_write(soc, 300)
        finally:
            print "\t" "bye"
            soc.close()
            self.connection.close()

    def do_GET(self):
        (scm, netloc, path, params, query, fragment) = urlparse.urlparse(
            self.path, 'http')
        if scm != 'http' or fragment or not netloc:
            self.send_error(400, "bad url %s" % self.path)
            return

	global dir

        try:
            t = time.time()
	    f = None
	    soc = None
	    soc = self._connect_to(netloc, None)
            if soc is not None:
                #self.log_request()
		path = fixpath(path, netloc)
		try: 
			if path == '/':
				lpath  = '/index.html'
			else:
				lpath = path
			if query != '':
				lquery = '?' + query 
			else:
				lquery = query
			fname = dir + str(int(t - (t % 86400))) + '/' + netloc + lpath + params + lquery
			print "Name: " + fname
			d = os.path.dirname(fname)
			if not os.path.exists(d):
				os.makedirs(d)
			if not os.path.exists(fname) or os.path.getsize(fname) == 0:
				f = open(fname,'w')
		except:
			#raise
			pass

                soc.send("%s %s %s\r\n" % (
                    self.command,
                    urlparse.urlunparse(('', '', path, params, query, '')),
                    self.request_version))
                self.headers['Connection'] = 'close'
                del self.headers['Proxy-Connection']
                for key_val in self.headers.items():
                    soc.send("%s: %s\r\n" % key_val)
                soc.send("\r\n")
                self._read_write(soc,f)
		try:
			f.close
		except:
			pass
		print str(time.time() -t)
        finally:
            print "\t" "bye"
            if soc is not None:
	            soc.close()
            self.connection.close()

    def _read_write(self, soc, f=None, max_idling=20):
        iw = [self.connection, soc]
        ow = []
        count = 0
	data2 = ''
	head = True
        while 1:
            count += 1
            (ins, _, exs) = select.select(iw, ow, iw, 3)
            if exs: break
            if ins:
                for i in ins:
                    if i is soc:
                        out = self.connection
                    else:
                        out = soc
                    data = i.recv(512)
                    if data:
			if head == True and f is not None:
				data2 = data2 + data
				offset = string.find(data2, "\r\n\r\n")
				if offset != -1:
					head = False
					data2 = data2 [offset+4:] 			  
					try:
						f.write(data2)
					except:
						pass
			elif f is not None:
				try:
					f.write(data)
				except:
					pass
                        out.send(data)
                        count = 0
            else:
                print "\t" "idle", count
            if count == max_idling: break
	if f is not None and len(data2) > 0 and head == True:
			try:
				f.write(data2)
			except:
				pass
		
    do_HEAD = do_GET
    do_POST = do_GET
    do_PUT  = do_GET
    do_DELETE=do_GET

class ThreadingHTTPServer (SocketServer.ThreadingMixIn,BaseHTTPServer.HTTPServer): 
    address_family = socket.AF_INET6

if __name__ == '__main__':
    from sys import argv
    if argv[1:] and argv[1] in ('-h', '--help'):
        print argv[0], "[port [allowed_client_name ...]]"
    else:
        if argv[2:]:
            allowed = []
            for name in argv[2:]:
                client = socket.gethostbyname(name)
                allowed.append(client)
                print "Accept: %s (%s)" % (client, name)
            ProxyHandler.allowed_clients = allowed
            del argv[2:]
        else:
            print "Any clients will be served..."
        #BaseHTTPServer.test(ProxyHandler, ThreadingHTTPServer)
	server_address = ('::', int(argv[1]))
	httpd = ThreadingHTTPServer(server_address, ProxyHandler)
	httpd.serve_forever()
