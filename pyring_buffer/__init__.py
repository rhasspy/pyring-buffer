"""Implementation of a ring buffer using bytearray."""
from typing import Union


class RingBuffer:
    """Basic ring buffer using a bytearray.

    Not threadsafe.
    """

    def __init__(self, maxlen: int) -> None:
        """Initialize empty buffer."""
        self._buffer = bytearray(maxlen)
        self._pos = 0
        self._length = 0
        self._maxlen = maxlen

    @property
    def maxlen(self) -> int:
        """Return the maximum size of the buffer."""
        return self._maxlen

    @property
    def pos(self) -> int:
        """Return the current put position."""
        return self._pos

    def __len__(self) -> int:
        """Return the length of data stored in the buffer."""
        return self._length

    def clear(self) -> None:
        """Logically clear the buffer (does not overwrite underlying bytes)."""
        self._pos = 0
        self._length = 0

    def put(self, data: Union[bytes, bytearray, memoryview]) -> None:
        """Put a chunk of data into the buffer, possibly wrapping around."""
        mv = data if isinstance(data, memoryview) else memoryview(data)
        if mv.ndim != 1:
            mv = mv.cast("B")
        data_len = mv.nbytes
        if data_len == 0:
            return

        buf = self._buffer
        maxlen = self._maxlen
        pos = self._pos
        length = self._length

        # If incoming data is larger than the buffer:
        # - keep only the last maxlen bytes
        # - advance pos by data_len % maxlen
        if data_len >= maxlen:
            tail = mv[data_len - maxlen :]  # last maxlen bytes
            pos = data_len % maxlen  # next write position

            if pos == 0:
                buf[:] = tail
            else:
                # Write tail so that chronological order is preserved when reading
                # from pos (oldest) to end then start to pos.
                n1 = maxlen - pos
                buf[pos:] = tail[:n1]
                buf[:pos] = tail[n1:]

            self._pos = pos
            self._length = maxlen
            return

        end = pos + data_len
        if end <= maxlen:
            buf[pos:end] = mv
            pos = end
            if pos == maxlen:
                pos = 0
        else:
            n1 = maxlen - pos
            buf[pos:maxlen] = mv[:n1]
            n2 = data_len - n1
            buf[0:n2] = mv[n1:]
            pos = n2

        self._pos = pos
        new_len = length + data_len
        self._length = maxlen if new_len >= maxlen else new_len

    def getvalue(self) -> bytes:
        """Return the bytes in chronological order (oldest -> newest)."""
        length = self._length
        if length == 0:
            return b""

        buf = self._buffer
        maxlen = self._maxlen

        # If not full, the valid data is just the prefix [0:length].
        if length < maxlen:
            return bytes(buf[:length])

        # Full: oldest data starts at _pos.
        pos = self._pos
        if pos == 0:
            return bytes(buf)  # already in order

        return bytes(buf[pos:] + buf[:pos])
