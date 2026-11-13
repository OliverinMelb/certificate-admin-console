"""Run real HTTP export measurements against an explicit generated database."""

import argparse
import csv
import ctypes
from ctypes import wintypes
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import socket
import sqlite3
import subprocess
import sys
import time

import httpx


ROOT = Path(__file__).resolve().parents[1]


class Download(io.RawIOBase):
    def __init__(self, response):
        super().__init__()
        self.chunks = response.iter_raw()
        self.pending = b''
        self.size = 0
        self.digest = hashlib.sha256()

    def readable(self):
        return True

    def readinto(self, buffer):
        if not self.pending:
            self.pending = next(self.chunks, b'')
            self.size += len(self.pending)
            self.digest.update(self.pending)
        count = min(len(buffer), len(self.pending))
        buffer[:count] = self.pending[:count]
        self.pending = self.pending[count:]
        return count


def peak_memory(pid):
    if os.name != 'nt':
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD),
                    ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t),
                    ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t),
                    ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t),
                    ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
    handle = kernel.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return None
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return counters.PeakWorkingSetSize
    finally:
        kernel.CloseHandle(handle)
    return None


def measure(client, params, expected, probe_list=False):
    started = time.perf_counter()
    listing_at = None
    previous = None
    count = 0
    with client.stream('GET', '/api/certificates/export.csv', params=params,
                       headers={'X-Actor-Id': 'alice'}) as response:
        response.raise_for_status()
        download = Download(response)
        reader = csv.reader(io.TextIOWrapper(io.BufferedReader(download), encoding='utf-8-sig', newline=''))
        assert next(reader) == ['learner_name', 'course_title', 'serial_number', 'issued_local_date']
        if probe_list:
            listing = client.get('/api/certificates', headers={'X-Actor-Id': 'alice'})
            assert listing.status_code == 200 and listing.json()['total'] == expected
            listing_at = time.perf_counter() - started
        field = {'learner_name': 0, 'serial_number': 2, 'issue_date': 3}[params['sort']]
        for row in reader:
            serial = row[2]
            if serial.startswith('PERF-'):
                identifier = 'perf-cert-' + serial[5:]
            else:
                assert serial.startswith('EAST-'), f'wrong tenant: {serial}'
                identifier = 'east-cert-' + serial[5:]
            key = row[field], identifier
            if previous is not None:
                if key[0] == previous[0]:
                    assert key[1] > previous[1], 'unstable tie or duplicate'
                elif params['order'] == 'asc':
                    assert key[0] > previous[0], 'incorrect ascending order'
                else:
                    assert key[0] < previous[0], 'incorrect descending order'
            previous = key
            count += 1
    elapsed = time.perf_counter() - started
    assert count == expected, (count, expected)
    assert elapsed <= 60, f'export took {elapsed:.3f}s'
    assert listing_at is None or listing_at < elapsed
    return {'query': params, 'rows': count, 'seconds': round(elapsed, 3),
            'bytes': download.size, 'sha256': download.digest.hexdigest(),
            'list_response_seconds_before_eof': round(listing_at, 3) if listing_at is not None else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True, type=Path)
    parser.add_argument('--rows', type=int, default=100000)
    args = parser.parse_args()
    path = args.database.resolve(strict=True)
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port = listener.getsockname()[1]
    env = {**os.environ, 'PYTHONPATH': str(ROOT / 'backend'), 'PYTHONUTF8': '1'}
    code = '''import os,sys,threading,uvicorn
from app.main import create_app
server = uvicorn.Server(uvicorn.Config(create_app(sys.argv[1]),host="127.0.0.1",port=int(sys.argv[2]),log_level="error"))
threading.Thread(target=lambda: (os.read(sys.stdin.fileno(),1),setattr(server,"should_exit",True)),daemon=True).start()
print(os.getpid(),flush=True)
server.run()
'''
    process = subprocess.Popen([sys.executable, '-c', code, str(path), str(port)], env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        server_pid = int(process.stdout.readline())
        with httpx.Client(base_url=f'http://127.0.0.1:{port}', timeout=60, trust_env=False) as client:
            deadline = time.monotonic() + 15
            while True:
                try:
                    if client.get('/api/health').status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError('server failed to start')
                time.sleep(.05)
            params = {'q': '', 'sort': 'issue_date', 'order': 'desc'}
            results = [measure(client, params, args.rows, probe_list=True), measure(client, params, args.rows)]
            assert results[0]['sha256'] == results[1]['sha256']
            expected_filtered = min(2000, args.rows - 12)
            results.append(measure(client, {'q': 'Perf Learner 000', 'sort': 'learner_name', 'order': 'asc'},
                                   expected_filtered))
            print(json.dumps({'platform': platform.platform(), 'python': sys.version.split()[0],
                              'sqlite': sqlite3.sqlite_version, 'machine': platform.machine(),
                              'processor': platform.processor(), 'logical_cpus': os.cpu_count(),
                              'server_peak_working_set_bytes': peak_memory(server_pid),
                              'results': results}, indent=2))
    finally:
        process.stdin.close()
        process.wait(timeout=10)
        process.stdout.close()


if __name__ == '__main__':
    main()
