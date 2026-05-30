export const SUPPORTED_EXAMS = ["CA_FOUNDATION","CA_INTERMEDIATE","CA_FINAL","JEE","NEET"] as const;
export const SUPPORTED_LANGUAGES = ["English","Bengali","Hindi","Tamil","Telugu"] as const;
export const STUDENT_LEVELS = ["WEAK","AVERAGE","TOPPER"] as const;

export const EXAM_SUBJECTS: Record<string, string[]> = {
  CA_FOUNDATION: ["Principles and Practice of Accounting","Business Mathematics","Business Economics","Business and Commercial Knowledge"],
  CA_INTERMEDIATE: ["Advanced Accounting","Corporate Laws","Cost and Management Accounting","Taxation","Auditing and Code of Ethics","Financial Management"],
  CA_FINAL: ["Financial Reporting","Strategic Financial Management","Advanced Auditing","Corporate Laws","Direct Tax Laws","Indirect Tax Laws"],
  JEE: ["Physics","Chemistry","Mathematics"],
  NEET: ["Physics","Chemistry","Biology"],
};

export const SUBSCRIPTION_PLANS = {
  FREE:  { price: 0,    label: "Free",     color: "slate" },
  BASIC: { price: 299,  label: "Basic",    color: "blue"  },
  PRO:   { price: 599,  label: "Pro",      color: "purple"},
  INSTITUTE: { price: 4999, label: "Institute", color: "amber" },
};
