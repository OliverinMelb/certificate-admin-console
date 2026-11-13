"""Bounded CSV producer: one worker owns its SQLite snapshot for the full stream."""

import csv
from io import StringIO
from queue import Empty, Full, Queue
from threading import Event, Thread
import unicodedata

import anyio
from fastapi import HTTPException
from starlette.responses import JSONResponse, StreamingResponse

from app.certificate_query import certificate_query, project
from app.database import connect


FIELDS = ('learner_name', 'course_title', 'serial_number', 'issued_local_date')
_DONE = object()


def safe_text(value):
    stripped = value
    while stripped and (stripped[0].isspace() or unicodedata.category(stripped[0]).startswith('C')):
        stripped = stripped[1:]
    if value.startswith(('\t', '\r', '\n')) or stripped.startswith(('=', '+', '-', '@')):
        return "'" + value
    return value


class CSVResponse(StreamingResponse):
    def __init__(self, database_path, tenant_id, q, sort, order):
        super().__init__((), media_type='text/csv',
                         headers={'Content-Disposition': 'attachment; filename="certificates.csv"'})
        self.arguments = database_path, tenant_id, q, sort, order
        self.queue = Queue(maxsize=2)
        self.stop = Event()

    def _put(self, value):
        while not self.stop.is_set():
            try:
                self.queue.put(value, timeout=.05)
                return
            except Full:
                pass

    def _produce(self):
        path, tenant_id, q, sort, order = self.arguments
        try:
            with connect(path) as db:
                db.execute('PRAGMA query_only = ON')
                db.set_progress_handler(lambda: int(self.stop.is_set()), 1000)
                db.execute('BEGIN')
                query, parameters, ordering, zone, check_dates = certificate_query(db, tenant_id, q, sort, order)
                cursor = db.execute(query + ordering, parameters)
                try:
                    check_dates()
                    first = True
                    while not self.stop.is_set():
                        batch = cursor.fetchmany(1000)
                        output = StringIO(newline='')
                        writer = csv.writer(output, lineterminator='\r\n')
                        if first:
                            writer.writerow(FIELDS)
                        for row in batch:
                            item = project(row, zone)
                            writer.writerow([safe_text(item[field]) for field in FIELDS])
                        check_dates()
                        data = output.getvalue().encode('utf-8-sig' if first else 'utf-8')
                        if data:
                            self._put(data)
                        first = False
                        if not batch:
                            break
                finally:
                    cursor.close()
                    db.rollback()
            self._put(_DONE)
        except Exception as error:
            if not self.stop.is_set():
                self._put(error)

    async def _next(self):
        while True:
            try:
                return self.queue.get_nowait()
            except Empty:
                await anyio.sleep(.005)

    async def _stream(self, scope, receive, send):
        item = await self._next()
        if isinstance(item, Exception):
            status = item.status_code if isinstance(item, HTTPException) else 500
            detail = item.detail if isinstance(item, HTTPException) else 'CSV export unavailable'
            await JSONResponse({'detail': detail}, status_code=status)(scope, receive, send)
            return
        await send({'type': 'http.response.start', 'status': 200, 'headers': self.raw_headers})
        while item is not _DONE:
            if isinstance(item, Exception):
                # Headers already sent: fail the transfer, never append a JSON error to CSV.
                raise RuntimeError('CSV stream interrupted') from item
            await send({'type': 'http.response.body', 'body': item, 'more_body': True})
            item = await self._next()
        await send({'type': 'http.response.body', 'body': b'', 'more_body': False})

    async def __call__(self, scope, receive, send):
        worker = Thread(target=self._produce, name='certificate-csv', daemon=True)
        worker.start()
        try:
            async with anyio.create_task_group() as group:
                async def stream():
                    await self._stream(scope, receive, send)
                    group.cancel_scope.cancel()

                async def disconnect():
                    await self.listen_for_disconnect(receive)
                    group.cancel_scope.cancel()

                group.start_soon(stream)
                group.start_soon(disconnect)
        finally:
            self.stop.set()
            # The producer checks cancellation in queue waits and SQLite VM execution.
            # Shield cleanup from disconnect cancellation, without blocking the event loop.
            with anyio.CancelScope(shield=True):
                await anyio.to_thread.run_sync(worker.join)


def export_csv(database_path, tenant_id, q, sort, order):
    return CSVResponse(database_path, tenant_id, q, sort, order)
