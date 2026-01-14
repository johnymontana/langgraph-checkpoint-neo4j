"use client";

import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Card,
  Heading,
  HStack,
  IconButton,
  Spinner,
  Stack,
  Text,
} from "@chakra-ui/react";
import { LuClock, LuHistory, LuRefreshCw, LuX } from "react-icons/lu";
import type { Checkpoint } from "@/lib/types";
import { listCheckpoints, timeTravel } from "@/lib/api";

interface HistoryTimelineProps {
  threadId: string;
  onClose: () => void;
  onTimeTravel: () => void;
}

export function HistoryTimeline({
  threadId,
  onClose,
  onTimeTravel,
}: HistoryTimelineProps) {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState<string | null>(null);

  useEffect(() => {
    loadCheckpoints();
  }, [threadId]);

  async function loadCheckpoints() {
    setLoading(true);
    try {
      const data = await listCheckpoints(threadId);
      setCheckpoints(data);
    } catch (error) {
      console.error("Failed to load checkpoints:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRestore(checkpointId: string) {
    if (
      !confirm(
        "Restore conversation to this checkpoint? Current state will be preserved as a new branch.",
      )
    ) {
      return;
    }

    setRestoring(checkpointId);
    try {
      await timeTravel(threadId, checkpointId);
      onTimeTravel();
    } catch (error) {
      console.error("Failed to restore checkpoint:", error);
    } finally {
      setRestoring(null);
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleString();
  }

  function getStepNumber(index: number) {
    return checkpoints.length - index;
  }

  return (
    <Box
      width="320px"
      borderLeftWidth="1px"
      bg="bg.panel"
      display="flex"
      flexDirection="column"
      height="full"
    >
      <HStack justify="space-between" p="4" borderBottomWidth="1px">
        <HStack gap="2">
          <LuHistory />
          <Heading size="sm">History</Heading>
        </HStack>
        <HStack gap="1">
          <IconButton
            aria-label="Refresh"
            variant="ghost"
            size="sm"
            onClick={loadCheckpoints}
          >
            <LuRefreshCw />
          </IconButton>
          <IconButton
            aria-label="Close"
            variant="ghost"
            size="sm"
            onClick={onClose}
          >
            <LuX />
          </IconButton>
        </HStack>
      </HStack>

      <Box flex="1" overflowY="auto" p="4">
        {loading ? (
          <Stack align="center" py="8">
            <Spinner />
            <Text color="fg.muted">Loading checkpoints...</Text>
          </Stack>
        ) : checkpoints.length === 0 ? (
          <Stack align="center" py="8">
            <LuClock size={32} />
            <Text color="fg.muted" textAlign="center">
              No checkpoints yet.
              <br />
              Send a message to create one.
            </Text>
          </Stack>
        ) : (
          <Stack gap="3">
            {checkpoints.map((checkpoint, index) => (
              <Card.Root key={checkpoint.checkpoint_id} size="sm">
                <Card.Body py="2" px="3">
                  <Stack gap="2">
                    <HStack justify="space-between">
                      <Text fontWeight="medium" textStyle="sm">
                        Step {getStepNumber(index)}
                      </Text>
                      {index > 0 && (
                        <Button
                          size="xs"
                          variant="outline"
                          onClick={() =>
                            handleRestore(checkpoint.checkpoint_id)
                          }
                          loading={restoring === checkpoint.checkpoint_id}
                        >
                          Restore
                        </Button>
                      )}
                      {index === 0 && (
                        <Text
                          textStyle="xs"
                          color="green.500"
                          fontWeight="medium"
                        >
                          Current
                        </Text>
                      )}
                    </HStack>
                    <Text textStyle="xs" color="fg.muted">
                      {formatDate(checkpoint.timestamp)}
                    </Text>
                    <Text textStyle="xs" color="fg.muted" truncate>
                      ID: {checkpoint.checkpoint_id.slice(0, 16)}...
                    </Text>
                  </Stack>
                </Card.Body>
              </Card.Root>
            ))}
          </Stack>
        )}
      </Box>
    </Box>
  );
}
