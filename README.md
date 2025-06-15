# Red Cross Kenya Disaster Management System

A comprehensive disaster management system for Red Cross Kenya that enables efficient incident reporting, real-time alerts, and resource management.

## Features

- **Incident Reporting System**
  - Location-based incident reporting with map integration
  - Photo upload capability for incident documentation
  - Real-time incident tracking

- **Alert System**
  - Real-time SMS alerts using Twilio API
  - Customizable alert templates
  - Multi-channel notification system

- **Resource Management**
  - Intelligent resource allocation based on incident type
  - Resource tracking and inventory management
  - Automated resource deployment suggestions

- **User Management**
  - JWT-based authentication
  - Role-based access control (Public, Responders, Admins)
  - Secure user sessions

## Technical Stack

### Frontend
- HTML5, CSS3, JavaScript
- Responsive design
- Modern UI/UX principles

### Backend
- Python (Flask)
- MongoDB
- RESTful API architecture

### Security
- HTTPS implementation
- Data encryption
- JWT authentication
- Role-based access control

## Project Structure

```
redcross_kenya/
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── utils/
├── docs/
│   ├── api_docs/
│   └── erd/
└── tests/
```

## Setup Instructions

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
4. Configure MongoDB connection
5. Run the application:
   ```bash
   python run.py
   ```

## API Documentation

Detailed API documentation is available in the `docs/api_docs` directory.

## Database Schema

The Entity Relationship Diagram (ERD) is available in the `docs/erd` directory.

## Security

- All sensitive data is encrypted
- HTTPS is enforced
- JWT tokens for authentication
- Role-based access control
- Input validation and sanitization

## License

This project is proprietary and confidential. All rights reserved by Red Cross Kenya.

## Contact

For support and inquiries, please contact the Red Cross Kenya IT Department. 