export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: 'STUDENT' | 'TEACHER' | 'ADMIN';
  phone_number?: string;
  profile_picture?: string;
  date_of_birth?: string;
  bio?: string;
  is_email_verified: boolean;
  created_at: string;
  student_profile?: StudentProfile;
  teacher_profile?: TeacherProfile;
}

export interface StudentProfile {
  grade_level?: string;
  subjects_interested: string[];
  learning_goals?: string;
  preferred_learning_style?: string;
}

export interface TeacherProfile {
  highest_degree?: string;
  university?: string;
  specialization?: string;
  years_of_experience: number;
  subjects_taught: string[];
  teaching_languages: string[];
  hourly_rate: number;
  is_verified: boolean;
  available_for_offline: boolean;
  available_for_online: boolean;
  average_rating: number;
  total_reviews: number;
  total_sessions: number;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  role: 'STUDENT' | 'TEACHER';
  phone_number?: string;
  date_of_birth?: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  tokens: AuthTokens;
}
