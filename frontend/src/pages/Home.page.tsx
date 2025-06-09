import { useState } from 'react';
import { Box, Container, Stack } from '@mantine/core';
import ChatMessage from '@/domain/ChatMessage';
import ChatBox from '@/components/ChatBox/ChatBox';
import ChatWindow from '@/components/ChatWindow/ChatWindow';

export function HomePage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleError = async (error: Response) => {
    const contentType = error.headers.get('content-type');
    let errorDetail = 'Unknown Error - Status Code '.concat(error.status.toString());

    if (contentType && contentType.indexOf('application/json') !== -1) {
      errorDetail = (await error.json()).detail;
    }

    setMessages((oldMessages) => [
      ...oldMessages,
      { message: 'Error: '.concat(errorDetail), role: 'bot', type: 'error' },
    ]);
    setLoading(false);
  };

  const sendChatRequest = (endpoint: string, headers: any, body: any) => {
    fetch(endpoint, {
      method: 'POST',
      headers,
      body,
    })
      .then((response) => {
        if (response.ok) {
          return response.json();
        }
        return Promise.reject(response);
      })
      .then((data) => {
        setMessages((oldMessages) => [...oldMessages, { message: data.response, role: 'bot' }]);
        setLoading(false);
      })
      .catch(async (error) => handleError(error));
  };

  const textMessageCreated = (message: string) => {
    setMessages((oldMessages) => [...oldMessages, { message, role: 'person' }]);
    setLoading(true);

    sendChatRequest(
      '/api/process',
      {
        'Content-Type': 'application/json',
      },
      JSON.stringify({ body: message })
    );
  };

  const auditFileUploaded = (file: File | null) => {
    setMessages((oldMessages) => [
      ...oldMessages,
      { message: 'Audit Uploaded...', role: 'person' },
    ]);

    setLoading(true);

    const formData = new FormData();
    formData.append('request', file);

    sendChatRequest('/api/process-audit-file', {}, formData);
  };

  const docFileUploaded = (file: File | null) => {
    setMessages((oldMessages) => [
      ...oldMessages,
      { message: 'Doc Uploaded...', role: 'person' },
    ]);

    setLoading(true);

    const formData = new FormData();
    formData.append('request', file);

    sendChatRequest('/api/process-doc-file', {}, formData);
  };

  const clearChatHistory = () => setMessages([]);

  return (
    <Container fluid>
      <Stack style={{ height: '87vh' }} p={0}>
        <ChatWindow messages={messages} loading={loading} />
        <Box>
          <ChatBox
            textMessageCreated={textMessageCreated}
            chatHistoryCleared={clearChatHistory}
            auditFileUploaded={auditFileUploaded}
          />
        </Box>
      </Stack>
    </Container>
  );
}
