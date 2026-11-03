import type { Field } from './schema';

export const KINDS = [
  { kind: 'choice', label: 'Choice', icon: '◉', note: 'Pick one answer from a list' },
  { kind: 'boolean', label: 'Yes / No', icon: '◐', note: 'A true or false answer' },
  { kind: 'scale', label: 'Scale', icon: '▮', note: 'A whole number in a range' },
] as const;

export const blank = (kind: Field['kind'], name = '', question = ''): Field =>
  kind === 'choice'
    ? { kind, name, question, options: [] }
    : kind === 'scale'
      ? { kind, name, question, min: 1, max: 5 }
      : { kind, name, question };

export const OPTION_SETS: Record<string, string[]> = {
  'Priority': ['low', 'medium', 'high'],
  'Sentiment': ['positive', 'neutral', 'negative'],
  'Yes / no / unsure': ['yes', 'no', 'unsure'],
  'Category': ['work', 'personal', 'finance', 'shopping', 'travel', 'social', 'other'],
  'Department': ['billing', 'support', 'sales', 'other'],
  'Next action': ['reply', 'read_later', 'archive', 'delete'],
  'Application status': ['applied', 'interview', 'offer', 'rejected', 'other'],
  'Order status': ['ordered', 'shipped', 'out_for_delivery', 'delivered', 'cancelled'],
};

export const SCALES: [string, number, number][] = [
  ['1 – 5 (rating)', 1, 5],
  ['0 – 4 (none → max)', 0, 4],
  ['1 – 10 (fine)', 1, 10],
  ['0 – 2 (low · mid · high)', 0, 2],
  ['1 – 3 (small)', 1, 3],
];

export const FIELD_PRESETS: Field[] = [
  { kind: 'boolean', name: 'receipt', question: 'Is this email a receipt or invoice?' },
  { kind: 'boolean', name: 'needs_reply', question: 'Does this email need a reply from me?' },
  { kind: 'boolean', name: 'newsletter', question: 'Is this a newsletter or marketing email?' },
  { kind: 'boolean', name: 'has_deadline', question: 'Does this email mention a deadline?' },
  { kind: 'scale', name: 'urgency', question: 'How urgent is this email? 0 is not at all, 4 is drop everything.', min: 0, max: 4 },
  { kind: 'scale', name: 'importance', question: 'How important is this email to me, from 1 to 5?', min: 1, max: 5 },
  { kind: 'choice', name: 'sentiment', question: "What is the sender's tone?", options: OPTION_SETS['Sentiment'] },
  { kind: 'choice', name: 'category', question: 'What is this email about?', options: OPTION_SETS['Category'] },
  { kind: 'choice', name: 'priority', question: 'What priority should this email get?', options: OPTION_SETS['Priority'] },
  { kind: 'choice', name: 'next_action', question: 'What should I do with this email?', options: OPTION_SETS['Next action'] },
];

export interface Template {
  title: string;
  blurb: string;
  name: string;
  desc: string;
  hint: string;
  fields: Field[];
}

export const TEMPLATES: Template[] = [
  {
    title: 'Blank',
    blurb: 'Start from nothing and add your own questions.',
    name: '',
    desc: '',
    hint: '',
    fields: [],
  },
  {
    title: 'Receipt tracker',
    blurb: 'Spot purchases and sort spending.',
    name: 'receipts',
    desc: 'Finds receipts and invoices and sorts them by spend category.',
    hint: 'Order confirmations, invoices and payment receipts from shops and services.',
    fields: [
      { kind: 'boolean', name: 'receipt', question: 'Is this email a receipt or invoice?' },
      { kind: 'choice', name: 'spend_category', question: 'What was bought?', options: ['groceries', 'food', 'travel', 'software', 'shopping', 'bills', 'other'] },
      { kind: 'boolean', name: 'subscription', question: 'Is this a recurring subscription charge?' },
    ],
  },
  {
    title: 'Support triage',
    blurb: 'Route customer mail to the right team.',
    name: 'support-triage',
    desc: 'Routes incoming support mail by team, urgency and mood.',
    hint: 'Customer emails to a support inbox about accounts, payments and bugs.',
    fields: [
      { kind: 'choice', name: 'department', question: 'Which team should handle this email?', options: OPTION_SETS['Department'] },
      { kind: 'scale', name: 'urgency', question: 'How urgent is this? 0 is not at all, 4 is an outage.', min: 0, max: 4 },
      { kind: 'choice', name: 'sentiment', question: "What is the customer's tone?", options: OPTION_SETS['Sentiment'] },
      { kind: 'boolean', name: 'refund_request', question: 'Is the customer asking for a refund?' },
    ],
  },
  {
    title: 'Job hunt',
    blurb: 'Follow applications from apply to offer.',
    name: 'job-hunt',
    desc: 'Tracks where each job application stands.',
    hint: 'Emails from recruiters, hiring platforms and company HR teams.',
    fields: [
      { kind: 'boolean', name: 'job_related', question: 'Is this email about a job application?' },
      { kind: 'choice', name: 'status', question: 'What stage is the application at?', options: OPTION_SETS['Application status'] },
      { kind: 'boolean', name: 'interview_invite', question: 'Does this email invite me to an interview?' },
    ],
  },
  {
    title: 'Inbox zero',
    blurb: 'Decide what needs you and what can wait.',
    name: 'inbox-zero',
    desc: 'Scores each email so the important ones surface first.',
    hint: 'A busy personal inbox with work mail, newsletters and notifications.',
    fields: [
      { kind: 'scale', name: 'importance', question: 'How important is this email to me, from 1 to 5?', min: 1, max: 5 },
      { kind: 'boolean', name: 'needs_reply', question: 'Does this email need a reply from me?' },
      { kind: 'choice', name: 'next_action', question: 'What should I do with this email?', options: OPTION_SETS['Next action'] },
    ],
  },
];

// Fields are edited in place, so every insert gets its own copy.
export const clone = <T>(value: T): T => structuredClone(value);

// Changes a field's kind in place so the card keeps its identity (and focus) across the switch.
export function retype(f: Field, kind: Field['kind']) {
  const next = blank(kind, f.name, f.question);
  const target = f as Record<string, unknown>;
  for (const key of Object.keys(target)) delete target[key];
  Object.assign(target, next);
}
