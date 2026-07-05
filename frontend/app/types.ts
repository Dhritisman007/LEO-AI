export type PlanStep = {
  id: number;
  description: string;
  status: "pending" | "in_progress" | "done" | "failed";
};

export type AgentStep = {
  step: number;
  type: "tool_call" | "thought" | "done" | "error";
  tool?: string;
  params?: any;
  result?: any;
  content?: string;
  thought?: string;
};

export type Message = {
  id: string;
  role: "user" | "leo";
  content: string;
  steps?: AgentStep[];
  plan?: PlanStep[];
  recalled_memories?: { task: string; success: boolean }[];  // NEW
  status: "pending" | "done" | "error";
  timestamp: number;
};

// NEW
export type Conversation = {
  id: string;
  title: string;          // first user message, truncated
  messages: Message[];
  createdAt: number;
  updatedAt: number;
};
