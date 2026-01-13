# Google Tasks and Notion Sync Process

This flow combines the synchronization processes between Google Tasks and Notion for both directions: Google to Notion and Notion to Google. The process ensures tasks are updated or created based on their states in each platform.

---

## **Flow Description**
The process involves two main workflows:

1. **Google to Notion Sync**: Tasks in Google Tasks are synchronized with Notion.
2. **Notion to Google Sync**: Notion pages are synchronized with Google Tasks.

Each workflow processes tasks and pages iteratively to ensure both platforms remain consistent.

---

## **Google to Notion Sync Functions**

### **Task 1: Mark Notion Page as Done**
If a task in Google Tasks is marked as **Done**, the corresponding Notion page is updated to reflect this status.
- **Flow Steps:**
  1. Retrieve completed tasks in Google Tasks since the last execution.
  2. Update the associated Notion page to mark it as done.
  3. Check if there are more tasks to process in the current tasklist.

### **Task 2: Create Notion Page for New Tasks**
If new tasks are created in Google Tasks, a corresponding page is created in Notion. The task in Google Tasks is then renamed to include the Notion page ID in the title.
- **Flow Steps:**
  1. Retrieve tasks created in Google Tasks since the last execution.
  2. Create an associated Notion page for each new task.
  3. Retrieve the ID of the created Notion page.
  4. Rename the Google Task to include the Notion page ID in the format: `$Page_Title - NONE | (ID)`.
  5. Check if there are more tasks to process in the current tasklist.

### **Task 3: Sync Active Google Tasks**
For active tasks in Google Tasks:
- Check if the task is already marked as **Done** in Notion:
  - If **Yes**, mark the Google Task as completed.
  - If **No**, skip the task and log it as skipped.
- **Flow Steps:**
  1. Retrieve active Google Tasks.
  2. Check the status of the task in Notion.
  3. If marked as done in Notion, mark it as completed in Google Tasks.
  4. If not marked as done in Notion, skip and log the task.
  5. Check if there are more tasks to process in the current tasklist.

---

## **Notion to Google Sync Functions**

### **Page 1: Sync Notion Pages to Google Tasks**
Notion pages that do not have corresponding Google Tasks are created as tasks in Google.
- **Flow Steps:**
  1. Retrieve Notion pages since the last execution.
  2. For each page, check if a corresponding Google Task exists.
  3. If not, create a new task in Google Tasks using the page details.
  4. Log success or errors as appropriate.

---

## **Google to Notion Sync Diagram**

```mermaid
graph TD

    A((Start Sync Process)) --> B[Retrieve Google Tasklists]

    B --> C[Iterate over Tasklists]
    C --> D[Process Tasks for Sync]
    D --> TASK1[Retrieve completed tasks since last execution]
    D --> TASK2[Retrieve created tasks since last execution]
    D --> TASK3[Retrieve IDs from Active Google Tasks]
    DB1[(Github API)] --> DB2[Retrieve last Successful Workflow run]
    DB2 --> TASK1
    DB2 --> TASK2


    TASK1 --> TASK11[Mark Notion page as Done]
    TASK11 --> X{More tasks?}
    TASK2 --> TASK21[Create Notion Page]
    TASK21 --> TASK211[Retrieve ID from created page]
    TASK211 --> TASK2111[Rename Google Tasks]
    TASK2111 --> X
    TASK3 --> TASK31{Are they marked as Done in Notion?}
    TASK31 --> |Yes| TASK311[Mark Task as completed in Google Tasks]
    TASK31 --> |No| TASK312[Skip & log skipped task]
    TASK311 --> X
    TASK312 --> X

    X --> |Yes| D
    X --> |No| Y{More task lists?}
    Y --> |Yes| C
    Y --> |No| Z((End of Sync))
```

---

## **Notion to Google Sync Diagram**

```mermaid
graph TD

    A1[Retrieve Notion Pages] --> B1{Pages Retrieved?}
    B1 -->|No| D1[Log Error & Exit]
    B1 -->|Yes| E1[Parse Notion Pages]
    E1 --> F1[Fetch Google Task Lists]
    F1 --> G1[Initialize Progress Bar]
    G1 --> H1[Iterate Over Parsed Pages]

    H1 --> I1{Task Exists in Google Tasks?}
    I1 -->|Yes| J1[Log & Skip Page]
    I1 -->|No| K1[Ensure Task List Exists]

    K1 --> L1{Error Ensuring Task List?}
    L1 -->|Yes| M1[Create a new tasklist based on page tag]
    L1 -->|No| N1[Build Task Description]

    M1 --> N1

    N1 --> O1{Error Building Description?}
    O1 -->|Yes| P1[Log Error & Skip Page]
    newLines1[Create Task in Google Tasks]
    O1 -->|No| newLines1

    newLines1 --> R1{Error Creating Task?}
    R1 -->|Yes| S1[Log Error & Skip]
    R1 -->|No| T1[Log Success]

    J1 --> U1[Update Progress Bar]
    P1 --> U1
    S1 --> U1
    T1 --> U1

    U1 --> V1{More Pages?}
    V1 -->|Yes| H1
    V1 -->|No| W1[Sync Completed]
```
