/**
 * Frontend mirror of the backend operation registry: labels, icons, routes and document-type-aware wording.
 * The backend remains the source of truth for analysis behaviour; this only drives presentation.
 */
export const OPERATIONS = [
  {
    key: 'COMPENSATION',
    label: 'Compensation & Benefits',
    icon: 'money',
    description: 'Payment amounts, fees and what is owed.',
    byType: {
      EMPLOYMENT: 'Salary, bonuses, allowances and benefits.',
      RENTAL: 'Rent, deposit, fees and payment obligations.',
      FREELANCE: 'Rates, invoices, payment schedule and expenses.',
      SAAS_TERMS: 'Subscription fees, renewal charges and payment conditions.',
      VENDOR: 'Pricing, payment terms, penalties and credits.',
      INTERNSHIP: 'Stipend, allowances and reimbursements.',
      FOUNDER: 'Capital, vesting and founder compensation.',
      PARTNERSHIP: 'Contributions, profit share and drawings.',
      SERVICE: 'Fees, milestones and payment conditions.',
    },
  },
  {
    key: 'NOTICE_EXIT',
    label: 'Notice & Exit Terms',
    icon: 'exit',
    description: 'How the agreement ends, and what notice is required.',
    byType: {
      EMPLOYMENT: 'Notice, resignation, termination and exit conditions.',
      RENTAL: 'Lock-in, vacating notice, deposit refund and early termination.',
      SAAS_TERMS: 'Cancellation, auto-renewal, suspension and data export.',
      FREELANCE: 'How the engagement ends and what notice is due.',
      NDA: 'How long the duty lasts and when it ends.',
      VENDOR: 'Termination, notice and wind-down obligations.',
    },
  },
  {
    key: 'RESTRICTIONS',
    label: 'Restrictions',
    icon: 'lock',
    description: 'Limits on what you can do, use or share.',
    byType: {
      EMPLOYMENT: 'Non-compete, confidentiality, bonds and other limits.',
      RENTAL: 'Subletting, alterations, use and pet restrictions.',
      NDA: 'Disclosure limits, permitted use and exceptions.',
      FREELANCE: 'Exclusivity, confidentiality and client restrictions.',
      SAAS_TERMS: 'Acceptable use, sharing and licence limits.',
    },
  },
  {
    key: 'CONCERNS',
    label: 'Potential Concerns',
    icon: 'alert',
    description: 'Identify clauses, unusual terms or potential inconsistencies to review.',
  },
  {
    key: 'OBLIGATIONS',
    label: 'Your Obligations',
    icon: 'listCheck',
    description: 'See what you are required to do under this agreement.',
  },
  {
    key: 'KEY_TERMS',
    label: 'Important Terms',
    icon: 'calendar',
    description: 'Extract dates, durations, amounts and key conditions.',
  },
  {
    key: 'DOCUMENT_QA',
    label: 'Ask About the Document',
    icon: 'message',
    description: 'Ask a question grounded in this document.',
  },
  {
    key: 'LAWYER_PREP',
    label: 'Prepare for a Lawyer',
    icon: 'scale',
    description: 'Prepare questions you may want to clarify with a legal professional.',
  },
];

export const ANALYSIS_OPERATION_KEYS = ['KEY_TERMS', 'COMPENSATION', 'NOTICE_EXIT', 'RESTRICTIONS', 'CONCERNS', 'OBLIGATIONS'];

export function getOperation(key) {
  return OPERATIONS.find((operation) => operation.key === key) ?? null;
}

export function operationDescription(operation, documentType) {
  return operation.byType?.[documentType] ?? operation.description;
}

export function operationPath(documentId, key) {
  if (key === 'DOCUMENT_QA') return `/documents/${documentId}/ask`;
  if (key === 'LAWYER_PREP') return `/documents/${documentId}/lawyer`;
  if (key === 'COMPARE') return `/documents/${documentId}/compare`;
  return `/documents/${documentId}/analyze/${key}`;
}

export const CATEGORY_LABELS = {
  notice_period: 'Notice Period',
  termination: 'Termination',
  resignation: 'Resignation',
  severance: 'Severance',
  post_exit: 'Post-exit obligations',
  renewal: 'Renewal & expiry',
  payment: 'Payment',
  bonus: 'Bonus & incentives',
  benefit: 'Benefits',
  deduction: 'Deductions',
  reimbursement: 'Reimbursements',
  equity: 'Equity',
  confidentiality: 'Confidentiality',
  non_compete: 'Non-compete',
  non_solicitation: 'Non-solicitation',
  exclusivity: 'Exclusivity',
  bond: 'Bond / repayment',
  ip: 'Intellectual property',
  use_restriction: 'Use restrictions',
  parties: 'Parties',
  dates: 'Dates',
  duration: 'Duration',
  amounts: 'Amounts',
  conditions: 'Conditions',
  during_term: 'During the agreement',
  on_exit: 'When leaving',
  compliance: 'Compliance',
  other: 'Other',
};

export function categoryLabel(category) {
  if (!category) return 'Other';
  return CATEGORY_LABELS[category] ?? category.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}
