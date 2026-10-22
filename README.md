# CodeView 🚀

### Code Together. Learn Together. Build Together.

CodeView is a collaborative software development platform where developers can write code, communicate with teammates, use AI assistants, preview applications, review contributions, and manage GitHub projects in one workspace.

## 🎯 Project Purpose

CodeView aims to make software development easier for students, programming fellows, and professional development teams.

Instead of switching between multiple applications for coding, meetings, AI assistance, and code reviews, developers can work together inside CodeView.

## ✨ Features

### 1. User Authentication
- Register and log in.
- Manage developer profiles.
- Access personal and group workspaces.

### 2. Project Groups

CodeView supports three group types:

**🌍 Public Community**
- Anyone can discover and join.
- Ask programming questions and share knowledge.
- Participate in discussions and group chat.
- Share code snippets, files, and voice notes.

**🔒 Restricted Community**
- Publicly discoverable.
- Administrators control posting and participation.
- Members can discuss programming topics and share resources.
- Supports group chat and voice notes.

**🔐 Private Development Group**
- Invitation or approval required.
- Maximum of **10 members, including the group owner**.
- Full access to CodeView's collaborative development features.
- Group administrators manage members and permissions.

### 3. Group Chat
- Send real-time text messages.
- Record and send voice notes.
- Share files and code snippets.
- Reply to messages.
- Receive group notifications.

### 4. Developer Workspace
- VS Code-like code editor.
- Project file explorer.
- Create and edit files.
- Work on individual Git branches.
- Save code and view changes.
- Access a terminal and console.

### 5. AI Assistant
- Choose ChatGPT, Claude, Gemini, or DeepSeek.
- Open official AI login and registration pages.
- Connect supported AI providers securely.
- Chat with AI directly inside CodeView.
- Explain code, find bugs, and generate tests.
- Review AI-generated changes.
- Accept or reject changes using **Insert Suggestion**.
- Switch AI providers.

AI autocomplete is intentionally excluded.

### 6. Live Preview and Code Execution
- Preview frontend changes while coding.
- Display HTML, CSS, and JavaScript results.
- Support modern frontend projects.
- Run supported programs in isolated environments.
- Display errors and console output.
- Share application previews with teammates.

### 7. Meeting Room
- Group video calls.
- Group voice calls.
- Present code during meetings.
- Share live application previews.
- Discuss code and request editing control.
- Continue coding and using AI during meetings.

**Private Development Group Meeting Rules:**
- Only **one active video meeting per group**.
- Maximum of **10 participants per meeting**.
- Only authorized group members can join.
- Members join an existing meeting instead of creating another.
- A new meeting can start after the previous meeting ends.

### 8. GitHub Integration
- Connect GitHub repositories.
- Browse repository files.
- Create and switch branches.
- Commit and push changes.
- Create pull requests.
- Review and merge approved contributions.
- Respect GitHub repository permissions.

### 9. Code Review
- Mark completed work as **Code Ready**.
- Notify teammates.
- Present code for review.
- Suggest corrections.
- Track approval and merge status.

### 10. Project Dashboard
- Assign tasks.
- Track developer progress.
- View contributions.
- Monitor completed and pending reviews.

## 💻 Supported Languages

**Programming languages:**

Python, JavaScript, TypeScript, Go, Java, C++, C#, and PHP.

**Additional web technologies:**

HTML, CSS, and SQL.

Language-specific execution and previews require their appropriate runtime environments.

## 🛠 Technology Stack

| Technology | Purpose |
|---|---|
| Python + Django | Backend application |
| PostgreSQL | Database |
| HTML, CSS, JavaScript | Frontend |
| Monaco Editor | Code editing |
| Django Channels + WebSockets | Real-time communication |
| WebRTC | Video and voice calls |
| Git + GitHub API | Repository integration |
| AI Provider APIs | Integrated AI assistance |
| Docker / isolated runners | Secure code execution |

## ⚙️ Installation (Ubuntu)

### 1. Clone the project

```bash
git clone <repository-url>
cd CODEVIEW
```

Replace `<repository-url>` with the actual repository address.

### 2. Create a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Start PostgreSQL:

```bash
sudo systemctl enable --now postgresql
```

Check installation:

```bash
psql --version
```

### 5. Create the PostgreSQL database

Open PostgreSQL:

```bash
sudo -u postgres psql
```

Create the database user:

```sql
CREATE USER codeview_user WITH PASSWORD 'replace_with_a_strong_password';
```

Create the database:

```sql
CREATE DATABASE codeview_db OWNER codeview_user;
```

Exit:

```sql
\q
```

### 6. Configure Django

Set these database values in your local Django environment configuration:

```text
DB_NAME=codeview_db
DB_USER=codeview_user
DB_PASSWORD=<your_database_password>
DB_HOST=127.0.0.1
DB_PORT=5432
```

The Django settings must read these environment variables.

Keep passwords and API keys out of Git.

### 7. Run migrations

```bash
python manage.py migrate
```

### 8. Start the application

```bash
python manage.py runserver
```

Open the local development server in your browser.

## 🔐 Security

- Only authorized group members can access private workspaces.
- Private development groups are limited to 10 members.
- Only one video meeting can be active per private development group.
- Meetings are restricted to authorized members.
- GitHub and AI credentials are stored securely.
- AI suggestions require developer approval before insertion.
- Code execution runs in isolated environments.
- Repository permissions and branch protections are respected.

## 📌 Development Status

**CodeView is under active development.**

The features above describe the complete project scope. Some are already partially implemented, while others are planned.

## 🎯 Project Vision

To create a single platform where developers can:

**Write Code → Use AI → Preview → Communicate → Present → Review → Push → Merge**

**CodeView — Build Better, Together.**