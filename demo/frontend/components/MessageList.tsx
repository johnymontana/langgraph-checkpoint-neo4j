"use client";

import { useRef, useEffect, forwardRef } from "react";
import {
  Box,
  Card,
  Code,
  Flex,
  HStack,
  Stack,
  Text,
  Circle,
  Icon,
} from "@chakra-ui/react";
import { LuBot, LuUser, LuWrench } from "react-icons/lu";
import type { Message } from "@/lib/types";

// Wrap icons with forwardRef for Chakra UI compatibility
const BotIcon = forwardRef<SVGSVGElement, React.ComponentProps<typeof LuBot>>(
  (props, ref) => <LuBot ref={ref} {...props} />,
);
BotIcon.displayName = "BotIcon";

const UserIcon = forwardRef<SVGSVGElement, React.ComponentProps<typeof LuUser>>(
  (props, ref) => <LuUser ref={ref} {...props} />,
);
UserIcon.displayName = "UserIcon";

const WrenchIcon = forwardRef<
  SVGSVGElement,
  React.ComponentProps<typeof LuWrench>
>((props, ref) => <LuWrench ref={ref} {...props} />);
WrenchIcon.displayName = "WrenchIcon";

interface MessageListProps {
  messages: Message[];
  streamingContent?: string;
}

export function MessageList({ messages, streamingContent }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  function renderMessageContent(content: string) {
    // Simple markdown-like rendering for code blocks
    const parts = content.split(/(```[\s\S]*?```)/g);
    return parts.map((part, i) => {
      if (part.startsWith("```") && part.endsWith("```")) {
        const code = part.slice(3, -3);
        const lines = code.split("\n");
        const language = lines[0];
        const codeContent = lines.slice(1).join("\n");
        return (
          <Box key={i} my="2">
            <Code display="block" whiteSpace="pre-wrap" p="3" borderRadius="md">
              {codeContent || code}
            </Code>
          </Box>
        );
      }
      return (
        <Text key={i} whiteSpace="pre-wrap">
          {part}
        </Text>
      );
    });
  }

  function renderToolCalls(message: Message) {
    if (!message.tool_calls || message.tool_calls.length === 0) return null;

    return (
      <Stack gap="2" mt="2">
        {message.tool_calls.map((call) => (
          <Card.Root key={call.id} size="sm" variant="outline">
            <Card.Body py="2" px="3">
              <HStack gap="2">
                <Icon color="orange.500">
                  <WrenchIcon />
                </Icon>
                <Text fontWeight="medium" textStyle="sm">
                  {call.name}
                </Text>
              </HStack>
              <Code display="block" textStyle="xs" mt="1">
                {JSON.stringify(call.args, null, 2)}
              </Code>
            </Card.Body>
          </Card.Root>
        ))}
      </Stack>
    );
  }

  function renderMessage(message: Message, index: number) {
    const isUser = message.role === "user";
    const isTool = message.role === "tool";

    if (isTool) {
      return (
        <Flex key={index} justify="center" my="2">
          <Card.Root size="sm" variant="subtle" maxW="md">
            <Card.Body py="2" px="3">
              <HStack gap="2">
                <Icon color="green.500">
                  <WrenchIcon />
                </Icon>
                <Text textStyle="sm" fontWeight="medium">
                  Tool Result
                </Text>
              </HStack>
              <Code display="block" textStyle="xs" mt="1" whiteSpace="pre-wrap">
                {typeof message.content === "string"
                  ? message.content.slice(0, 200)
                  : JSON.stringify(message.content)}
              </Code>
            </Card.Body>
          </Card.Root>
        </Flex>
      );
    }

    return (
      <Flex key={index} justify={isUser ? "flex-end" : "flex-start"} mb="4">
        <HStack align="start" gap="3" maxW="80%">
          {!isUser && (
            <Circle size="8" bg="blue.500" color="white" flexShrink={0}>
              <BotIcon size={16} />
            </Circle>
          )}
          <Card.Root
            bg={isUser ? "blue.500" : "bg.subtle"}
            color={isUser ? "white" : "fg"}
          >
            <Card.Body py="2" px="3">
              {renderMessageContent(message.content)}
              {renderToolCalls(message)}
            </Card.Body>
          </Card.Root>
          {isUser && (
            <Circle size="8" bg="gray.500" color="white" flexShrink={0}>
              <UserIcon size={16} />
            </Circle>
          )}
        </HStack>
      </Flex>
    );
  }

  return (
    <Box flex="1" overflowY="auto" p="4">
      {messages.length === 0 ? (
        <Flex height="full" align="center" justify="center">
          <Stack align="center" gap="4">
            <Circle size="16" bg="blue.100">
              <Icon color="blue.500" boxSize="8">
                <BotIcon />
              </Icon>
            </Circle>
            <Text color="fg.muted" textAlign="center">
              Start a conversation by typing a message below.
              <br />
              Try asking about the weather or a math calculation!
            </Text>
          </Stack>
        </Flex>
      ) : (
        <>
          {messages.map((message, index) => renderMessage(message, index))}
          {streamingContent && (
            <Flex justify="flex-start" mb="4">
              <HStack align="start" gap="3" maxW="80%">
                <Circle size="8" bg="blue.500" color="white" flexShrink={0}>
                  <BotIcon size={16} />
                </Circle>
                <Card.Root bg="bg.subtle">
                  <Card.Body py="2" px="3">
                    <Text whiteSpace="pre-wrap">{streamingContent}</Text>
                  </Card.Body>
                </Card.Root>
              </HStack>
            </Flex>
          )}
        </>
      )}
      <div ref={bottomRef} />
    </Box>
  );
}
