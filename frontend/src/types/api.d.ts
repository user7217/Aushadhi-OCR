export interface Match {
  name: string;
  score: number;
  row_index: number;
  generic?: string;        // strength from CSV
  manufacturer?: string;
  form?: string;           // add this
  alias_name?: string;
  main_uses?: string;      // add this
}

export interface InferResp {
  ocr_text: string;
  top_k: Match[];
  mismatch_flag: boolean;
  flags: string[];
  main_uses?: string;      // top match’s uses (convenience)
}
