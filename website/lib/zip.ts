type ZipEntry = {
  path: string;
  data: string | Uint8Array;
};

const MAX_ENTRY_NAME_BYTES = 512;

function crc32(data: Uint8Array): number {
  let value = 0xffffffff;
  for (let index = 0; index < data.length; index += 1) {
    const byte = data[index];
    value ^= byte;
    for (let bit = 0; bit < 8; bit += 1) value = (value >>> 1) ^ (value & 1 ? 0xedb88320 : 0);
  }
  return (value ^ 0xffffffff) >>> 0;
}

function writeU16(value: number): Uint8Array {
  const bytes = new Uint8Array(2);
  new DataView(bytes.buffer).setUint16(0, value, true);
  return bytes;
}

function writeU32(value: number): Uint8Array {
  const bytes = new Uint8Array(4);
  new DataView(bytes.buffer).setUint32(0, value >>> 0, true);
  return bytes;
}

function join(chunks: Uint8Array[]): Uint8Array {
  const total = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const output = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) {
    output.set(chunk, offset);
    offset += chunk.length;
  }
  return output;
}

function validatePath(path: string): void {
  if (!path || path.length > MAX_ENTRY_NAME_BYTES || path.startsWith('/') || path.includes('..') || path.includes('\\')) {
    throw new Error('Archive paths must be relative and cannot contain traversal.');
  }
}

/**
 * Produces a standards-compliant, uncompressed ZIP archive. Keeping exports
 * uncompressed makes memory use and archive contents predictable on a
 * serverless function; the caller owns the total-size limit.
 */
export function createStoredZip(entries: ZipEntry[]): Uint8Array {
  const encoder = new TextEncoder();
  const records: Array<{ name: Uint8Array; data: Uint8Array; crc: number; offset: number }> = [];
  const localParts: Uint8Array[] = [];
  let offset = 0;

  for (const entry of entries) {
    validatePath(entry.path);
    const name = encoder.encode(entry.path);
    const data = typeof entry.data === 'string' ? encoder.encode(entry.data) : entry.data;
    const crc = crc32(data);
    const header = join([
      writeU32(0x04034b50), writeU16(20), writeU16(0x0800), writeU16(0),
      writeU16(0), writeU16(0), writeU32(crc), writeU32(data.length), writeU32(data.length),
      writeU16(name.length), writeU16(0), name,
    ]);
    localParts.push(header, data);
    records.push({ name, data, crc, offset });
    offset += header.length + data.length;
  }

  const centralOffset = offset;
  const centralParts: Uint8Array[] = [];
  for (const record of records) {
    const header = join([
      writeU32(0x02014b50), writeU16(0x0314), writeU16(20), writeU16(0x0800), writeU16(0),
      writeU16(0), writeU16(0), writeU32(record.crc), writeU32(record.data.length), writeU32(record.data.length),
      writeU16(record.name.length), writeU16(0), writeU16(0), writeU16(0), writeU16(0), writeU32(0), writeU32(record.offset), record.name,
    ]);
    centralParts.push(header);
    offset += header.length;
  }

  const centralSize = offset - centralOffset;
  const end = join([
    writeU32(0x06054b50), writeU16(0), writeU16(0), writeU16(records.length), writeU16(records.length),
    writeU32(centralSize), writeU32(centralOffset), writeU16(0),
  ]);
  return join([...localParts, ...centralParts, end]);
}
