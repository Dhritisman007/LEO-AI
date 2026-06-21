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
  status: "pending" | "done" | "error";
  timestamp: number;
};
