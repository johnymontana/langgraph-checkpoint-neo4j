"use client";

import { useState, useRef, useEffect, forwardRef } from "react";
import { Box, Button, Flex, Textarea } from "@chakra-ui/react";
import { LuSend } from "react-icons/lu";

// Wrap icon with forwardRef for Chakra UI compatibility
const SendIcon = forwardRef<SVGSVGElement, React.ComponentProps<typeof LuSend>>(
  (props, ref) => <LuSend ref={ref} {...props} />,
);
SendIcon.displayName = "SendIcon";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!disabled && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [disabled]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  }

  return (
    <Box
      as="form"
      onSubmit={handleSubmit}
      p="4"
      borderTopWidth="1px"
      bg="bg.panel"
    >
      <Flex gap="3">
        <Textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled}
          rows={1}
          resize="none"
          autoresize
          maxH="150px"
          flex="1"
        />
        <Button
          type="submit"
          colorPalette="blue"
          disabled={!message.trim() || disabled}
          alignSelf="flex-end"
        >
          <SendIcon />
        </Button>
      </Flex>
    </Box>
  );
}
