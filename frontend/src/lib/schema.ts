// Same rules as backend/plugins/validation.py, which also checks what Laya itself rejects.
// Laya reads a flat JSON Schema: one property per question. Each property is an enum (choice),
// a boolean (yes/no), or an integer range of at most MAX_LEVELS (scale). Nothing else is accepted.

export const MAX_FIELDS = 32;
export const MAX_LEVELS = 10;
export const MAX_OPTIONS = 32;
export const MAX_RULES = 16;
export const MAX_PATTERN = 512;

export type Field =
  | { kind: 'choice'; name: string; question: string; options: string[] }
  | { kind: 'boolean'; name: string; question: string }
  | { kind: 'scale'; name: string; question: string; min: number; max: number };

export interface Draft {
  name: string;
  desc: string;
  fields: Field[];
  rules: Rule[];
}

// Each rule stores every match as a list under output.rules[name], so `rules` is not a question key.
export interface Rule {
  name: string;
  pattern: string;
}


const prop = (f: Field) => {
  const description = f.question.trim() || undefined;
  if (f.kind === 'boolean') return { type: 'boolean', description };
  if (f.kind === 'scale') return { type: 'integer', minimum: f.min, maximum: f.max, description };
  return { type: 'string', enum: f.options.map((option) => option.trim()), description };
};

export const toSchema = (fields: Field[]) => ({
  type: 'object',
  properties: Object.fromEntries(fields.map((f) => [f.name, prop(f)])),
});

export function fieldProblems(f: Field, fields: Field[]): string[] {
  const out: string[] = [];
  if (!/^[a-z][a-z0-9_]*$/.test(f.name)) out.push('Key must start with a letter and use only a-z, 0-9 and _.');
  else if (f.name === 'rules') out.push('Key `rules` is reserved for rule matches.');
  else if (fields.some((g) => g !== f && g.name === f.name)) out.push('Key is already used by another question.');
  if (f.kind === 'choice') {
    if (f.options.length < 2) out.push('Add at least two answers.');
    if (f.options.length > MAX_OPTIONS) out.push(`At most ${MAX_OPTIONS} answers.`);
    if (f.options.some((option) => !option.trim())) out.push('Fill in or remove blank answers.');
    if (new Set(f.options.map((option) => option.trim())).size !== f.options.length) out.push('Answers must be unique.');
  }
  if (f.kind === 'scale') {
    if (!Number.isInteger(f.min) || !Number.isInteger(f.max)) out.push('Min and max must be whole numbers.');
    else if (f.max < f.min) out.push('Max must be at least min.');
    else if (f.max - f.min + 1 > MAX_LEVELS) out.push(`At most ${MAX_LEVELS} levels.`);
  }
  return out;
}

export function problems(fields: Field[], rules: Rule[]): string[] {
  const out: string[] = [];
  if (!fields.length && !rules.length) out.push('Add at least one question or rule.');
  if (fields.length > MAX_FIELDS) out.push(`Use at most ${MAX_FIELDS} questions.`);
  fields.forEach((f, i) => fieldProblems(f, fields).forEach((p) => out.push(`${f.name || `#${i + 1}`}: ${p}`)));
  if (rules.length > MAX_RULES) out.push(`Use at most ${MAX_RULES} rules.`);
  rules.forEach((r, i) => ruleProblems(r, rules).forEach((p) => out.push(`rule ${r.name || `#${i + 1}`}: ${p}`)));
  return out;
}

// Best effort: JS and Python regex syntax differ slightly, the server has the final say.
export function ruleProblems(r: Rule, rules: Rule[]): string[] {
  const out: string[] = [];
  if (!/^[a-z][a-z0-9_]*$/.test(r.name)) out.push('Name must start with a letter and use only a-z, 0-9 and _.');
  else if (rules.some((g) => g !== r && g.name === r.name)) out.push('Name is already used by another rule.');
  if (!r.pattern) out.push('Pattern is required.');
  else if (r.pattern.length > MAX_PATTERN) out.push(`Pattern: at most ${MAX_PATTERN} characters.`);
  else {
    try {
      new RegExp(r.pattern);
    } catch {
      out.push('Pattern does not compile.');
    }
  }
  return out;
}

export const toRules = (rules: Rule[]) => Object.fromEntries(rules.map((r) => [r.name, r.pattern]));
export const fromRules = (rules: unknown): Rule[] =>
  Object.entries((rules as Record<string, string> | null) ?? {}).map(([name, pattern]) => ({ name, pattern }));

// What Laya builds from each property (structured.py): choice, noul (yes/no) or score.
export const toQuestions = (fields: Field[]) =>
  Object.fromEntries(
    fields.map((f) => {
      const q = f.question.trim();
      if (f.kind === 'boolean') return [f.name, { type: 'noul', instructions: q || `Is \`${f.name}\` true?` }];
      if (f.kind === 'scale') {
        const criteria = Number.isInteger(f.min) && f.max >= f.min ? Array.from({ length: f.max - f.min + 1 }, (_, i) => String(f.min + i)) : [];
        return [f.name, { type: 'score', instructions: q || `Score \`${f.name}\` from ${f.min} to ${f.max}`, criteria }];
      }
      return [f.name, { type: 'choice', instructions: q || `What is \`${f.name}\`?`, criteria: Object.fromEntries(f.options.map((o) => [o.trim(), null])) }];
    }),
  );

const FILLER = new Set('a an the is are was this that it its does do did what which how who of for to in on from email mail message me my i you your there any be'.split(' '));

// Suggests a result key from the question: "Is this email a receipt?" -> "receipt".
export function slug(question: string) {
  const words = question.toLowerCase().replace(/['’]/g, '').split(/[^a-z0-9]+/).filter(Boolean);
  const kept = words.filter((w) => !FILLER.has(w));
  return (kept.length ? kept : words).slice(0, 4).join('_').replace(/^[^a-z]+/, '').slice(0, 40);
}

// Mirrors the Plugin model: a slug name of at most 255 characters and desc of 1024.
// Uniqueness per developer is only checked by the server.
export function pluginProblems(name: string, desc: string): string[] {
  const out: string[] = [];
  if (!name) out.push('Name is required.');
  else if (!/^[-a-z0-9_]+$/.test(name)) out.push('Name: use only lowercase letters, numbers, - and _.');
  else if (name.length > 255) out.push('Name: at most 255 characters.');
  if (desc.length > 1024) out.push('Description: at most 1024 characters.');
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
