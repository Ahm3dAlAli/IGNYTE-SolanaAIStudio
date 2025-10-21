const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options?: RequestInit
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        return {
          error: `HTTP ${response.status}: ${response.statusText}`,
          status: response.status,
        };
      }

      const data = await response.json();
      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Unknown error',
        status: 0,
      };
    }
  }

  async getAgents() {
    return this.request('/api/agents');
  }

  async getAgent(id: string) {
    return this.request(`/api/agents/${id}`);
  }

  async getMarketPrice(token: string) {
    return this.request(`/api/market/price/${token}`);
  }

  async getTransactions() {
    return this.request('/api/transactions');
  }

  async getMetrics() {
    return this.request('/api/metrics');
  }

  async getWalletBalance() {
    return this.request('/api/wallet/balance');
  }

  async executeAgentAction(agentId: string, action: string, params: any) {
    return this.request(`/api/agents/${agentId}/action`, {
      method: 'POST',
      body: JSON.stringify({ action, params }),
    });
  }
}

export const api = new ApiService(API_BASE_URL);

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectInterval = 5000;
  private reconnectTimer?: NodeJS.Timeout;

  constructor(private url: string) {}

  connect(onMessage: (data: any) => void) {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.reconnectTimer = setTimeout(() => {
          console.log('Attempting to reconnect...');
          this.connect(onMessage);
        }, this.reconnectInterval);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }
}

export const createAgentWebSocket = (onMessage: (data: any) => void) => {
  const wsUrl = API_BASE_URL.replace('http', 'ws');
  const ws = new WebSocketService(`${wsUrl}/ws/agents`);
  ws.connect(onMessage);
  return ws;
};

export const createMarketWebSocket = (onMessage: (data: any) => void) => {
  const wsUrl = API_BASE_URL.replace('http', 'ws');
  const ws = new WebSocketService(`${wsUrl}/ws/market`);
  ws.connect(onMessage);
  return ws;
};
