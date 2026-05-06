const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export class VideoStreamService {
  private inputSocket: WebSocket | null = null;
  private onProcessedFrame: (data: any) => void;

  constructor(onProcessedFrame: (data: any) => void) {
    this.onProcessedFrame = onProcessedFrame;
  }

  connect() {
    this.inputSocket = new WebSocket(`${WS_BASE_URL}/api/stream/input`);

    this.inputSocket.onopen = () => {
      console.log('WebSocket connected');
    };

    this.inputSocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.onProcessedFrame(data);
    };

    this.inputSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.inputSocket.onclose = () => {
      console.log('WebSocket disconnected');
    };
  }

  sendFrame(base64Frame: string) {
    if (this.inputSocket?.readyState === WebSocket.OPEN) {
      this.inputSocket.send(JSON.stringify({ frame: base64Frame }));
    }
  }

  disconnect() {
    this.inputSocket?.close();
  }
}