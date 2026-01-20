"use client";

import { useState, useCallback, useEffect } from "react";
import { Box, Flex } from "@chakra-ui/react";
import type { Message } from "@/lib/types";
import { sendMessage } from "@/lib/api";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";

interface ChatInterfaceProps {
  threadId: string;
  initialMessages: Message[];
  onMessagesChange?: () => void;
}

export function ChatInterface({
  threadId,
  initialMessages,
  onMessagesChange,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);

  // Sync messages when initialMessages changes (e.g., after time travel)
  useEffect(() => {
    setMessages(initialMessages);
  }, [initialMessages]);
  const [sending, setSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");

  const handleSend = useCallback(
    async (content: string) => {
      // Add user message immediately
      const userMessage: Message = {
        role: "user",
        content,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setSending(true);
      setStreamingContent("");

      try {
        // Use non-streaming endpoint for simplicity
        const response = await sendMessage(threadId, content);

        // Update messages with response
        setMessages(response.messages);
        onMessagesChange?.();
      } catch (error) {
        console.error("Failed to send message:", error);
        // Remove user message on error
        setMessages((prev) => prev.slice(0, -1));
      } finally {
        setSending(false);
        setStreamingContent("");
      }
    },
    [threadId, onMessagesChange],
  );

  return (
    <Flex direction="column" height="full" bg="bg">
      <MessageList messages={messages} streamingContent={streamingContent} />
      <MessageInput onSend={handleSend} disabled={sending} />
    </Flex>
  );
}
