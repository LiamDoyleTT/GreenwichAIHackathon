import { Button, FileInput, Group, Stack, Textarea } from '@mantine/core';
import {
  IconClearAll,

  IconSend,
  IconUpload,
} from '@tabler/icons-react';
import { useRef, useState } from 'react';

interface ChatBoxProps {
  textMessageCreated: (message: string) => void;
  chatHistoryCleared: () => void;
  auditFileUploaded: (file: File | null) => void;
}

export default function ChatBox({
  textMessageCreated,
  chatHistoryCleared,
  auditFileUploaded,
}: ChatBoxProps) {
  const [message, setMessage] = useState<string>('');

  const hiddenFileInput = useRef<HTMLButtonElement>(null);
  const onDocFileClick = () => {
    if (hiddenFileInput.current) {
      hiddenFileInput.current.click();
    }
  };

  const onNewTextMessage = () => {
    textMessageCreated(message);
    setMessage('');
  };
  
  return (
    <>
      <Stack>
        <Textarea
          placeholder="Type your message here"
          autosize
          minRows={7}
          value={message}
          onChange={(e) => setMessage(e.currentTarget.value)}
        />
        <Group w="100%">
          <Group>
            <Button onClick={onNewTextMessage} leftSection={<IconSend />}>
              Send
            </Button>
            <Button onClick={onDocFileClick} leftSection={<IconUpload />}>
              Upload Audit
            </Button>
            {/* <Button
              leftSection={isRecording() ? <IconMicrophone /> : <IconMicrophoneOff />}
              onClick={onRecordingClick}
            >
              {isRecording()
                ? // ? 'Stop Recording" ('.concat(recorderControls.recordingTime.toString(), ')')
                  'Stop Recording'
                : 'Start Recording'}
            </Button> */}
          </Group>
          <Group ml="auto">
            <Button variant="outline" onClick={chatHistoryCleared} leftSection={<IconClearAll />}>
              Clear Chat
            </Button>
          </Group>
        </Group>
        <FileInput
          label="Audit File"
          description="Audit File"
          placeholder="Audit File"
          style={{ display: 'none' }}
          onChange={auditFileUploaded}
          ref={hiddenFileInput}
        />
      </Stack>
    </>
  );
}
