import type { Field, Rule } from './schema';

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

export interface Template {
  title: string;
  blurb: string;
  name: string;
  desc: string;
  fields: Field[];
  rules: Rule[];
}

// Patterns are RE2 and JS compatible; the first capture group is what gets kept.
const MONEY = String.raw`((?:[$€£₹]|Rs\.?|INR|USD|EUR|GBP) ?\d[\d,]*(?:\.\d{2})?)`;

export const TEMPLATES: Template[] = [
  {
    title: 'Blank',
    blurb: 'Your own questions.',
    name: '',
    desc: '',
    fields: [],
    rules: [],
  },
  {
    title: 'Spending',
    blurb: 'Every receipt, sorted, with the amount.',
    name: 'spending',
    desc: 'Finds receipts, sorts them by category and pulls out what was paid.',
    fields: [
      { kind: 'boolean', name: 'receipt', question: 'Is this email a receipt or invoice for something I paid?' },
      { kind: 'choice', name: 'spend_category', question: 'What was the money spent on?', options: ['groceries', 'food', 'travel', 'software', 'shopping', 'bills', 'other'] },
      { kind: 'boolean', name: 'subscription', question: 'Is this a recurring subscription charge?' },
    ],
    rules: [{ name: 'amount', pattern: String.raw`(?:[Tt]otal|[Aa]mount|[Cc]harged)[^$€£₹\d]{0,20}` + MONEY }],
  },
  {
    title: 'Deliveries',
    blurb: 'Where each package is, and if it is late.',
    name: 'deliveries',
    desc: 'Follows shipping mail and keeps the tracking number.',
    fields: [
      { kind: 'choice', name: 'order_status', question: 'Is this about an order or delivery, and where is it now?', options: ['none', ...OPTION_SETS['Order status']] },
      { kind: 'boolean', name: 'delayed', question: 'Is the delivery late or rescheduled?' },
      { kind: 'boolean', name: 'action_needed', question: 'Do I need to do something, like sign, pay duty or pick it up?' },
    ],
    rules: [{ name: 'tracking_number', pattern: String.raw`[Tt]racking (?:number|no\.?|#|ID)?\s*:?\s*([A-Z0-9]{10,30})` }],
  },
  {
    title: 'Bills',
    blurb: 'What is owed, and by when.',
    name: 'bills',
    desc: 'Catches bills and statements with the amount and the due date.',
    fields: [
      { kind: 'choice', name: 'bill', question: 'Is this a bill asking me to pay, and for what?', options: ['none', 'rent', 'utilities', 'phone_internet', 'credit_card', 'insurance', 'tax', 'other'] },
      { kind: 'boolean', name: 'overdue', question: 'Does it say the payment is overdue?' },
    ],
    rules: [
      { name: 'amount_due', pattern: String.raw`(?:[Aa]mount|[Bb]alance|[Tt]otal) due[^$€£₹\d]{0,10}` + MONEY },
      { name: 'due_date', pattern: String.raw`[Dd]ue (?:on|by|date:?)\s*([A-Z][a-z]{2,8} \d{1,2}|\d{1,2} [A-Z][a-z]{2,8}|\d{1,2}/\d{1,2}(?:/\d{2,4})?)` },
    ],
  },
  {
    title: 'Travel',
    blurb: 'Bookings, changes and their codes.',
    name: 'travel',
    desc: 'Spots bookings and schedule changes and keeps the booking reference.',
    fields: [
      { kind: 'choice', name: 'booking_type', question: 'Is this a travel booking, and for what?', options: ['none', 'flight', 'train', 'bus', 'hotel', 'car_rental', 'other'] },
      { kind: 'choice', name: 'change', question: 'Has anything changed about the trip?', options: ['none', 'delayed', 'rescheduled', 'cancelled'] },
    ],
    rules: [
      { name: 'booking_ref', pattern: String.raw`(?:[Cc]onfirmation|[Bb]ooking|PNR)(?: code| number| ref\w*| #| no\.?)?\s*:?\s*(\d{10}|[A-Z0-9]{6})\b` },
      { name: 'flight', pattern: String.raw`[Ff]light:? ((?:[A-Z][A-Z0-9]|\d[A-Z]) ?\d{2,4})\b` },
    ],
  },
  {
    title: 'Meetings',
    blurb: 'Invites, how to join and if you must reply.',
    name: 'meetings',
    desc: 'Finds meeting invites, how to join and whether a reply is needed.',
    fields: [
      { kind: 'boolean', name: 'invite', question: 'Is someone asking me to meet or join a call?' },
      { kind: 'choice', name: 'format', question: 'How will the meeting happen?', options: ['in_person', 'video', 'phone', 'unclear'] },
      { kind: 'boolean', name: 'rsvp_needed', question: 'Do they want me to confirm or reply?' },
    ],
    rules: [{ name: 'join_link', pattern: String.raw`(https://(?:[\w-]+\.)*(?:zoom\.us|meet\.google\.com|teams\.microsoft\.com|webex\.com)/\S+)` }],
  },
  {
    title: 'Security alerts',
    blurb: 'Sign-ins and resets, ranked by risk.',
    name: 'security-alerts',
    desc: 'Flags account security mail and scores how much it needs attention.',
    fields: [
      { kind: 'choice', name: 'alert', question: 'What kind of security email is this?', options: ['none', 'new_sign_in', 'password_change', 'verification_code', 'suspicious_activity'] },
      { kind: 'scale', name: 'risk', question: 'How worried should I be? 0 is routine, 4 is act now.', min: 0, max: 4 },
    ],
    rules: [{ name: 'ip_address', pattern: String.raw`\b(\d{1,3}(?:\.\d{1,3}){3})\b` }],
  },
  {
    title: 'Job hunt',
    blurb: 'Follow applications from apply to offer.',
    name: 'job-hunt',
    desc: 'Tracks where each job application stands.',
    fields: [
      { kind: 'boolean', name: 'job_related', question: 'Is this email about a job application of mine?' },
      { kind: 'choice', name: 'status', question: 'What stage is the application at?', options: OPTION_SETS['Application status'] },
      { kind: 'boolean', name: 'interview_invite', question: 'Does this email invite me to an interview?' },
    ],
    rules: [{ name: 'scheduling_link', pattern: String.raw`(https://(?:calendly\.com|cal\.com)/\S+)` }],
  },
  {
    title: 'Newsletters',
    blurb: 'Keep the good ones, find the way out.',
    name: 'newsletters',
    desc: 'Rates newsletters and keeps the unsubscribe link.',
    fields: [
      { kind: 'boolean', name: 'newsletter', question: 'Is this a newsletter or marketing email?' },
      { kind: 'choice', name: 'topic', question: 'What is it mostly about?', options: ['news', 'tech', 'finance', 'deals', 'lifestyle', 'other'] },
      { kind: 'scale', name: 'worth_reading', question: 'How worth reading is it, from 1 to 5?', min: 1, max: 5 },
    ],
    rules: [{ name: 'unsubscribe', pattern: String.raw`(https?://\S*unsubscribe\S*)` }],
  },
  {
    title: 'Appointments',
    blurb: 'Bookings and reminders, with the time.',
    name: 'appointments',
    desc: 'Catches appointment bookings, reminders and changes, and keeps the time.',
    fields: [
      { kind: 'choice', name: 'appointment', question: 'Is this about an appointment, and what kind?', options: ['none', 'health', 'personal_care', 'home_service', 'vehicle', 'government', 'other'] },
      { kind: 'choice', name: 'status', question: 'What does it say about the appointment?', options: ['booked', 'reminder', 'rescheduled', 'cancelled'] },
      { kind: 'boolean', name: 'action_needed', question: 'Do I need to confirm, pay, fill a form or bring something?' },
    ],
    rules: [{ name: 'time', pattern: String.raw`\b(\d{1,2}(?::\d{2})? ?[AaPp]\.?[Mm]\b\.?)` }],
  },
  {
    title: 'Support triage',
    blurb: 'Route customer mail to the right team.',
    name: 'support-triage',
    desc: 'Sorts a support inbox by team, urgency and mood, and keeps the order number.',
    fields: [
      { kind: 'choice', name: 'team', question: 'Which team should handle this email?', options: ['billing', 'technical', 'account', 'sales', 'feedback', 'other'] },
      { kind: 'scale', name: 'urgency', question: 'How urgent is this? 0 is not at all, 4 is something is down.', min: 0, max: 4 },
      { kind: 'choice', name: 'sentiment', question: "What is the customer's tone?", options: OPTION_SETS['Sentiment'] },
      { kind: 'boolean', name: 'refund_request', question: 'Is the customer asking for a refund?' },
    ],
    rules: [{ name: 'order_number', pattern: String.raw`[Oo]rder ?(?:#|[Nn]o\.?|[Nn]umber|ID)\s*:?\s*([A-Z0-9][A-Z0-9-]{3,})` }],
  },
  {
    title: 'Inbox priority',
    blurb: 'Decide what needs you and what can wait.',
    name: 'inbox-priority',
    desc: 'Scores each email so the important ones surface first.',
    fields: [
      { kind: 'scale', name: 'importance', question: 'How important is this email to me, from 1 to 5?', min: 1, max: 5 },
      { kind: 'boolean', name: 'needs_reply', question: 'Does this email need a reply from me?' },
      { kind: 'boolean', name: 'has_deadline', question: 'Does this email mention a deadline?' },
      { kind: 'choice', name: 'next_action', question: 'What should I do with this email?', options: OPTION_SETS['Next action'] },
    ],
    rules: [],
  },
];

// Changes a field's kind in place so the card keeps its identity (and focus) across the switch.
export function retype(f: Field, kind: Field['kind']) {
  const next = blank(kind, f.name, f.question);
  const target = f as Record<string, unknown>;
  for (const key of Object.keys(target)) delete target[key];
  Object.assign(target, next);
}
