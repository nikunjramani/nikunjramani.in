import { decode } from "blurhash";

// A small local base64 table rather than Buffer — this runs both server-side (the public
// project page) and client-side (the admin editor's live preview, which reuses the same
// ProjectDetailView component deliberately, per 5.7's "preview must use the real
// components"), and Buffer isn't available in the browser bundle without a polyfill Next
// doesn't add by default. btoa() exists in both runtimes but only accepts a binary string,
// not a byte array, so this still needs to build that string manually either way.
function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return typeof btoa === "function" ? btoa(binary) : Buffer.from(binary, "binary").toString("base64");
}

/**
 * Decodes a stored blurhash into a tiny BMP data URL for next/image's `blurDataURL`.
 * BMP needs no encoder dependency — an uncompressed 24-bit header plus the raw pixels
 * decode straight out of `blurhash`, and every browser renders it like any other image.
 * The payload is ~1KB at 32x32.
 */
export function blurhashToDataURL(hash: string, width = 32, height = 32): string {
  const pixels = decode(hash, width, height);

  const rowSize = Math.ceil((width * 3) / 4) * 4;
  const pixelArraySize = rowSize * height;
  const fileSize = 54 + pixelArraySize;

  const bytes = new Uint8Array(fileSize);
  const view = new DataView(bytes.buffer);
  bytes[0] = 0x42; // "B"
  bytes[1] = 0x4d; // "M"
  view.setUint32(2, fileSize, true);
  view.setUint32(10, 54, true);
  view.setUint32(14, 40, true);
  view.setInt32(18, width, true);
  view.setInt32(22, height, true);
  view.setUint16(26, 1, true);
  view.setUint16(28, 24, true);
  view.setUint32(30, 0, true);
  view.setUint32(34, pixelArraySize, true);

  for (let y = 0; y < height; y++) {
    // BMP rows are stored bottom-to-top and padded to 4-byte boundaries.
    const srcY = height - 1 - y;
    const rowOffset = 54 + y * rowSize;
    for (let x = 0; x < width; x++) {
      const srcIdx = (srcY * width + x) * 4;
      const dstIdx = rowOffset + x * 3;
      bytes[dstIdx] = pixels[srcIdx + 2] ?? 0;
      bytes[dstIdx + 1] = pixels[srcIdx + 1] ?? 0;
      bytes[dstIdx + 2] = pixels[srcIdx] ?? 0;
    }
  }

  return `data:image/bmp;base64,${bytesToBase64(bytes)}`;
}
