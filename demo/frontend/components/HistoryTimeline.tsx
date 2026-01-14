"use client";

import { useEffect, useState } from "react";
import {
  Badge,
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
import {
  LuClock,
  LuGitBranch,
  LuHistory,
  LuRefreshCw,
  LuX,
} from "react-icons/lu";
import type { Branch, Checkpoint, Message } from "@/lib/types";
import {
  listCheckpoints,
  listBranches,
  switchBranch,
  timeTravel,
} from "@/lib/api";

interface HistoryTimelineProps {
  threadId: string;
  onClose: () => void;
  onTimeTravel: (messages: Message[]) => void;
}

export function HistoryTimeline({
  threadId,
  onClose,
  onTimeTravel,
}: HistoryTimelineProps) {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState<string | null>(null);
  const [switchingBranch, setSwitchingBranch] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [threadId]);

  async function loadData() {
    setLoading(true);
    try {
      const [checkpointData, branchData] = await Promise.all([
        listCheckpoints(threadId),
        listBranches(threadId),
      ]);
      setCheckpoints(checkpointData);
      setBranches(branchData);
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleRestore(checkpointId: string) {
    const confirmMsg =
      "Fork from this checkpoint? This will create a new branch and switch to it.";
    if (!confirm(confirmMsg)) {
      return;
    }

    setRestoring(checkpointId);
    try {
      const result = await timeTravel(threadId, checkpointId);
      onTimeTravel(result.messages);
      // Reload data to show the new branch
      loadData();
    } catch (error) {
      console.error("Failed to fork from checkpoint:", error);
    } finally {
      setRestoring(null);
    }
  }

  async function handleSwitchBranch(branchId: string) {
    setSwitchingBranch(branchId);
    try {
      const result = await switchBranch(threadId, branchId);
      onTimeTravel(result.messages);
      // Reload data to update active branch
      loadData();
    } catch (error) {
      console.error("Failed to switch branch:", error);
    } finally {
      setSwitchingBranch(null);
    }
  }

  function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleString();
  }

  function getStepNumber(index: number) {
    return checkpoints.length - index;
  }

  const activeBranch = branches.find((b) => b.is_active);

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
            onClick={loadData}
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
            <Text color="fg.muted">Loading history...</Text>
          </Stack>
        ) : (
          <Stack gap="4">
            {/* Branch Selector */}
            {branches.length > 0 && (
              <Box>
                <HStack gap="2" mb="2">
                  <LuGitBranch />
                  <Text fontWeight="medium" textStyle="sm">
                    Branches ({branches.length})
                  </Text>
                </HStack>
                <Stack gap="2">
                  {branches.map((branch) => (
                    <Card.Root
                      key={branch.branch_id}
                      size="sm"
                      variant={branch.is_active ? "elevated" : "outline"}
                      borderColor={branch.is_active ? "green.500" : undefined}
                      borderWidth={branch.is_active ? "2px" : "1px"}
                    >
                      <Card.Body py="2" px="3">
                        <HStack justify="space-between">
                          <Stack gap="0">
                            <HStack gap="2">
                              <Text fontWeight="medium" textStyle="sm">
                                {branch.name}
                              </Text>
                              {branch.is_active && (
                                <Badge colorPalette="green" size="sm">
                                  Active
                                </Badge>
                              )}
                            </HStack>
                            {branch.fork_point_id && (
                              <Text textStyle="xs" color="fg.muted">
                                Forked from {branch.fork_point_id.slice(0, 8)}
                                ...
                              </Text>
                            )}
                          </Stack>
                          {!branch.is_active && (
                            <Button
                              size="xs"
                              variant="outline"
                              onClick={() =>
                                handleSwitchBranch(branch.branch_id)
                              }
                              loading={switchingBranch === branch.branch_id}
                            >
                              Switch
                            </Button>
                          )}
                        </HStack>
                      </Card.Body>
                    </Card.Root>
                  ))}
                </Stack>
              </Box>
            )}

            {/* Checkpoints */}
            <Box>
              <HStack gap="2" mb="2">
                <LuClock />
                <Text fontWeight="medium" textStyle="sm">
                  Checkpoints
                  {activeBranch && (
                    <Text as="span" color="fg.muted" fontWeight="normal">
                      {" "}
                      on {activeBranch.name}
                    </Text>
                  )}
                </Text>
              </HStack>

              {checkpoints.length === 0 ? (
                <Stack align="center" py="8">
                  <Text color="fg.muted" textAlign="center">
                    No checkpoints yet.
                    <br />
                    Send a message to create one.
                  </Text>
                </Stack>
              ) : (
                <Stack gap="2">
                  {checkpoints.map((checkpoint, index) => (
                    <Card.Root key={checkpoint.checkpoint_id} size="sm">
                      <Card.Body py="2" px="3">
                        <Stack gap="1">
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
                                Fork
                              </Button>
                            )}
                            {index === 0 && (
                              <Badge colorPalette="blue" size="sm">
                                HEAD
                              </Badge>
                            )}
                          </HStack>
                          <Text textStyle="xs" color="fg.muted">
                            {formatDate(checkpoint.timestamp)}
                          </Text>
                          <Text textStyle="xs" color="fg.muted" truncate>
                            {checkpoint.checkpoint_id.slice(0, 20)}...
                          </Text>
                        </Stack>
                      </Card.Body>
                    </Card.Root>
                  ))}
                </Stack>
              )}
            </Box>
          </Stack>
        )}
      </Box>
    </Box>
  );
}
