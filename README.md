# CodeView

CodeView is a web-based developer community platform built to help programmers connect, share knowledge, discuss programming problems, and collaborate on projects.

The platform allows developers to interact through community posts and create or join project groups to work together.

## Features

- **User Authentication:** Developers can register, log in, and access their accounts.
- **Community Posts:** Users can create posts, like posts, comment, and share post links.
- **Project Groups:** Developers can create public or private project groups.
- **Group Membership:** Users can join public groups and access their group workspace.
- **Group Management:** Group creators become owners and administrators.
- **Group Workspace:** Members can view group information, descriptions, and other members.
- **Responsive Design:** The website supports desktop, tablet, and mobile screen sizes.

## Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Django | Web framework |
| PostgreSQL | Database |
| HTML | Webpage structure |
| CSS | Styling and responsive design |
| JavaScript | Frontend interactions |
| Git & GitHub | Version control |

## Project Structure

```text
CodeView/
├── config/          # Django project settings and URLs
├── home/            # Homepage
├── users/           # Registration and login
├── community/       # Posts, comments, likes, and groups
├── manage.py        # Django management commands
└── README.md        # Project documentation
```

## How to Run the Project

**1. Clone the repository**

```bash
git clone <your-repository-url>
cd <your-project-folder>
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Configure the database**

Create a PostgreSQL database and configure the database connection in Django's `config/settings.py`.

Set the database password using the environment variable expected by the project:

```bash
export CODEVIEW_DB_PASSWORD="your_database_password"
```

**5. Apply database migrations**

```bash
python manage.py migrate
```

**6. Start the development server**

```bash
python manage.py runserver
```

Open your browser and visit:

`http://127.0.0.1:8000/`

## How It Works

After registering and logging in, developers can publish posts, interact with other users, and explore project groups.

Developers can create their own groups or join existing public groups. Group members can access their group's workspace to view information and other members.

The application uses Django for backend operations and PostgreSQL to store user accounts, community posts, comments, likes, and group memberships.

---

**CodeView — Learn Together. Build Together. Grow Together.**
