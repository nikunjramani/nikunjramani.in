import "server-only";

import { decode } from "blurhash";

/**
 * Decodes a stored blurhash into a tiny BMP data URL for next/image's `blurDataURL`.
 * BMP needs no encoder dependency — an uncompressed 24-bit header plus the raw pixels
 * decode straight out of `blurhash`, and every browser renders it like any other image.
 * Runs at request time on the server; the payload is ~1KB at 32x32, cached by the page
 * alongside everything else `unstable_cache` already covers.
 */
export function blurhashToDataURL(hash: string, width = 32, height = 32): string {
  const pixels = decode(hash, width, height);

  const rowSize = Math.ceil((width * 3) / 4) * 4;
  const pixelArraySize = rowSize * height;
  const fileSize = 54 + pixelArraySize;

  const buffer = Buffer.alloc(fileSize);
  buffer.write("BM", 0);
  buffer.writeUInt32LE(fileSize, 2);
  buffer.writeUInt32LE(54, 10);
  buffer.writeUInt32LE(40, 14);
  buffer.writeInt32LE(width, 18);
  buffer.writeInt32LE(height, 22);
  buffer.writeUInt16LE(1, 26);
  buffer.writeUInt16LE(24, 28);
  buffer.writeUInt32LE(0, 30);
  buffer.writeUInt32LE(pixelArraySize, 34);

  for (let y = 0; y < height; y++) {
    // BMP rows are stored bottom-to-top and padded to 4-byte boundaries.
    const srcY = height - 1 - y;
    const rowOffset = 54 + y * rowSize;
    for (let x = 0; x < width; x++) {
      const srcIdx = (srcY * width + x) * 4;
      const dstIdx = rowOffset + x * 3;
      buffer[dstIdx] = pixels[srcIdx + 2] ?? 0;
      buffer[dstIdx + 1] = pixels[srcIdx + 1] ?? 0;
      buffer[dstIdx + 2] = pixels[srcIdx] ?? 0;
    }
  }

  return `data:image/bmp;base64,${buffer.toString("base64")}`;
}
