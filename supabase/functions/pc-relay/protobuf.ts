// Minimal manual protobuf for the Pocket Casts wire format.
// Mirrors the canonical encoder in pocket-radio-menubar APIService.swift.
// Runs in Deno where binary (Uint8Array) is NUL-safe — the thing Roku can't do.
//
// Wire types: 0 = varint, 2 = length-delimited. All field numbers <= 15
// (single-byte tags). We only ever emit/parse those two wire types; unknown
// wire types (1/5) are skipped on decode.

const enc = new TextEncoder();
const dec = new TextDecoder();

// ---- encode ----------------------------------------------------------------

export function encodeVarint(value: number): Uint8Array {
  // Arithmetic (not bitwise) so values > 2^31 (e.g. ms timestamps) are safe.
  const out: number[] = [];
  let v = value;
  if (v < 0) throw new Error("varint must be non-negative");
  do {
    let byte = v % 128;
    v = Math.floor(v / 128);
    if (v > 0) byte |= 0x80;
    out.push(byte);
  } while (v > 0);
  return new Uint8Array(out);
}

function tag(fieldNumber: number, wireType: number): Uint8Array {
  return new Uint8Array([(fieldNumber << 3) | wireType]);
}

export function concat(...parts: Uint8Array[]): Uint8Array {
  const len = parts.reduce((n, p) => n + p.length, 0);
  const out = new Uint8Array(len);
  let off = 0;
  for (const p of parts) {
    out.set(p, off);
    off += p.length;
  }
  return out;
}

export function stringField(fieldNumber: number, value: string): Uint8Array {
  const bytes = enc.encode(value);
  return concat(tag(fieldNumber, 2), encodeVarint(bytes.length), bytes);
}

export function varintField(fieldNumber: number, value: number): Uint8Array {
  return concat(tag(fieldNumber, 0), encodeVarint(value));
}

export function lenDelimField(fieldNumber: number, buf: Uint8Array): Uint8Array {
  return concat(tag(fieldNumber, 2), encodeVarint(buf.length), buf);
}

// Int32Value wrapper = sub-message { field 1 (varint) = int }.
export function int32Value(fieldNumber: number, value: number): Uint8Array {
  return lenDelimField(fieldNumber, varintField(1, value));
}

// ---- decode ----------------------------------------------------------------

export type Field = { wire: number; varint?: number; bytes?: Uint8Array };
export type Fields = Map<number, Field[]>;

function readVarint(buf: Uint8Array, pos: number): [number, number] {
  let result = 0;
  let shift = 1; // multiplier (2^(7*i)), arithmetic to stay > 32-bit safe
  let p = pos;
  while (p < buf.length) {
    const b = buf[p++];
    result += (b & 0x7f) * shift;
    if ((b & 0x80) === 0) break;
    shift *= 128;
  }
  return [result, p];
}

export function decode(buf: Uint8Array): Fields {
  const fields: Fields = new Map();
  let pos = 0;
  while (pos < buf.length) {
    const tagByte = buf[pos++];
    const fieldNumber = tagByte >> 3;
    const wire = tagByte & 0x07;
    let field: Field;
    if (wire === 0) {
      const [v, np] = readVarint(buf, pos);
      pos = np;
      field = { wire, varint: v };
    } else if (wire === 2) {
      const [len, np] = readVarint(buf, pos);
      const bytes = buf.subarray(np, np + len);
      pos = np + len;
      field = { wire, bytes };
    } else if (wire === 1) {
      pos += 8; // fixed64 — skip
      continue;
    } else if (wire === 5) {
      pos += 4; // fixed32 — skip
      continue;
    } else {
      break; // unknown wire type
    }
    const arr = fields.get(fieldNumber) ?? [];
    arr.push(field);
    fields.set(fieldNumber, arr);
  }
  return fields;
}

export function getString(fields: Fields, fn: number): string | undefined {
  const f = fields.get(fn)?.[0];
  return f?.bytes ? dec.decode(f.bytes) : undefined;
}

export function getVarint(fields: Fields, fn: number): number | undefined {
  return fields.get(fn)?.[0]?.varint;
}

export function getBytes(fields: Fields, fn: number): Uint8Array | undefined {
  return fields.get(fn)?.[0]?.bytes;
}

export function getRepeatedBytes(fields: Fields, fn: number): Uint8Array[] {
  return (fields.get(fn) ?? []).map((f) => f.bytes!).filter(Boolean);
}

// Unwrap Int32Value / Timestamp sub-message -> its field-1 varint.
export function unwrapInt(bytes: Uint8Array | undefined): number | undefined {
  if (!bytes) return undefined;
  return getVarint(decode(bytes), 1);
}
