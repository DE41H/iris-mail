import { el } from './api';
import { type Field, MAX_FIELDS, problems, toSchema } from './schema';

const KINDS = [
  ['choice', 'Choice'],
  ['boolean', 'Yes / no'],
  ['scale', 'Scale'],
] as const;

let groups = 0;

const defaults = (kind: Field['kind'], name: string, question: string): Field =>
  kind === 'choice'
    ? { kind, name, question, options: [] }
    : kind === 'scale'
      ? { kind, name, question, min: 0, max: 4 }
      : { kind, name, question };

const text = (value: string, placeholder: string, mono = false) => {
  const input = document.createElement('input');
  if (mono) input.className = 'mono';
  input.type = 'text';
  input.value = value;
  input.placeholder = placeholder;
  input.spellcheck = false;
  input.autocomplete = 'off';
  return input;
};

// Mounts the field editor into `root`. Structural edits re-render the list; typing only updates
// the state, so the input keeps focus.
export function mountBuilder(root: HTMLElement, initial: Field[], onChange: () => void) {
  let fields = initial;
  const list = el('div', 'fields');
  const issues = el('ul', 'problems');
  issues.setAttribute('role', 'status');
  const preview = el('pre', 'preview mono');
  const previewHead = el('div', 'preview-head');
  previewHead.append(el('span', 'eyebrow', 'LIVE OUTPUT'), el('span', 'muted', 'JSON schema'));
  const previewPanel = el('section', 'schema-preview');
  previewPanel.append(previewHead, preview);
  const add = el('button', 'btn btn-sm', 'Add field');
  add.type = 'button';
  const builderHead = el('div', 'builder-head');
  const count = el('span', 'field-count');
  builderHead.append(el('div', '', 'Questions'), count);
  root.replaceChildren(builderHead, list, add, issues, previewPanel);

  const sync = () => {
    const found = problems(fields);
    issues.replaceChildren(...found.map((message) => el('li', '', message)));
    preview.textContent = JSON.stringify(toSchema(fields), null, 2);
    count.textContent = `${fields.length} / ${MAX_FIELDS} fields`;
    add.disabled = fields.length >= MAX_FIELDS;
    onChange();
  };

  const render = (focusLast = false) => {
    const group = ++groups;
    list.replaceChildren(
      ...(fields.length ? fields.map((f, i) => card(f, i, group)) : [el('div', 'empty', 'No fields yet. Each field is one question Laya answers per email.')]),
    );
    if (focusLast) list.lastElementChild?.querySelector('input')?.focus();
    sync();
  };

  const card = (f: Field, i: number, group: number) => {
    const node = el('div', 'field-card');
    node.style.setProperty('--field-index', String(i));
    const top = el('div', 'field-top');

    const name = text(f.name, 'field_name', true);
    name.className = 'mono field-name';
    name.setAttribute('aria-label', `Field ${i + 1} name`);
    name.addEventListener('input', () => { f.name = name.value; sync(); });

    const seg = el('div', 'seg');
    seg.setAttribute('role', 'radiogroup');
    seg.setAttribute('aria-label', `Field ${i + 1} type`);
    for (const [kind, label] of KINDS) {
      const wrap = el('label');
      const radio = document.createElement('input');
      radio.type = 'radio';
      radio.name = `kind-${group}-${i}`;
      radio.value = kind;
      radio.checked = f.kind === kind;
      radio.addEventListener('change', () => {
        fields[i] = defaults(kind, f.name, f.question);
        render();
      });
      wrap.append(radio, el('span', '', label));
      seg.append(wrap);
    }

    const remove = el('button', 'btn-link', 'Remove');
    remove.type = 'button';
    remove.setAttribute('aria-label', `Remove field ${i + 1}`);
    remove.addEventListener('click', () => { fields = fields.filter((_, j) => j !== i); render(); });

    top.append(el('span', 'field-index', String(i + 1).padStart(2, '0')), name, seg, remove);

    const question = text(f.question, 'Question for Laya, e.g. Is this a receipt?');
    question.className = 'field-question';
    question.setAttribute('aria-label', `Field ${i + 1} question`);
    question.addEventListener('input', () => { f.question = question.value; sync(); });
    node.append(top, question);

    if (f.kind === 'choice') {
      const optionBox = el('div', 'option-box');
      optionBox.append(el('div', 'option-title', 'Possible answers'));
      const optionList = el('div', 'option-list');
      f.options.forEach((option, optionIndex) => {
        const line = el('div', 'option-line');
        const input = text(option, `Option ${optionIndex + 1}`);
        input.setAttribute('aria-label', `Field ${i + 1} option ${optionIndex + 1}`);
        input.addEventListener('input', () => { f.options[optionIndex] = input.value.trim(); sync(); });
        const removeOption = el('button', 'option-remove', '×');
        removeOption.type = 'button';
        removeOption.setAttribute('aria-label', `Remove option ${optionIndex + 1}`);
        removeOption.addEventListener('click', () => { f.options.splice(optionIndex, 1); render(); });
        line.append(input, removeOption);
        optionList.append(line);
      });
      const addOption = el('button', 'btn btn-sm option-add', '+ Add answer');
      addOption.type = 'button';
      addOption.addEventListener('click', () => { f.options.push(''); render(); optionList.lastElementChild?.querySelector('input')?.focus(); });
      optionBox.append(optionList, addOption);
      node.append(optionBox);
    } else if (f.kind === 'scale') {
      const range = el('div', 'range');
      const from = document.createElement('input');
      const to = document.createElement('input');
      from.type = to.type = 'number';
      from.step = to.step = '1';
      from.value = String(f.min);
      to.value = String(f.max);
      from.setAttribute('aria-label', `Field ${i + 1} lowest value`);
      to.setAttribute('aria-label', `Field ${i + 1} highest value`);
      const num = (v: string) => (v === '' ? NaN : Number(v));
      from.addEventListener('input', () => { f.min = num(from.value); sync(); });
      to.addEventListener('input', () => { f.max = num(to.value); sync(); });
      range.append(el('span', 'muted', 'From'), from, el('span', 'muted', 'to'), to);
      node.append(range);
    } else {
      node.append(el('div', 'type-note', 'A clear yes or no for each email.'));
    }
    return node;
  };

  add.addEventListener('click', () => {
    if (fields.length >= MAX_FIELDS) return;
    fields = [...fields, defaults('choice', '', '')];
    render(true);
  });

  render();

  return {
    fields: () => fields,
    problems: () => problems(fields),
  };
}
