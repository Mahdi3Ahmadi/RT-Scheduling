import threading
import queue

# -------------------------------
# Task Class
# -------------------------------
class Task:
    def __init__(self, task_id, execution_time, deadline=None, priority=0):
        self.task_id = task_id
        self.execution_time = execution_time
        self.remaining_time = execution_time
        self.state = "READY"  # READY, WAITING, RUNNING
        self.deadline = deadline  # Only for real-time tasks
        self.priority = priority  # Priority of the task

    def __lt__(self, other):
        """Define comparison for PriorityQueue based on priority (or other criteria)."""
        # Compare by priority (lower value means higher priority)
        return self.priority < other.priority


# -------------------------------
# Resource Manager
# -------------------------------
class ResourceManager:
    def __init__(self, r1, r2):
        self.r1 = r1
        self.r2 = r2
        self.lock = threading.Lock()

    def allocate_resources(self, r1_needed, r2_needed):
        """Allocate resources if available. Return True if successful, else False."""
        with self.lock:
            if self.r1 >= r1_needed and self.r2 >= r2_needed:
                self.r1 -= r1_needed
                self.r2 -= r2_needed
                return True
            return False

    def release_resources(self, r1_released, r2_released):
        """Release resources back to the pool."""
        with self.lock:
            self.r1 += r1_released
            self.r2 += r2_released

# -------------------------------
# Subsystem 1
# -------------------------------
class Subsystem1:
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.waiting_queue = queue.Queue()
        self.ready_queues = [queue.PriorityQueue() for _ in range(3)]
        self.threads = []
        for i in range(3):
            t = threading.Thread(target=self.processor_thread, args=(i,))
            self.threads.append(t)
    def report_status(self):
        """Generate status report for Subsystem 1."""
        print(f"Resources: R1 = {self.resource_manager.r1}, R2 = {self.resource_manager.r2}")
        for i, queue in enumerate(self.ready_queues):
            print(f"Core{i}:")
            if not queue.empty():
                task = list(queue.queue)[0]  # Task currently running
                print(f"  Running Task: {task.task_id}")
            else:
                print("  Running Task: idle")
        print("Waiting Queue:")
        waiting_tasks = list(self.waiting_queue.queue)
        if waiting_tasks:
            for task in waiting_tasks:
                print(f"  Task {task.task_id} - Waiting")
        else:
            print("  Waiting Queue: []")
    def processor_thread(self, core_id):
        """Weighted Round Robin scheduling logic."""
        while True:
            try:
                # Get the next task from the ready queue for this core
                task = self.ready_queues[core_id].get(timeout=1)  # Timeout to avoid infinite wait
                task.state = "RUNNING"

                # Simulate execution of the task for a time slice
                execution_time = min(task.remaining_time, 2)  # Assuming time slice = 2
                task.remaining_time -= execution_time

                # If task is completed, mark it as done
                if task.remaining_time <= 0:
                    print(f"Core {core_id}: Completed Task {task.task_id}")
                else:
                    # If not completed, put it back in the queue
                    task.state = "READY"
                    self.ready_queues[core_id].put(task)
            except queue.Empty:
                # If queue is empty, skip the cycle
                continue

    def load_balancing(self):
        """Load balancing logic for ready queues."""
        # Calculate the load of each ready queue
        loads = [q.qsize() for q in self.ready_queues]

        # Find the most and least loaded queues
        most_loaded = max(range(len(loads)), key=lambda i: loads[i])
        least_loaded = min(range(len(loads)), key=lambda i: loads[i])

        # Balance the load by moving a task from the most loaded queue to the least loaded queue
        if loads[most_loaded] - loads[least_loaded] > 1:
            try:
                task = self.ready_queues[most_loaded].get_nowait()
                self.ready_queues[least_loaded].put(task)
                print(f"Load Balancing: Moved Task {task.task_id} from Core {most_loaded} to Core {least_loaded}")
            except queue.Empty:
                pass

    def return_from_waiting(self):
        """Move tasks from the waiting queue back to the ready queue when resources are available."""
        with self.resource_manager.lock:
            for _ in range(self.waiting_queue.qsize()):
                task = self.waiting_queue.get()
                if self.resource_manager.allocate_resources(1, 1):  # Example resource requirement
                    task.state = "READY"
                    # Add the task to the least loaded ready queue
                    least_loaded = min(range(len(self.ready_queues)), key=lambda i: self.ready_queues[i].qsize())
                    self.ready_queues[least_loaded].put(task)
                    print(f"Returned Task {task.task_id} from Waiting to Ready Queue {least_loaded}")
                else:
                    # Put the task back into the waiting queue if resources are not available
                    self.waiting_queue.put(task)

    def report_status(self):
        """Generate status report for Subsystem 1."""
        print("Subsystem 1 Status Report:")
        for i, queue in enumerate(self.ready_queues):
            print(f"Core {i} Ready Queue:")
            tasks = list(queue.queue)
            for task in tasks:
                print(f"  Task {task.task_id} - State: {task.state}, Remaining Time: {task.remaining_time}")
        print("Waiting Queue:")
        waiting_tasks = list(self.waiting_queue.queue)
        for task in waiting_tasks:
            print(f"  Task {task.task_id} - State: {task.state}, Remaining Time: {task.remaining_time}")


# -------------------------------
# Subsystem 2
# -------------------------------
class Subsystem2:
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.ready_queue = queue.PriorityQueue()
        self.threads = []
        for i in range(2):
            t = threading.Thread(target=self.processor_thread, args=(i,))
            self.threads.append(t)
    def report_status(self):
        """Generate status report for Subsystem 2."""
        print(f"Resources: R1 = {self.resource_manager.r1}, R2 = {self.resource_manager.r2}")
        print("Ready Queue:")
        ready_tasks = list(self.ready_queue.queue)
        if ready_tasks:
            for task in ready_tasks:
                print(f"  Task {task.task_id} - State: {task.state}, Remaining Time: {task.remaining_time}")
        else:
            print("  Ready Queue: []")
    def processor_thread(self, core_id):
        """Shortest Remaining Time First (SRTF) scheduling logic."""
        while True:
            try:
                # Get the task with the shortest remaining time
                task = self.ready_queue.get(timeout=1)  # Timeout to avoid infinite wait
                task.state = "RUNNING"
                
                # Simulate execution of the task
                execution_time = 1  # SRTF processes tasks unit by unit
                task.remaining_time -= execution_time
                
                # If the task is completed, mark it as done
                if task.remaining_time <= 0:
                    print(f"Core {core_id}: Completed Task {task.task_id}")
                else:
                    # If not completed, put it back in the ready queue
                    task.state = "READY"
                    self.ready_queue.put(task)
            except queue.Empty:
                # If the queue is empty, skip the cycle
                continue

    def deadlock_prevention(self):
        """Implement Banker's Algorithm to avoid deadlock."""
        with self.resource_manager.lock:
            # Example implementation of Banker's Algorithm
            print("Running Banker's Algorithm for deadlock prevention...")
            resources_available = [self.resource_manager.r1, self.resource_manager.r2]
            tasks = list(self.ready_queue.queue)  # Copy tasks from the ready queue
            
            # Check if resources can satisfy at least one task
            for task in tasks:
                # Assume each task has specific resource needs
                r1_needed, r2_needed = 1, 1  # Example resource requirements
                if r1_needed <= resources_available[0] and r2_needed <= resources_available[1]:
                    # Simulate granting resources to this task
                    resources_available[0] -= r1_needed
                    resources_available[1] -= r2_needed
                else:
                    print(f"Task {task.task_id} might cause deadlock. Adjusting resources...")
                    # If resources are insufficient, take corrective action (e.g., defer task execution).

    def report_status(self):
        """Generate status report for Subsystem 2."""
        print("Subsystem 2 Status Report:")
        print("Ready Queue:")
        tasks = list(self.ready_queue.queue)
        for task in tasks:
            print(f"  Task {task.task_id} - State: {task.state}, Remaining Time: {task.remaining_time}")
        print(f"Available Resources: R1 = {self.resource_manager.r1}, R2 = {self.resource_manager.r2}")


# -------------------------------
# Subsystem 3
# -------------------------------
class Subsystem3:
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.ready_queue = queue.PriorityQueue()
        self.thread = threading.Thread(target=self.processor_thread)
    def report_status(self):
        """Generate status report for Subsystem 3."""
        print(f"Resources: R1 = {self.resource_manager.r1}, R2 = {self.resource_manager.r2}")
        print("Ready Queue:")
        ready_tasks = list(self.ready_queue.queue)
        if ready_tasks:
            for task in ready_tasks:
                print(f"  Task {task.task_id} - State: {task.state}, Remaining Time: {task.remaining_time}, Deadline: {task.deadline}")
        else:
            print("  Ready Queue: []")
    def processor_thread(self):
        """Rate Monotonic scheduling logic."""
        while True:
            try:
                # Get the highest priority task (lowest period for Rate Monotonic)
                task = self.ready_queue.get(timeout=1)
                task.state = "RUNNING"
                
                # Simulate execution of the task
                execution_time = min(task.remaining_time, 2)  # Execute 2 time units per system time unit
                task.remaining_time -= execution_time
                
                if task.remaining_time <= 0:
                    # If the task is completed
                    print(f"Completed Task {task.task_id} within its deadline.")
                else:
                    # Check if task is still within its deadline
                    if task.deadline > 0:
                        task.deadline -= 1
                        task.state = "READY"
                        self.ready_queue.put(task)  # Requeue the task for the next cycle
                    else:
                        print(f"Task {task.task_id} missed its deadline!")
            except queue.Empty:
                # If the queue is empty, skip this cycle
                continue

    def borrow_resources(self):
        """Borrow resources from other subsystems."""
        with self.resource_manager.lock:
            # Example logic: Request resources from the pool
            print("Borrowing resources from other subsystems...")
            if self.resource_manager.r1 > 0 and self.resource_manager.r2 > 0:
                self.resource_manager.r1 -= 1
                self.resource_manager.r2 -= 1
                print("Borrowed 1 unit of R1 and R2 for this subsystem.")
            else:
                print("Not enough resources to borrow.")

    def return_resources(self):
        """Return borrowed resources to their original subsystems."""
        with self.resource_manager.lock:
            # Example logic: Return resources to the pool
            print("Returning resources to other subsystems...")
            self.resource_manager.r1 += 1
            self.resource_manager.r2 += 1
            print("Returned 1 unit of R1 and R2 to the resource pool.")

    def handle_hard_deadlines(self):
        """Handle tasks with hard deadlines."""
        tasks = list(self.ready_queue.queue)
        for task in tasks:
            if task.deadline <= 0 and task.remaining_time > 0:
                print(f"Task {task.task_id} missed its hard deadline and is being removed.")
                self.ready_queue.queue.remove(task)
            elif task.deadline > 0:
                print(f"Task {task.task_id} is within its deadline and will continue execution.")

    def report_status(self):
        """Generate status report for Subsystem 3."""
        print("Subsystem 3 Status Report:")
        print("Ready Queue:")
        tasks = list(self.ready_queue.queue)
        for task in tasks:
            print(f"  Task {task.task_id} - State: {task.state}, Remaining Time: {task.remaining_time}, Deadline: {task.deadline}")
        print(f"Available Resources: R1 = {self.resource_manager.r1}, R2 = {self.resource_manager.r2}")


# -------------------------------
# Main System
# -------------------------------
class MainSystem:
    def __init__(self):
        self.resource_manager = ResourceManager(r1=10, r2=10)  # Example initial resources
        self.subsystem1 = Subsystem1(self.resource_manager)
        self.subsystem2 = Subsystem2(self.resource_manager)
        self.subsystem3 = Subsystem3(self.resource_manager)
        self.current_time = 0  # Initialize the current time counter

    def report_status(self):
        """Generate status report for all subsystems."""
        print(f"Time: {self.current_time}")
        print("Subsystem 1:")
        self.subsystem1.report_status()
        print("\nSubsystem 2:")
        self.subsystem2.report_status()
        print("\nSubsystem 3:")
        self.subsystem3.report_status()

    def distribute_tasks(self, tasks):
         """Distribute tasks to appropriate subsystems."""
         for subsystem, task in tasks:
          if subsystem == "Sub1":
            # Assign tasks to Subsystem 1 (distribute across cores)
            least_loaded_core = min(range(len(self.subsystem1.ready_queues)),
                                    key=lambda i: self.subsystem1.ready_queues[i].qsize())
            self.subsystem1.ready_queues[least_loaded_core].put(task)
          elif subsystem == "Sub2":
            # Assign tasks to Subsystem 2
            self.subsystem2.ready_queue.put(task)
          elif subsystem == "Sub3":
            # Assign tasks to Subsystem 3
            self.subsystem3.ready_queue.put(task)

    def start(self):
        """Start all subsystems."""
        for t in self.subsystem1.threads:
            t.start()
        for t in self.subsystem2.threads:
            t.start()
        self.subsystem3.thread.start()

    def synchronize(self):
        """Synchronize all subsystems."""
        self.current_time += 1
        self.subsystem1.return_from_waiting()
        self.subsystem2.deadlock_prevention()
        self.subsystem3.handle_hard_deadlines()

    def generate_report(self):
        """Generate a final report of all tasks."""
        print("\n--- Final Report ---")
        print("Subsystem 1:")
        self.subsystem1.report_status()
        print("\nSubsystem 2:")
        self.subsystem2.report_status()
        print("\nSubsystem 3:")
        self.subsystem3.report_status()


    def status_report(self):
        """Generate status report at each time unit."""
        self.report_status()

    def handle_deadlines(self):
        """Ensure real-time deadlines are met by coordinating subsystems."""
        self.subsystem3.handle_hard_deadlines()

def parse_input():
    """Parse input data for resources and tasks."""
    resources = []
    print("Enter the number of resources for each subsystem (e.g., '3 3'). Enter for Sub1, Sub2, Sub3:")
    
    # دریافت منابع برای هر زیرسیستم
    for i in range(1, 4):  # Assuming 3 subsystems
        print(f"Enter resources for Subsystem {i} (e.g., '3 3'):")
        line = input().strip()
        r1, r2 = map(int, line.split())
        resources.append((r1, r2))

    resource_manager = ResourceManager(sum(r[0] for r in resources), sum(r[1] for r in resources))
    tasks = []

    print("\nEnter tasks for each subsystem. End each subsystem's tasks with '$'.\n")
    subsystem_map = {1: "Sub1", 2: "Sub2", 3: "Sub3"}
    for i in range(1, 4):  # Assuming 3 subsystems
        print(f"Enter tasks for Subsystem {i} (e.g., 'T11 4 1 0 0 1'). Enter '$' to finish:")
        while True:
            line = input().strip()
            if line == "$":
                break
            parts = line.split()
            task_id = parts[0]
            execution_time = int(parts[1])
            r1 = int(parts[2])
            r2 = int(parts[3])
            deadline = int(parts[4]) if len(parts) > 4 else None
            tasks.append((subsystem_map[i], Task(task_id, execution_time, deadline, priority=r1)))

    return resource_manager, tasks


# Main simulation
if __name__ == "__main__":
    print("Welcome to the system simulation!")

    # Parse input
    resource_manager, tasks = parse_input()

    # Create the main system
    system = MainSystem()

    # Distribute tasks to subsystems
    system.distribute_tasks(tasks)

    # Start the simulation
    system.start()

    # Example synchronization and reporting loop
    for time_unit in range(10):  # Simulate 10 time units
        system.synchronize()
        system.status_report()

    # Generate the final report
    system.generate_report()
