export interface Match {
  name: string;
  score: number;
  row_index: number;
  generic?: string;       // strength
  manufacturer?: string;
  form?: string;
  alias_name?: string;
  main_uses?: string;
}

export interface InferResp {
  ocr_text: string;
  top_k: Match[];
  mismatch_flag: boolean;
  flags: string[];
  main_uses?: string;     // best match convenience
  edit_distance?: number; // new
  vision_score?: number;  // new 0-100
}
