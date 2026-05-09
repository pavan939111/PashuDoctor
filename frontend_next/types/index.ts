export type Role = "user" | "assistant" | "system";

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: Date;
  image_url?: string;
  is_streaming?: boolean;
}

export interface Session {
  case_id: string;
  user_id: string;
  animal_type?: string;
  last_diagnosis?: any;
}
