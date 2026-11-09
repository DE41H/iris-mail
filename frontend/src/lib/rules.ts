// Rule checks, apart from schema.ts so only the editor loads re2js (the plugin list only reads schemas).
import { RE2JS } from 're2js';
import { chars, fieldProblems, KEY, MAX_FIELDS, MAX_NAME_LENGTH, MAX_PATTERN, MAX_RULES, type Field, type Rule } from './schema';

const MAX_MATCHES = 20; // matches kept per rule per email, as in meta.py
const MAX_MATCH_LENGTH = 200; // characters kept per match, as in meta.py

export function problems(fields: Field[], rules: Rule[]): string[] {
  const out: string[] = [];
  if (!fields.length && !rules.length) out.push('Add at least one question or rule.');
  if (fields.length > MAX_FIELDS) out.push(`Use at most ${MAX_FIELDS} questions.`);
  fields.forEach((f, i) => fieldProblems(f, fields).forEach((p) => out.push(`Question ${i + 1}: ${p}`)));
  if (rules.length > MAX_RULES) out.push(`Use at most ${MAX_RULES} rules.`);
  rules.forEach((r, i) => ruleProblems(r, rules).forEach((p) => out.push(`Rule ${i + 1}: ${p}`)));
  return out;
}

// The worker matches with RE2 (re2.compile in validation.py and extract.py); re2js is the same engine,
// so a pattern that compiles here compiles there.
// Every keystroke checks each rule several times, so compiled patterns are cached.
const compiled = new Map<string, RE2JS | string>();
function compile(pattern: string): RE2JS | string {
  let re = compiled.get(pattern);
  if (re === undefined) {
    try {
      re = RE2JS.compile(pattern);
    } catch (err) {
      re = (err as Error).message.replace(/^error parsing regexp: /, '');
    }
    if (compiled.size > 200) compiled.clear(); // typing makes a new pattern per key
    compiled.set(pattern, re);
  }
  return re;
}

export function ruleProblems(r: Rule, rules: Rule[]): string[] {
  const out: string[] = [];
  if (!KEY.test(r.name)) out.push('Name must start with a letter and use only a-z, 0-9 and _.');
  else if (r.name.length > MAX_NAME_LENGTH) out.push(`Name: at most ${MAX_NAME_LENGTH} characters.`);
  else if (rules.some((g) => g !== r && g.name === r.name)) out.push('Name is already used by another rule.');
  if (!r.pattern) out.push('Pattern is required.');
  else if (chars(r.pattern) > MAX_PATTERN) out.push(`Pattern: at most ${MAX_PATTERN} characters.`);
  else {
    const re = compile(r.pattern);
    if (typeof re === 'string') out.push(`Pattern: ${re}.`);
  }
  return out;
}

// Same as extract._match: at most MAX_MATCHES matches, each the first non-empty group (else the whole match),
// cut to MAX_MATCH_LENGTH. A pattern that does not compile gives null.
export function ruleMatches(pattern: string, text: string): string[] | null {
  const re = compile(pattern);
  if (typeof re === 'string') return null;
  const m = re.matcher(text);
  const out: string[] = [];
  while (out.length < MAX_MATCHES && m.find()) {
    const groups = Array.from({ length: m.groupCount() }, (_, i) => m.group(i + 1));
    out.push((groups.length ? (groups.find(Boolean) ?? groups[0] ?? '') : (m.group() ?? '')).slice(0, MAX_MATCH_LENGTH));
  }
  return out;
}
