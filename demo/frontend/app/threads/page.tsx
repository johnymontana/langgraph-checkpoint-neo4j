"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Box,
  Button,
  Card,
  Container,
  Flex,
  Grid,
  Heading,
  HStack,
  IconButton,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";
import { LuMessageSquare, LuPlus, LuTrash2 } from "react-icons/lu";
import type { Thread } from "@/lib/types";
import { listThreads, createThread, deleteThread } from "@/lib/api";

export default function ThreadsPage() {
  const router = useRouter();
  const [threads, setThreads] = useState<Thread[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadThreads();
  }, []);

  async function loadThreads() {
    try {
      const data = await listThreads();
      setThreads(data);
    } catch (error) {
      console.error("Failed to load threads:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateThread() {
    setCreating(true);
    try {
      const thread = await createThread();
      router.push(`/threads/${thread.id}`);
    } catch (error) {
      console.error("Failed to create thread:", error);
      setCreating(false);
    }
  }

  async function handleDeleteThread(threadId: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this thread?")) return;

    try {
      await deleteThread(threadId);
      setThreads((prev) => prev.filter((t) => t.id !== threadId));
    } catch (error) {
      console.error("Failed to delete thread:", error);
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleString();
  }

  if (loading) {
    return (
      <Flex height="100vh" align="center" justify="center">
        <Spinner size="xl" />
      </Flex>
    );
  }

  return (
    <Container maxW="6xl" py="8">
      <Stack gap="6">
        <Flex justify="space-between" align="center">
          <Heading size="xl">Conversations</Heading>
          <Button
            colorPalette="blue"
            onClick={handleCreateThread}
            loading={creating}
          >
            <LuPlus /> New Conversation
          </Button>
        </Flex>

        {threads.length === 0 ? (
          <Card.Root>
            <Card.Body>
              <Stack align="center" gap="4" py="8">
                <LuMessageSquare size={48} />
                <Text color="fg.muted">No conversations yet</Text>
                <Button colorPalette="blue" onClick={handleCreateThread}>
                  Start your first conversation
                </Button>
              </Stack>
            </Card.Body>
          </Card.Root>
        ) : (
          <Grid
            templateColumns={{
              base: "1fr",
              md: "repeat(2, 1fr)",
              lg: "repeat(3, 1fr)",
            }}
            gap="4"
          >
            {threads.map((thread) => (
              <Card.Root
                key={thread.id}
                cursor="pointer"
                onClick={() => router.push(`/threads/${thread.id}`)}
                _hover={{ bg: "bg.subtle" }}
                transition="background 0.2s"
              >
                <Card.Body>
                  <Stack gap="3">
                    <HStack justify="space-between">
                      <HStack gap="2">
                        <LuMessageSquare />
                        <Text fontWeight="medium" truncate maxW="200px">
                          {thread.name || thread.id.slice(0, 8) + "..."}
                        </Text>
                      </HStack>
                      <IconButton
                        aria-label="Delete thread"
                        variant="ghost"
                        colorPalette="red"
                        size="sm"
                        onClick={(e) => handleDeleteThread(thread.id, e)}
                      >
                        <LuTrash2 />
                      </IconButton>
                    </HStack>
                    <Box>
                      <Text textStyle="sm" color="fg.muted">
                        {thread.message_count} messages
                      </Text>
                      <Text textStyle="xs" color="fg.muted">
                        Created {formatDate(thread.created_at)}
                      </Text>
                    </Box>
                  </Stack>
                </Card.Body>
              </Card.Root>
            ))}
          </Grid>
        )}
      </Stack>
    </Container>
  );
}
