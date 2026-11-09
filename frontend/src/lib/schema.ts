// Same rules and limits as the metaschemas in backend/plugins/meta.py (FIELD, SCHEMA, RULES).
// A flat JSON Schema: one property per question. Each property is an enum (choice), an array of an
// enum (multi), a boolean (yes/no), a number, a date, or an integer range of at most MAX_LEVELS (scale).
// `nullable: true` lets the answer be null when the email does not say. Nothing else is accepted.

export const MAX_FIELDS = 32; // questions per plugin
export const MAX_LEVELS = 10; // steps on a scale question (max - min + 1)
export const MAX_OPTIONS = 32; // answers per choice question
export const MAX_ANSWER_LENGTH = 100; // characters in a choice answer
export const MAX_DESCRIPTION = 500; // characters in a question, sent to the LLM with every email
export const MAX_RULES = 16; // rules per plugin
export const MAX_PATTERN = 512; // characters in a rule pattern
export const MAX_NAME_LENGTH = 64; // characters in a question key or rule name

type Base = { name: string; question: string; nullable?: boolean };
export type Field = Base &
  (
    | { kind: 'choice'; options: string[] }
    | { kind: 'multi'; options: string[] }
    | { kind: 'boolean' }
    | { kind: 'number' }
    | { kind: 'date' }
    | { kind: 'scale'; min: number; max: number }
  );

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

export const KEY = /^[a-z][a-z0-9_]*$/; // question keys and rule names
// Lengths in code points, as the backend counts them (an emoji is one, not two).
export const chars = (s: string) => [...s].length;

const shape = (f: Field) => {
  if (f.kind === 'boolean') return { type: 'boolean' };
  if (f.kind === 'number') return { type: 'number' };
  if (f.kind === 'date') return { type: 'string', format: 'date' };
  if (f.kind === 'scale') return { type: 'integer', minimum: f.min, maximum: f.max };
  const values = { type: 'string', enum: f.options.map((option) => option.trim()) };
  return f.kind === 'multi' ? { type: 'array', items: values } : values;
};

const prop = (f: Field) => ({ ...shape(f), description: f.question.trim() || undefined, ...(f.nullable ? { nullable: true } : {}) });

export const toSchema = (fields: Field[]) => ({
  type: 'object',
  properties: Object.fromEntries(fields.map((f) => [f.name, prop(f)])),
});

export function fieldProblems(f: Field, fields: Field[]): string[] {
  const out: string[] = [];
  if (!f.name) out.push(f.question.trim() ? 'Give it a saved-as key.' : 'Write the question.');
  else if (!KEY.test(f.name)) out.push('Key must start with a letter and use only a-z, 0-9 and _.');
  else if (f.name.length > MAX_NAME_LENGTH) out.push(`Key: at most ${MAX_NAME_LENGTH} characters.`);
  else if (f.name === 'rules') out.push('Key `rules` is reserved for rule matches.');
  else if (fields.some((g) => g !== f && g.name === f.name)) out.push('Key is already used by another question.');
  if (chars(f.question.trim()) > MAX_DESCRIPTION) out.push(`Question: at most ${MAX_DESCRIPTION} characters.`);
  if (f.kind === 'choice' || f.kind === 'multi') {
    const answers = new Set(f.options.map((option) => option.trim()));
    if (f.options.length < 2 || f.options.length > MAX_OPTIONS) out.push(`Use 2 to ${MAX_OPTIONS} answers.`);
    if (answers.has('')) out.push('Fill in or remove blank answers.');
    if (answers.size !== f.options.length) out.push('Answers must be unique.');
    if (f.options.some((o) => chars(o.trim()) > MAX_ANSWER_LENGTH)) out.push(`Answers: at most ${MAX_ANSWER_LENGTH} characters each.`);
  }
  if (f.kind === 'scale') {
    if (!Number.isInteger(f.min) || !Number.isInteger(f.max)) out.push('Min and max must be whole numbers.');
    else if (f.max < f.min) out.push('Max must be at least min.');
    else if (f.max - f.min + 1 > MAX_LEVELS) out.push(`At most ${MAX_LEVELS} levels.`);
  }
  return out;
}

export const toRules = (rules: Rule[]) => Object.fromEntries(rules.map((r) => [r.name, r.pattern]));
// The body the plugin endpoints take.
export const toBody = ({ fields, rules, ...rest }: Draft) => JSON.stringify({ ...rest, schema: toSchema(fields), rules: toRules(rules) });
export const fromRules = (rules: unknown): Rule[] =>
  Object.entries((rules as Record<string, string> | null) ?? {}).map(([name, pattern]) => ({ name, pattern }));

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
  if (chars(desc) > 1024) out.push('Description: at most 1024 characters.');
  return out;
}

const isObject = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);

// One property as a field, or why it is not a supported question. Same cases, in the same order, as _problem.
function toField(name: string, prop: unknown): Field | string {
  if (!isObject(prop)) return 'must be an object';
  const { description: question = '', enum: values, type, minimum: min, maximum: max, items, format, nullable = false } = prop;
  if (typeof question !== 'string') return 'description must be a string';
  if (typeof nullable !== 'boolean') return 'nullable must be true or false';
  const base = { name, question, ...(nullable ? { nullable } : {}) };
  if (Array.isArray(values) && values.length && values.every((v) => typeof v === 'boolean')) {
    if (values.length !== 2 || new Set(values).size !== 2) return 'a true/false enum must be [true, false]';
    return (type ?? 'boolean') === 'boolean' ? { kind: 'boolean', ...base } : 'type must be boolean for a true/false enum';
  }
  const options = (vs: unknown[]) => (vs.every((v) => typeof v === 'string') ? (vs as string[]) : 'enum values must be strings');
  if (Array.isArray(values)) {
    if ((type ?? 'string') !== 'string') return 'type must be string for an enum of answers';
    const o = options(values);
    return typeof o === 'string' ? o : { kind: 'choice', ...base, options: o };
  }
  if (type === 'array' && isObject(items) && Array.isArray(items.enum)) {
    if ((items.type ?? 'string') !== 'string') return 'items type must be string';
    const o = options(items.enum);
    return typeof o === 'string' ? o : { kind: 'multi', ...base, options: o };
  }
  if (type === 'boolean') return { kind: 'boolean', ...base };
  if (type === 'number') return { kind: 'number', ...base };
  if (type === 'string' && format === 'date') return { kind: 'date', ...base };
  if (type === 'integer' && Number.isInteger(min) && Number.isInteger(max)) return { kind: 'scale', ...base, min: min as number, max: max as number };
  return 'must be an enum, an array of an enum, a boolean, a number, a date or an integer with minimum and maximum';
}

// Reads a saved schema back into fields. Shapes the builder cannot express come back as an error,
// so saving never silently drops a property. Answer counts, blanks and levels are left to fieldProblems.
export function fromSchema(schema: unknown): { fields: Field[] } | { error: string } {
  const properties = isObject(schema) ? (schema.properties ?? {}) : {};
  if (!isObject(properties)) return { error: 'Schema has no properties object.' };
  const fields: Field[] = [];
  for (const [name, prop] of Object.entries(properties)) {
    const field = toField(name, prop);
    if (typeof field === 'string') return { error: `"${name}" ${field}. Recreate the plugin to change it.` };
    fields.push(field);
  }
  return { fields };
}
