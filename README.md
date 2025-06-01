# Smart-Time: Intelligent Time Management System

Smart-Time is an AI-powered time management application that helps users organize their meetings, tasks, and schedule efficiently. The application features a smart AI assistant that can understand natural language commands and help manage your time effectively.

## Features

- 🤖 AI-powered chat assistant for natural language scheduling
- 📅 Meeting management and scheduling
- ✅ Task management with priorities
- 📊 Dashboard for overview
- 🔄 Real-time updates
- 🌐 Responsive web interface
- 🔒 Secure authentication system

## Screenshots

### Login Page
![Log in](https://github.com/user-attachments/assets/7b8e2b94-7a41-4b28-aae1-e00b359a5fd0)


### Dashboard
![dashbord](https://github.com/user-attachments/assets/757314a7-9fee-4a47-b5ad-1daf8cc270fc)


### Meetings View
![meetings](https://github.com/user-attachments/assets/d3467200-35ee-4f12-afe0-8fabd10e4a42)


### Tasks Management
![Tasks](https://github.com/user-attachments/assets/25798deb-6789-43e7-a86f-f1c587ed574e)


### AI Chat Assistant
![chat](https://github.com/user-attachments/assets/1bc9f099-f1ea-4aa4-823d-6ecd02957d09)


## Technology Stack

### Frontend
- Vue.js 3 with Composition API
- Vite for build tooling
- Tailwind CSS for styling
- Axios for API communication

### Backend
- FastAPI (Python)
- SQLAlchemy for database management
- OpenAI integration for AI capabilities
- JWT authentication

## Getting Started

### Prerequisites
- Node.js (v14 or higher)
- Python 3.8 or higher
- OpenAI API key

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/smart-time.git
cd smart-time
```

2. Backend Setup
```bash
cd smart-time-backedn
python -m venv venv
# Activate virtual environment (Windows)
.\venv\Scripts\activate
pip install -r requirements.txt

# Create and configure environment variables
New-Item -Path ".env" -Type File
```

Configure your .env file with the following variables:
```env
DATABASE_URL=mysql://username:password@localhost/smart_time_db
OPENAI_API_KEY=your_openai_api_key_here

```

Make sure to:
- Replace `username` and `password` with your MySQL credentials
- Add your actual OpenAI API key
- Create the database 'smart_time_db' in MySQL using:
  ```sql
  CREATE DATABASE smart_time_db;
  ```

3. Frontend Setup
```bash
cd smart-time-frontend
npm install
```

### Running the Application

1. Start the backend server
```bash
cd smart-time-backedn
uvicorn app.main:app --reload
```

2. Start the frontend development server
```bash
cd smart-time-frontend
npm run dev
```

## Features in Detail

### AI Assistant Capabilities
- Natural language meeting scheduling
- Task management through conversation
- Schedule queries and availability checks
- Intelligent time slot suggestions

### Meeting Management
- Create, edit, and delete meetings
- Calendar view with drag-and-drop
- List view for quick overview
- Conflict detection
- Location and participant management

### Task Management
- Priority-based task organization
- Due date tracking
- Status updates
- Task filtering and sorting

## Contributing

We welcome contributions to Smart-Time! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the AI capabilities
- Vue.js team for the excellent framework
- FastAPI team for the powerful backend framework
- All contributors and users of Smart-Time

---
*Note: To add screenshots, create a `screenshots` folder in your project root and add your application screenshots with the corresponding names (login.png, dashboard.png, etc.)*
