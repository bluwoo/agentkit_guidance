import { create } from 'zustand';
import type {
  AcceptanceCase,
  AggregateMetricsPanel,
  ChatMessage,
  ConfirmedPoint,
  GoalCard,
  StepId,
  TestState,
  Topology,
  TraceOverlay,
  ValidationIssue,
} from '@/types';

/**
 * Global wizard state. Single source of truth across all 4 steps.
 * The test panel + overlay follows the S0-S4 finite state machine (01 §6):
 *   S0 idle | S1 running | S2 done+trace | S3 done+no-trace | S4 failed.
 */

interface StepMeta {
  completed: boolean;
  needsReview: boolean;
}

interface WizardState {
  // navigation
  currentStep: StepId;
  authenticated: boolean;
  setAuthenticated: (v: boolean) => void;
  steps: Record<StepId, StepMeta>;

  // step 1
  goal: GoalCard;
  points: ConfirmedPoint[];
  chatMessages: ChatMessage[];
  interviewStarted: boolean;
  adrMarkdown: string;
  glossaryMarkdown: string;

  // step 2
  cases: AcceptanceCase[];
  evalDatasetsConnected: boolean;

  // step 3
  topology: Topology;
  validationIssues: ValidationIssue[];
  selectedNodeId: string | null;
  recommendations: string[];

  // step 4 — test state machine
  testState: TestState;
  testPrompt: string;
  userId: string;
  sessionId: string;
  testOutput: string;
  activeTraceId: string | null;
  traceOverlay: TraceOverlay | null;
  traceOverlayEnabled: boolean;
  aggregate: AggregateMetricsPanel | null;
  testError: string | null;

  // actions
  setStep: (step: StepId) => void;
  markCompleted: (step: StepId) => void;
  markNeedsReview: (step: StepId) => void;

  setGoal: (goal: Partial<GoalCard>) => void;
  setPoints: (points: ConfirmedPoint[]) => void;
  addPoint: (text: string) => void;
  removePoint: (id: string) => void;
  togglePoint: (id: string) => void;
  setChatMessages: (msgs: ChatMessage[]) => void;
  appendChatMessage: (msg: ChatMessage) => void;
  setInterviewStarted: (v: boolean) => void;
  setAdr: (md: string) => void;
  setGlossary: (md: string) => void;

  setCases: (cases: AcceptanceCase[]) => void;
  setDatasetsConnected: (v: boolean) => void;

  setTopology: (topology: Topology) => void;
  setValidationIssues: (issues: ValidationIssue[]) => void;
  setSelectedNode: (id: string | null) => void;
  setRecommendations: (ids: string[]) => void;

  setTestState: (s: TestState) => void;
  setTestPrompt: (v: string) => void;
  setUserId: (v: string) => void;
  setSessionId: (v: string) => void;
  appendTestOutput: (v: string) => void;
  resetTestOutput: () => void;
  setActiveTraceId: (id: string | null) => void;
  setTraceOverlay: (o: TraceOverlay | null) => void;
  setTraceOverlayEnabled: (v: boolean) => void;
  setAggregate: (a: AggregateMetricsPanel | null) => void;
  setTestError: (e: string | null) => void;
}

const emptyGoal: GoalCard = {
  name: '',
  target_user: '',
  task: '',
  typical_input: '',
  expected_output: '',
  non_goals: [],
  long_running: false,
  migration: null,
  classification: null,
};

const emptyTopology: Topology = { nodes: [], edges: [] };

export const useWizardStore = create<WizardState>((set) => ({
  currentStep: 1,
  authenticated: false,
  setAuthenticated: (v: boolean) => set({ authenticated: v }),
  steps: {
    1: { completed: false, needsReview: false },
    2: { completed: false, needsReview: false },
    3: { completed: false, needsReview: false },
    4: { completed: false, needsReview: false },
  },

  goal: emptyGoal,
  points: [],
  chatMessages: [],
  interviewStarted: false,
  adrMarkdown: '',
  glossaryMarkdown: '',

  cases: [],
  evalDatasetsConnected: false,

  topology: emptyTopology,
  validationIssues: [],
  selectedNodeId: null,
  recommendations: [],

  testState: 'S0',
  testPrompt: '',
  userId: 'wizard-user',
  sessionId: '',
  testOutput: '',
  activeTraceId: null,
  traceOverlay: null,
  traceOverlayEnabled: false,
  aggregate: null,
  testError: null,

  setStep: (step) => set({ currentStep: step }),
  markCompleted: (step) =>
    set((s) => ({ steps: { ...s.steps, [step]: { ...s.steps[step], completed: true, needsReview: false } } })),
  markNeedsReview: (step) =>
    set((s) => ({ steps: { ...s.steps, [step]: { ...s.steps[step], needsReview: true } } })),

  setGoal: (partial) => set((s) => ({ goal: { ...s.goal, ...partial } })),
  setPoints: (points) => set({ points }),
  addPoint: (text) =>
    set((s) => ({
      points: [...s.points, { id: `p${Date.now()}`, text, confirmed: true }],
    })),
  removePoint: (id) => set((s) => ({ points: s.points.filter((p) => p.id !== id) })),
  togglePoint: (id) =>
    set((s) => ({
      points: s.points.map((p) => (p.id === id ? { ...p, confirmed: !p.confirmed } : p)),
    })),
  setChatMessages: (msgs) => set({ chatMessages: msgs }),
  appendChatMessage: (msg) => set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  setInterviewStarted: (v) => set({ interviewStarted: v }),
  setAdr: (md) => set({ adrMarkdown: md }),
  setGlossary: (md) => set({ glossaryMarkdown: md }),

  setCases: (cases) => set({ cases }),
  setDatasetsConnected: (v) => set({ evalDatasetsConnected: v }),

  setTopology: (topology) => set({ topology }),
  setValidationIssues: (issues) => set({ validationIssues: issues }),
  setSelectedNode: (id) => set({ selectedNodeId: id }),
  setRecommendations: (ids) => set({ recommendations: ids }),

  setTestState: (ts) => set({ testState: ts }),
  setTestPrompt: (v) => set({ testPrompt: v }),
  setUserId: (v) => set({ userId: v }),
  setSessionId: (v) => set({ sessionId: v }),
  appendTestOutput: (v) => set((s) => ({ testOutput: s.testOutput + v })),
  resetTestOutput: () => set({ testOutput: '', testError: null, activeTraceId: null, traceOverlay: null, traceOverlayEnabled: false }),
  setActiveTraceId: (id) => set({ activeTraceId: id }),
  setTraceOverlay: (o) => set({ traceOverlay: o }),
  setTraceOverlayEnabled: (v) => set({ traceOverlayEnabled: v }),
  setAggregate: (a) => set({ aggregate: a }),
  setTestError: (e) => set({ testError: e }),
}));
