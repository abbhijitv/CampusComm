# 🎓 Campus Comm

**AI-Powered Campus Intelligence**

Campus Comm is a hackathon project that transforms scattered campus reports into structured, actionable intelligence.

Students can submit reports about issues such as Wi-Fi outages, broken facilities, transportation problems, accessibility concerns, or safety issues. Campus Comm uses **Snowflake + Snowflake Cortex AI** to analyze those reports, detect emerging patterns, and present campus-wide insights through a **Streamlit dashboard**.

---

## 💡 The Problem

Campus issues are often reported through many disconnected channels.

For example:

- A student reports broken Wi-Fi at Hayden Library.
- Another student reports the same issue 10 minutes later.
- Several more students experience the problem.
- Each report may appear to be an isolated complaint.

Campus Comm combines these reports to detect that they may represent a larger campus issue.

---

## 🚀 Our Solution

Campus Comm creates the following pipeline:

```text
Student Report
      ↓
Streamlit
      ↓
Snowflake Cortex AI
      ↓
Classify + Summarize
      ↓
Snowflake Database
      ↓
SQL Pattern Detection
      ↓
Emerging Campus Issue
      ↓
Campus Comm Dashboard
```

Example:

```text
"Wi-Fi isn't working on the second floor of Hayden."
                         ↓
                  Snowflake AI
                         ↓
Category: Technology
Subcategory: Wi-Fi
Severity: High
Location: Hayden Library
                         ↓
                 Stored in Snowflake
                         ↓
Several similar reports detected
                         ↓
🚨 Emerging Issue:
Hayden Library Wi-Fi Outage
```

---

## ✨ Main Features

### 📢 Campus Issue Reporting

Students can submit campus problems through a simple interface.

Reports can include issues related to:

- Technology
- Facilities
- Transportation
- Safety
- Accessibility
- Campus services
- Other campus concerns

---

### 🤖 AI Report Analysis

Snowflake Cortex AI analyzes free-text reports and extracts structured information such as:

```text
Category
Subcategory
Severity
Summary
```

For example:

```text
Input:

"The Wi-Fi keeps disconnecting on the second floor of Hayden."

Output:

Category: Technology
Subcategory: Wi-Fi
Severity: High
Summary: Students are experiencing Wi-Fi connectivity problems at Hayden Library.
```

---

### 🚨 Emerging Issue Detection

Campus Comm groups recent reports by factors such as:

```text
Location
+
Category
+
Time
```

When several related reports occur, Campus Comm can surface them as an emerging issue.

Example:

```text
6 reports
+
Hayden Library
+
Technology
+
Last 24 hours

        ↓

🚨 Emerging Issue

Hayden Library Wi-Fi Problems
```

---

### ✨ AI Campus Briefing

Campus Comm can analyze recent campus activity and generate a short operations briefing.

Example:

```text
Campus activity indicates an elevated number of technology
reports at Hayden Library, primarily involving Wi-Fi
connectivity.

Several transportation reports also indicate congestion near
Apache Parking Garage.

Facilities reports remain relatively low.
```

---

### 💬 Ask Campus Comm

Users can ask natural-language questions about campus reports.

Example:

```text
Question:

What's happening at Hayden Library?
```

Campus Comm can analyze the stored reports and provide an answer based on the available campus data.

---

## 🛠 Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Frontend dashboard |
| Snowflake | Cloud database and analytics |
| Snowflake Cortex AI | LLM-powered report analysis |
| Snowflake SQL | Pattern detection and aggregation |
| Pandas | Data handling |
| python-dotenv | Environment variable management |
| VS Code | Development environment |

---

## 📁 Project Structure

```text
CampusComm/
│
├── app.py
│
├── snowflake_client.py
│
├── ai.py
│
├── analytics.py
│
├── requirements.txt
│
├── README.md
│
├── .env
├── .env.example
├── .gitignore
│
├── data/
│   └── campus_reports.csv
│
├── sql/
│   ├── setup.sql
│   └── queries.sql
│
└── assets/
    └── architecture.png
```

---

## 📄 File Responsibilities

### `app.py`

Main Streamlit application.

Responsible for:

- Campus Comm dashboard
- Report submission
- Dashboard metrics
- Emerging issues
- AI Campus Briefing
- Ask Campus Comm
- Recent reports

### `snowflake_client.py`

Handles communication between Python and Snowflake.

Responsibilities include:

```text
Connecting to Snowflake
Saving reports
Reading reports
Retrieving dashboard statistics
```

### `ai.py`

Contains Campus Comm's AI functionality.

Responsibilities include:

```text
Report classification
Severity detection
Report summarization
Campus briefing generation
Campus Q&A
```

### `analytics.py`

Detects patterns across campus reports.

Example:

```text
Multiple reports
      ↓
Same location
      ↓
Same category
      ↓
Recent time window
      ↓
Emerging Issue
```

### `sql/setup.sql`

Creates the Snowflake database tables required by Campus Comm.

### `sql/queries.sql`

Contains SQL queries used for analytics, testing, and development.

### `data/campus_reports.csv`

Contains synthetic campus reports used for testing and demonstrating the system.

---

## ❄️ Snowflake Architecture

Campus Comm uses a shared Snowflake environment.

```text
             CAMPUS COMM TEAM
                    │
                    ▼
             Snowflake Account
                    │
                    ▼
            CAMPUS_COMM_DB
                    │
                  PUBLIC
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   CAMPUS_REPORTS          INCIDENTS
```

Team members use their own Snowflake users while working with the same shared database.

---

## 🗃 Database Structure

### `CAMPUS_REPORTS`

Stores individual campus reports.

```text
REPORT_ID
CREATED_AT
REPORT_TEXT
LOCATION
CATEGORY
SUBCATEGORY
SEVERITY
SUMMARY
STATUS
```

### `INCIDENTS`

Stores detected campus incidents.

```text
INCIDENT_ID
CREATED_AT
TITLE
LOCATION
CATEGORY
SEVERITY
REPORT_COUNT
SUMMARY
STATUS
```

---

## 👥 Team Development

The project can be developed simultaneously by splitting responsibilities.

### Person 1 — Snowflake / Backend

Files:

```text
sql/setup.sql
snowflake_client.py
.env.example
```

Responsibilities:

- Snowflake database
- Tables
- Database connection
- Insert/query functions

### Person 2 — AI / Analytics

Files:

```text
ai.py
analytics.py
sql/queries.sql
data/campus_reports.csv
```

Responsibilities:

- Cortex AI integration
- Report classification
- AI summaries
- Emerging issue detection
- Synthetic demo data

### Person 3 — Frontend

Files:

```text
app.py
assets/
```

Responsibilities:

- Streamlit dashboard
- Report form
- Dashboard metrics
- Emerging issue cards
- Campus Briefing UI
- Ask Campus Comm UI

### Person 4 — Presentation / Pitch / Integration Support

Files:

```text
README.md
assets/
presentation materials

---

## ⚙️ Local Setup

### 1. Clone/open the project

Open the `CampusComm` folder in VS Code.

### 2. Create a virtual environment

Mac/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

The project currently requires:

```text
streamlit
snowflake-connector-python
python-dotenv
pandas
```

---

## 🔐 Environment Variables

Each developer should create their own local `.env` file.

Example:

```env
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=CAMPUS_COMM_DB
SNOWFLAKE_SCHEMA=PUBLIC
```

Use `.env.example` as the template.

### ⚠️ Important

Never commit:

```text
.env
.venv/
```

These are excluded through `.gitignore`.

Do **not** share Snowflake passwords or other secrets through GitHub.

---

## ▶️ Running Campus Comm

Make sure your virtual environment is active:

```bash
source .venv/bin/activate
```

Then start Streamlit:

```bash
streamlit run app.py
```

Streamlit will provide a local URL for the application.

---

## 🧪 Demo Scenario

A strong demo scenario is a campus Wi-Fi outage.

Several synthetic reports are stored:

```text
"Wi-Fi isn't working at Hayden."

"Internet keeps disconnecting on the second floor."

"I can't connect to the Hayden wireless network."

"Hayden internet has been down for 20 minutes."

"Wi-Fi stopped working while I was studying."
```

Campus Comm detects:

```text
Location: Hayden Library
Category: Technology
Reports: 5+
```

and surfaces:

```text
🚨 EMERGING ISSUE

Hayden Library Wi-Fi Problems
Multiple related reports detected
```

The presenter can then ask:

```text
What's happening at Hayden Library?
```

and demonstrate Campus Comm's AI-powered response.

---

## 🎯 MVP

Our minimum viable product is complete when this entire pipeline works:

```text
Submit Report
      ↓
Snowflake Cortex AI
      ↓
Classify Report
      ↓
Store in Snowflake
      ↓
Detect Related Reports
      ↓
Surface Emerging Issue
      ↓
Generate Campus Briefing
```

Additional features should be added only after this end-to-end workflow is reliable.

---

## 🔮 Future Improvements

Potential future features include:

- Interactive campus map
- Real-time notifications
- Campus department dashboards
- Incident resolution tracking
- Authentication
- Anonymous student reporting
- Historical trend analysis
- Automatic department routing
- Mobile interface
- Advanced semantic clustering
- Integration with official university systems

---

## 🏆 Hackathon Goal

Campus Comm demonstrates how AI can turn fragmented campus reports into useful operational intelligence.

Instead of treating every report as an isolated complaint, Campus Comm helps identify the larger patterns behind what is happening across campus.

**Campus Comm — Know what's happening on campus, before it becomes a bigger problem.**