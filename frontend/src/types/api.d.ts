export type Match = { name: string; score: number; row_index: number; generic?: string; manufacturer?: string };
export type InferResp = { ocr_text: string; top_k: Match[]; mismatch_flag: boolean; flags: string[] };
