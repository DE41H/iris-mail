// Laya reads a flat JSON Schema: one property per question. Each property is an enum (choice),
// a boolean (yes/no), or an integer range of at most MAX_LEVELS (scale). Nothing else is accepted.

export const MAX_FIELDS = 32;
export const MAX_LEVELS = 10;

export type Field =
  | { kind: 'choice'; name: string; question: string; options: string[] }
  | { kind: 'boolean'; name: string; question: string }
  | { kind: 'scale'; name: string; question: string; min: number; max: number };

const prop = (f: Field) => {
  const description = f.question.trim() || undefined;
  if (f.kind === 'boolean') return { type: 'boolean', description };
  if (f.kind === 'scale') return { type: 'integer', minimum: f.min, maximum: f.max, description };
  return { type: 'string', enum: f.options, description };
};

export const toSchema = (fields: Field[]) => ({
  type: 'object',
  properties: Object.fromEntries(fields.map((f) => [f.name, prop(f)])),
});

export function problems(fields: Field[]): string[] {
  const out: string[] = [];
  if (!fields.length) out.push('Add at least one field.');
  if (fields.length > MAX_FIELDS) out.push(`Use at most ${MAX_FIELDS} fields.`);
  const names = new Set<string>();
  fields.forEach((f, i) => {
    const at = f.name ? `"${f.name}"` : `Field ${i + 1}`;
    if (!/^[a-z][a-z0-9_]*$/.test(f.name)) out.push(`${at}: name must start with a letter and use only a-z, 0-9 and _.`);
    if (names.has(f.name)) out.push(`${at}: name is already used.`);
    names.add(f.name);
    if (f.kind === 'choice') {
      if (f.options.length < 2) out.push(`${at}: add at least two options.`);
      if (f.options.length > 32) out.push(`${at}: at most 32 options.`);
      if (f.options.some((option) => !option.trim())) out.push(`${at}: fill in or remove blank answers.`);
      if (new Set(f.options.map((option) => option.trim())).size !== f.options.length) out.push(`${at}: answers must be unique.`);
    }
    if (f.kind === 'scale') {
      if (!Number.isInteger(f.min) || !Number.isInteger(f.max)) out.push(`${at}: min and max must be whole numbers.`);
      else if (f.max < f.min) out.push(`${at}: max must be at least min.`);
      else if (f.max - f.min + 1 > MAX_LEVELS) out.push(`${at}: at most ${MAX_LEVELS} levels.`);
    }
  });
  return out;
}

// Reads a saved schema back into fields. Shapes the builder cannot express come back as an error,
// so saving never silently drops a property.
export function fromSchema(schema: unknown): { fields: Field[] } | { error: string } {
  const properties = (schema as { properties?: unknown } | null)?.properties ?? {};
  if (typeof properties !== 'object' || Array.isArray(properties)) return { error: 'Schema has no properties object.' };
  const fields: Field[] = [];
  for (const [name, raw] of Object.entries(properties)) {
    const p = raw as { type?: unknown; enum?: unknown; description?: string; minimum?: unknown; maximum?: unknown };
    const question = typeof p.description === 'string' ? p.description : '';
    const values = p.enum;
    if (Array.isArray(values) && values.length === 2 && values.includes(true) && values.includes(false)) {
      fields.push({ kind: 'boolean', name, question });
    } else if (Array.isArray(values) && values.every((v) => typeof v === 'string')) {
      fields.push({ kind: 'choice', name, question, options: values });
    } else if (p.type === 'boolean') {
      fields.push({ kind: 'boolean', name, question });
    } else if (p.type === 'integer' && Number.isInteger(p.minimum) && Number.isInteger(p.maximum)) {
      fields.push({ kind: 'scale', name, question, min: p.minimum as number, max: p.maximum as number });
    } else {
      return { error: `"${name}" uses a shape this builder cannot edit. Recreate the plugin to change it.` };
    }
  }
  return { fields };
}
