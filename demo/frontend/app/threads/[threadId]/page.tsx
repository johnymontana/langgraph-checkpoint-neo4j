"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  Box,
  Button,
  Flex,
  Heading,
  HStack,
  IconButton,
  Spinner,
  Text,
} from "@chakra-ui/react";
import {
  LuArrowLeft,
  LuHistory,
  LuMessageSquare,
  LuTrash2,
} from "react-icons/lu";
import type { Message, Thread } from "@/lib/types";
import { getThread, getMessages, deleteThread } from "@/lib/api";
import { ChatInterface } from "@/components/ChatInterface";
import { HistoryTimeline } from "@/components/HistoryTimeline";

export default function ThreadPage() {
  const params = useParams();
  const router = useRouter();
  const threadId = params.threadId as string;

  const [thread, setThread] = useState<Thread | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [showHistory, setShowHistory] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [threadData, messagesData] = await Promise.all([
        getThread(threadId),
        getMessages(threadId),
      ]);
      setThread(threadData);
      setMessages(messagesData);
    } catch (error) {
      console.error("Failed to load thread:", error);
      router.push("/threads");
    } finally {
      setLoading(false);
    }
  }, [threadId, router]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleDelete() {
    if (!confirm("Are you sure you want to delete this conversation?")) return;

    try {
      await deleteThread(threadId);
      router.push("/threads");
    } catch (error) {
      console.error("Failed to delete thread:", error);
    }
  }

  function handleTimeTravel() {
    // Reload messages after time travel
    loadData();
    setShowHistory(false);
  }

  if (loading) {
    return (
      <Flex height="100vh" align="center" justify="center">
        <Spinner size="xl" />
      </Flex>
    );
  }

  if (!thread) {
    return (
      <Flex height="100vh" align="center" justify="center">
        <Text>Thread not found</Text>
      </Flex>
    );
  }

  return (
    <Flex height="100vh" direction="column">
      {/* Header */}
      <Box borderBottomWidth="1px" bg="bg.panel" px="4" py="3">
        <Flex justify="space-between" align="center">
          <HStack gap="3">
            <IconButton
              aria-label="Back to threads"
              variant="ghost"
              onClick={() => router.push("/threads")}
            >
              <LuArrowLeft />
            </IconButton>
            <HStack gap="2">
              <LuMessageSquare />
              <Heading size="md">
                {threadId.slice(0, 8)}...
              </Heading>
            </HStack>
          </HStack>
          <HStack gap="2">
            <Button
              variant={showHistory ? "solid" : "outline"}
              size="sm"
              onClick={() => setShowHistory(!showHistory)}
            >
              <LuHistory /> History
            </Button>
            <IconButton
              aria-label="Delete thread"
              variant="ghost"
              colorPalette="red"
              onClick={handleDelete}
            >
              <LuTrash2 />
            </IconButton>
          </HStack>
        </Flex>
      </Box>

      {/* Main content */}
      <Flex flex="1" overflow="hidden">
        <Box flex="1">
          <ChatInterface
            threadId={threadId}
            initialMessages={messages}
            onMessagesChange={loadData}
          />
        </Box>
        {showHistory && (
          <HistoryTimeline
            threadId={threadId}
            onClose={() => setShowHistory(false)}
            onTimeTravel={handleTimeTravel}
          />
        )}
      </Flex>
    </Flex>
  );
}
