"""Read a window of a (cloud-optimised) GeoTIFF over HTTP range requests or from disk.
Pure Python: rasterio/imagecodecs DLLs are blocked by Smart App Control."""
import io, zlib, urllib.request
import numpy as np
import tifffile


class RangeFile(io.RawIOBase):
    def __init__(self, url, block=1 << 16):
        self.url, self.pos, self.block, self.cache = url, 0, block, {}
        req = urllib.request.Request(url, method="HEAD")
        self.size = int(urllib.request.urlopen(req, timeout=60).headers["Content-Length"])

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else self.pos + off if whence == 1 else self.size + off
        return self.pos

    def _get(self, start, end):
        req = urllib.request.Request(self.url, headers={"Range": f"bytes={start}-{end - 1}"})
        return urllib.request.urlopen(req, timeout=120).read()

    def read(self, n=-1):
        if n < 0: n = self.size - self.pos
        end = min(self.pos + n, self.size)
        if end - self.pos > 4 * self.block:  # big read: fetch directly
            data = self._get(self.pos, end)
        else:
            b0, b1 = self.pos // self.block, (end - 1) // self.block
            for b in range(b0, b1 + 1):
                if b not in self.cache:
                    self.cache[b] = self._get(b * self.block, min((b + 1) * self.block, self.size))
            data = b"".join(self.cache[b] for b in range(b0, b1 + 1))
            data = data[self.pos - b0 * self.block: end - b0 * self.block]
        self.pos = end
        return data

    def readinto(self, b):
        d = self.read(len(b)); b[:len(d)] = d; return len(d)


def _undo_predictor(buf, pred, dtype, tw, th, spp=1):
    if pred == 1:
        return np.frombuffer(buf, dtype).reshape(th, tw)
    if pred == 2:
        a = np.frombuffer(buf, dtype).reshape(th, tw).copy()
        return np.cumsum(a, axis=1, dtype=a.dtype)
    if pred == 3:  # floating point: byte planes, most significant first, then differenced
        nb = np.dtype(dtype).itemsize
        a = np.frombuffer(buf, np.uint8).reshape(th, tw * nb)
        a = np.cumsum(a, axis=1, dtype=np.uint8).reshape(th, nb, tw)
        be = np.ascontiguousarray(a.transpose(0, 2, 1)).reshape(th, tw * nb)
        return be.view(np.dtype(dtype).newbyteorder(">")).astype(dtype).reshape(th, tw)
    raise ValueError(pred)


def read_window(src, r0, r1, c0, c1):
    """Rows [r0, r1), cols [c0, c1) of page 0. src: path or URL."""
    fh = RangeFile(src) if str(src).startswith("http") else open(src, "rb")
    with tifffile.TiffFile(fh) as tif:
        p = tif.pages[0]
        g = tif.geotiff_metadata
        dtype = p.dtype
        if not p.is_tiled:  # strips or plain: fall back to memmap-able read
            full = p.asarray()
            return full[r0:r1, c0:c1], g
        tw, th = p.tilewidth, p.tilelength
        ntx = -(-p.imagewidth // tw)
        out = np.zeros((r1 - r0, c1 - c0), dtype)
        for ty in range(r0 // th, (r1 - 1) // th + 1):
            for tx in range(c0 // tw, (c1 - 1) // tw + 1):
                i = ty * ntx + tx
                fh.seek(p.dataoffsets[i]); raw = fh.read(p.databytecounts[i])
                if p.compression == 8 or p.compression == 32946:
                    raw = zlib.decompress(raw)
                elif p.compression != 1:
                    raise ValueError(f"compression {p.compression}")
                tile = _undo_predictor(raw, p.predictor, dtype, tw, th)
                ya, yb = max(r0, ty * th), min(r1, (ty + 1) * th)
                xa, xb = max(c0, tx * tw), min(c1, (tx + 1) * tw)
                out[ya - r0:yb - r0, xa - c0:xb - c0] = tile[ya - ty * th:yb - ty * th, xa - tx * tw:xb - tx * tw]
        return out, g
