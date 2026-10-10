"""Upload one ordinary file over non-PTY SSH, verify remote SHA256.
Requires paramiko. Password is prompted locally, never an argument. Host-key
SHA256 fingerprint must have been verified separately through a trusted channel.
No extraction, execution, partition access or final configuration replacement.
"""
import argparse,base64,getpass,hashlib,pathlib,shlex,socket,sys
import paramiko
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--host',required=True);p.add_argument('--user',default='root');p.add_argument('--host-key-sha256',required=True)
p.add_argument('--source',type=pathlib.Path,required=True);p.add_argument('--target',required=True)
a=p.parse_args();target=pathlib.PurePosixPath(a.target)
if not target.is_absolute() or '..' in target.parts or target.parent!=pathlib.PurePosixPath('/tmp'):
    p.error('Only a new direct child file of /tmp/ is accepted; final deployment is a separate reviewed step.')
data=a.source.read_bytes();digest=hashlib.sha256(data).hexdigest()
s=socket.create_connection((a.host,22),timeout=15);t=paramiko.Transport(s);t.start_client(timeout=15)
actual='SHA256:'+base64.b64encode(hashlib.sha256(t.get_remote_server_key().asbytes()).digest()).decode().rstrip('=')
if actual!=a.host_key_sha256:t.close();p.exit(2,'Host key mismatch; nothing uploaded.\n')
t.auth_password(a.user,getpass.getpass('SSH password: '))
q=shlex.quote(str(target));ch=t.open_session();ch.settimeout(120);ch.exec_command('set -C; umask 077; cat > '+q)
ch.sendall(data);ch.shutdown_write()
while ch.recv(65536):pass
if ch.recv_exit_status()!=0:t.close();p.exit(2,'Upload refused/failed; check target separately.\n')
ch=t.open_session();ch.settimeout(30);ch.exec_command('sha256sum '+q);out=b''
while chunk:=ch.recv(4096):out+=chunk
if ch.recv_exit_status()!=0 or not out.split() or out.split()[0].decode()!=digest:
    t.close();p.exit(2,'Readback mismatch. Do not deploy or execute this file.\n')
t.close();print('SHA256 verified:',digest)
