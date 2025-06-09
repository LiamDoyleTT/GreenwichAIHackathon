import { Card, Flex } from '@mantine/core';
import ChatMessage from '@/domain/ChatMessage';
import Markdown from "react-markdown";
import rehypeRaw from "rehype-raw";
interface ChatMessageDisplayProps {
  message: ChatMessage;
}

export default function ChatMessageDisplay({ message }: ChatMessageDisplayProps) {
  const justify = message.role === 'bot' ? 'flex-start' : 'flex-end';
  let bg = message.role === 'bot' ? 'gray.2' : 'green.4';

  if (message.type === 'error') {
    bg = 'red.4';
  }

  return (
    <Flex justify={justify}>
      <Card bg={bg} w="55%" shadow="none">
        <Markdown rehypePlugins={[rehypeRaw]}>
          {message.message}
        </Markdown>
      </Card>
    </Flex>
  );
}
