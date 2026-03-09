// Type definitions for MemoryThread

export interface Content {
  id: number;
  title: string;
  platform: string;
  created_at: string;
  word_count: number;
  tags: string[];
}

export interface SearchResult {
  id: number;
  title: string;
  content_preview: string;
  platform: string;
  similarity: number;
  created_at: string;
}

export interface RepetitionResult {
  is_repetition: boolean;
  similar_content: SimilarContent[];
  message: string;
  max_similarity: number;
}

export interface SimilarContent {
  id: number;
  title: string;
  content: string;
  platform: string;
  similarity: number;
  created_at: string;
}

export interface PlatformAdaptation {
  title: string;
  content: string;
  tone?: string;
  format?: string;
}

export interface AdaptationResult {
  linkedin: PlatformAdaptation;
  twitter: PlatformAdaptation;
  instagram: PlatformAdaptation;
  tiktok: PlatformAdaptation;
  original_length: number;
}

export interface Stats {
  total_content: number;
  platform_breakdown: Record<string, number>;
  total_words: number;
  recent_activity: number;
  avg_words_per_content: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  total_content: number;
}

export type Platform = 'general' | 'blog' | 'linkedin' | 'twitter' | 'instagram' | 'tiktok';

export interface UploadData {
  title: string;
  content: string;
  platform: Platform;
  tags?: string[];
}
