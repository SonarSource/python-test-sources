FROM busybox

# Report the memory (through the size of the group memory)
RUN echo "memory:" $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)
