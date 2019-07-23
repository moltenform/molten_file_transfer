# mft_server_top.py
# Ben Fisher, 2019
# Released under the GNU General Public License version 3

# this is very simple code, only designed to
# support one file-transfer request at a time.
# uses some example code by Sergio Tanzilli
# (acmesystems.it/python_http)

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import cgi
import sys

from mft_common import *
import mft_server_impl

class MoltenFileTransferServer(BaseHTTPRequestHandler):
    stateGetFile = Bucket()
    stateSendFile = Bucket()

    def __init__(self, *args, **kwags):
        BaseHTTPRequestHandler.__init__(self, *args, **kwags)
    
    def do_GET(self):
        # overrides the default implementation
        return self.doAndCatch(lambda: self.do_GETImpl())
    
    def do_POST(self):
        # overrides the default implementation
        return self.doAndCatch(lambda: self.do_POSTImpl())
    
    def log_message(self, format, *args):
        # overrides the default implementation
        if self.logfile:
            self.logfile.write("%s - - [%s] %s\n" %
                (self.client_address[0],
                 self.log_date_time_string(),
                 format % args))
            self.logfile.flush()

    def do_GETImpl(self):
        url = self.path
        parsed = urlparse(url)
        getParams = GetParamWrapper(parse_qs(parsed.query))
        pathBefore = self.path.split('?')[0]
        if not self.isTokenValid(getParams):
            return
        
        if self.filesPath == 'listen' and not pathBefore.endswith('/ping'):
            raise MoltenTFException(
                'Server was set up for recieving files, it can\'t send files.')
        
        response = None
        if pathBefore.endswith('/get_file_list'):
            response = mft_server_impl.get_file_list(
                getParams, self.stateGetFile, self.filesPath, self.filesIsStar)
        elif pathBefore.endswith('/get_file'):
            response = mft_server_impl.get_file(
                getParams, self.stateGetFile)
        elif pathBefore.endswith('/get_file_complete'):
            response = mft_server_impl.get_file_complete(
                getParams, self.stateGetFile)
        elif pathBefore.endswith('/ping'):
            response = Bucket(directPath=None, response='Molten:Success')
        else:
            raise MoltenTFException(
                f'No such endpoint (get): {self.path}', 404)

        mimetype = 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-type', mimetype)
        self.end_headers()
        if response.directPath:
            with open(response.directPath, 'rb') as f:
                memoryEfficientCopyFileObject(f, self.wfile)
        else:
            self.wfile.write(response.response.encode('utf-8'))

    def do_POSTImpl(self):
        # even though this is a post, we send query parameters as if it were a get
        # this is because Request module sendfile seems to only be able to
        # stream post data when sending it unstructured, so we'll send in
        # params in the url this way.
        url = self.path
        parsed = urlparse(url)
        getParams = GetParamWrapper(parse_qs(parsed.query))
        pathBefore = self.path.split('?')[0]
        if not self.isTokenValid(getParams):
            return
        
        if self.filesPath != 'listen':
            raise MoltenTFException(
                'Server was set up for sending files, it can\'t receive files.')
        
        response = None
        if pathBefore.endswith('/send_file_list'):
            response = mft_server_impl.send_file_list(
                getParams, self.stateSendFile)
        elif pathBefore.endswith('/send_file'):
            response = mft_server_impl.send_file(
                getParams, self.stateSendFile, self.rfile, self.headers)
        elif pathBefore.endswith('/send_file_complete'):
            response = mft_server_impl.send_file_complete(
                getParams, self.stateSendFile)
        else:
            raise MoltenTFException(
                f'No such endpoint (post): {self.path}', 404)
            
        mimetype = 'application/octet-stream'
        self.send_response(200)
        self.send_header('Content-type', mimetype)
        self.end_headers()
        self.wfile.write(response.response.encode('utf-8'))
        
    def traditionalHandlePost(self):
        env = {'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': self.headers['Content-Type']}
    
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ=env)
    
        # allow unused variable since this is just example code
        data = form['key'].value  # noqa: F841
    
    def isTokenValid(self, params):
        tkGot = params.get('token')
        if isinstance(tkGot, bytes):
            tkGot = tkGot.decode('utf-8')
        if tkGot != self.token:
            MoltenFileTransferServer.countIncorrectTokens += 1
            msg = 'Incorrect or missing token!'
            showMsg(msgHigh, msg)
            if MoltenFileTransferServer.countIncorrectTokens >= 3:
                msg += ' Sleeping.'
                clientTimeoutTime = 10
                showMsg(msgMed, f'Sleeping for {clientTimeoutTime - 1}s')
                import time
                time.sleep(clientTimeoutTime - 1)
            
            self.mySendErr(msg, 401)
            return False
        else:
            return True

    def mySendErr(self, s, code=500):
        self.error_message_format = '''\nMessage: %(code)s - %(explain)s\n'''
        self.send_error(code, explain=s)
        
    def doAndCatch(self, fn):
        try:
            fn()
        except MoltenTFException as err:
            self.mySendErr(str(err))
        except:
            if debugMode():
                raise
            else:
                exc = sys.exc_info()[1]
                msg = 'Unhandled exception...' + str(exc)
                showMsg(msgHigh, msg)
                self.mySendErr(msg)

        showMsg(msgVerbose, 'Listening...')
        showMsg(msgMed,
            f'the address for this server is: {self.myIpAddr}')
        showMsg(msgMed,
            f'the token for this server is: {self.token}')

def goStartServer(filesIsStar, filesPath):
    try:
        showMsg(msgMed, 'welcome to moltenfiletransfer_server!')
        token = genToken()
        myIpAddr = displayActual192_168Address()
        showMsg(msgMed,
            f'the address for this server is: {myIpAddr}')
        showMsg(msgMed,
            f'the token for this server is: {token}')
        
        server = HTTPServer(('', getPortNumber()), MoltenFileTransferServer)
        server.RequestHandlerClass.token = token
        server.RequestHandlerClass.myIpAddr = myIpAddr
        server.RequestHandlerClass.filesIsStar = filesIsStar
        server.RequestHandlerClass.filesPath = filesPath
        server.RequestHandlerClass.countIncorrectTokens = 0
        logPath = f'{getOurDirectory()}/log'
        
        def makeLogFile():
            server.RequestHandlerClass.logfile = open(logPath, 'a')
        doAndCheckForFileAccessErrAndReRaise(makeLogFile, logPath)
        showMsg(msgMed, 'started server on port', getPortNumber())
        showMsg(msgMed, '\nReady to go! When you are done, press ctrl-c to exit.')
        server.serve_forever()
    except:
        showMsg(msgMed, 'shutting down the server')
        server.socket.close()
        raise
