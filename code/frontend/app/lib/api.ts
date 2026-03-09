import axios from 'axios';
import type {
  Content,
  SearchResult,
  RepetitionResult,
  AdaptationResult,
  Stats,
  HealthResponse,
  UploadData
} from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Functions
export const apiClient = {
  // Health check
  health: async (): Promise<HealthResponse> => {
    const { data } = await api.get('/api/health');
    return data;
  },

  // Upload content
  uploadContent: async (uploadData: UploadData) => {
    const { data } = await api.post('/api/content/upload', uploadData);
    return data;
  },

  // List content
  listContent: async (platform?: string): Promise<Content[]> => {
    const { data } = await api.get('/api/content/list', {
      params: platform ? { platform } : {},
    });
    return data;
  },

  // Search content
  searchContent: async (query: string, limit = 5): Promise<SearchResult[]> => {
    const { data } = await api.post('/api/search', { query, limit });
    return data;
  },

  // Check repetition
  checkRepetition: async (content: string): Promise<RepetitionResult> => {
    const { data } = await api.post('/api/check-repetition', { content });
    return data;
  },

  // Adapt for platforms
  adaptPlatform: async (content: string): Promise<AdaptationResult> => {
    const { data } = await api.post('/api/adapt-platform', { content });
    return data;
  },

  // Get stats
  getStats: async (): Promise<Stats> => {
    const { data } = await api.get('/api/stats');
    return data;
  },

  // Export content
  exportContent: async () => {
    const { data } = await api.get('/api/export');
    return data;
  },
};

// WebSocket connection
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;

  constructor() {
    this.url = API_BASE_URL.replace('http', 'ws') + '/ws';
  }

  connect(onMessage: (data: any) => void, onError?: (error: any) => void) {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default apiClient;
