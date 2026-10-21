# CodeView

**CodeView — A Developer Community and Collaborative Project Platform**

CodeView is a web application designed to bring developers together to share knowledge, discuss programming challenges, create project groups, and collaborate on software development.

The platform aims to provide a space where beginners and experienced developers can learn from one another, build projects together, and grow their technical skills.

## 1. Project Overview

CodeView combines a developer community with project-based collaboration.

Developers can create accounts, publish posts, interact with other developers, and create or join public project groups.

The long-term goal is to introduce collaborative coding tools, including a Code Board where group members can work on shared code without accidentally overwriting one another's changes.

**Project Status:** Active Development

## 2. Features

### User Authentication

- User registration
- User login
- Authenticated access to community features
- User identification on posts, comments, and project groups

### Developer Community

- Create and publish community posts
- View posts from other developers
- Like and unlike posts
- Comment on posts
- View post comments
- Share links to community posts

### Project Groups

- Create project groups
- Choose between public and private groups
- Browse available public groups
- Join public groups
- Prevent duplicate group memberships
- Enter groups after joining
- View group descriptions inside the group workspace
- View group members and their roles
- Automatically assign the group creator as an administrator

Private groups are only displayed to their existing members. Private-group invitations and approval workflows are planned for future development.

### Responsive User Interface

CodeView uses a dark-themed interface with green accents.

The frontend is designed to support:

- Desktop computers
- Laptops
- Tablets
- Mobile phones

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Django | Web framework and application logic |
| PostgreSQL | Relational database |
| HTML5 | Website structure |
| CSS3 | Styling and responsive layouts |
| JavaScript | Frontend interactions |
| Django ORM | Database operations |
| Git | Version control |
| GitHub | Source code hosting and collaboration |

## 4. Project Structure

```text
code-view/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── home/
│   └── ...
│
├── users/
│   └── ...
│
├── community/
│   ├── migrations/
│   ├── templates/
│   │   └── community/
│   │       ├── community.html
│   │       ├── groups.html
│   │       ├── create_group.html
│   │       └── group_detail.html
│   │
│   ├── static/
│   │   └── community/
│   │       ├── community.css
│   │       ├── community.js
│   │       └── groups.css
│   │
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
│
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

The structure above shows the main application components. Additional Django-generated and application files may also be present.

## 5. Installation and Setup

### Prerequisites

Ensure the following are installed:

- Python
- PostgreSQL
- Git
- pip

### Step 1: Clone the Repository

```bash
git clone <your-repository-url>
cd code-view
```

Replace the repository URL with the actual CodeView GitHub repository URL.

### Step 2: Create a Virtual Environment

```bash
python3 -m venv venv
```

Activate it on Linux or macOS:

```bash
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has not been created yet, generate it from your working virtual environment after reviewing the installed packages:

```bash
pip freeze > requirements.txt
```

### Step 4: Configure PostgreSQL

Create a PostgreSQL database and database user with the appropriate permissions.

Configure the Django database settings using your local environment variables.

For example, the project uses:

```bash
export CODEVIEW_DB_PASSWORD="your-local-database-password"
```

Other database settings must match your local Django configuration.

**Security:** Never commit database passwords, secret keys, `.env` files containing secrets, or virtual environment folders to GitHub.

### Step 5: Apply Database Migrations

```bash
python manage.py migrate
```

### Step 6: Run the Development Server

```bash
python manage.py runserver
```

Open:

`http://127.0.0.1:8000/`

The development server is intended for local development, not production deployment.

## 6. How CodeView Works

### Community Interaction

A developer signs in, publishes a post, and other developers can interact through likes and comments.

Community data is stored in PostgreSQL using Django models.

### Project Group Creation

A logged-in developer creates a project group by providing a group name, description, and privacy setting.

The developer becomes the group owner and is automatically added as an administrator.

### Joining Public Groups

Public groups are discoverable by logged-in developers.

When a developer clicks **Join Group**, CodeView creates a membership record. The developer can then enter the group's workspace.

The system prevents duplicate memberships.

### Group Privacy

Public groups are discoverable by other developers.

Private groups are visible only to their members in the current group listing.

Group descriptions are not displayed on the general listing page; they are shown inside the group workspace.

## 7. Planned Features

The following features are part of the development roadmap and are not yet fully implemented.

### Group Discussions

- Create discussion posts with titles
- Comment on group discussions
- Share development progress
- Ask group-specific programming questions

### Collaborative Code Board

- Shared code workspace for project members
- Persistent code storage
- One active editor at a time
- Editing queue for other members
- Comments and discussions around code
- Protection against unauthorized overwriting

### Group Management

- Invite developers to private groups
- Approve or reject membership requests
- Manage group administrators and members
- Define membership permissions

### Group Communication

- Group chat
- Meeting coordination
- Voice communication where technically feasible

## 8. Security and Access Control

CodeView uses Django authentication to identify developers.

Current access controls include:

- Login requirements for community and group actions
- CSRF protection for forms
- Membership checks before entering group workspaces
- Restrictions on joining private groups directly
- Database constraints preventing duplicate memberships

Additional authorization, testing, and security review will be needed before production deployment.

## 9. Development Roadmap

| Phase | Feature | Status |
|---|---|---|
| 1 | Django project setup | Completed |
| 2 | PostgreSQL integration | Completed |
| 3 | User registration and login | Completed |
| 4 | Community posts | Completed |
| 5 | Likes and comments | Completed |
| 6 | Project group creation | Completed |
| 7 | Public group joining | Completed |
| 8 | Group workspace | Initial version |
| 9 | Group discussions | Planned |
| 10 | Private group invitations | Planned |
| 11 | Collaborative Code Board | Planned |
| 12 | Group communication | Planned |
| 13 | Deployment and production hardening | Planned |

## 10. Project Goals

CodeView is being developed to:

1. Encourage collaboration among developers.
2. Help beginners learn through real development projects.
3. Provide a community for asking questions and sharing programming knowledge.
4. Make it easier for developers to find project collaborators.
5. Support organized group development with controlled editing permissions.

## 11. Contributing

CodeView is currently under active development.

A contribution workflow can include creating a feature branch, making changes, testing them, and submitting a pull request for review.

Contributors should follow the project's coding conventions and avoid committing sensitive configuration data.

## 12. License

A license has not yet been selected.

Until a license is added, public availability of the source code does not automatically grant permission to reuse, modify, or redistribute it.

---

**CodeView — Learn Together. Build Together. Grow Together.**
