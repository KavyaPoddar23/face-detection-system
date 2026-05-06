const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export class VideoStreamService {
  private inputSocket: WebSocket | null = null;
  private onProcessedFrame: (data: any) => void;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 3;

  constructor(onProcessedFrame: (data: any) => void) {
    this.onProcessedFrame = onProcessedFrame;
  }

  connect() {
    try {
      this.inputSocket = new WebSocket(`${WS_BASE_URL}/api/stream/input`);

      this.inputSocket.onopen = () => {
        console.log('WebSocket connected to backend');
        this.reconnectAttempts = 0;
      };

      this.inputSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onProcessedFrame(data);
        } catch (e) {
          console.error('Failed to parse frame data:', e);
        }
      };

      this.inputSocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      this.inputSocket.onclose = () => {
        console.log('WebSocket disconnected');
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }

  sendFrame(base64Frame: string) {
    if (this.inputSocket?.readyState === WebSocket.OPEN) {
      this.inputSocket.send(JSON.stringify({ frame: base64Frame }));
    }
  }

  isConnected(): boolean {
    return this.inputSocket?.readyState === WebSocket.OPEN;
  }

  disconnect() {
    this.inputSocket?.close();
    this.inputSocket = null;
  }
}