# Document Tracking System

![Document Tracking System Logo](static/img/document.svg)

A secure and efficient platform for managing academic document submissions and tracking their processing status in real-time.

## 📋 Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Admin Access](#admin-access)
- [System Requirements](#system-requirements)
- [Directory Structure](#directory-structure)
- [Technologies Used](#technologies-used)
- [Screenshots](#screenshots)
- [License](#license)
- [Support](#support)

## ✨ Features

### For Students
- Secure account creation and authentication
- Document submission with support for multiple file formats
- Real-time tracking of application status
- Automatic notifications for status changes
- Profile management and document history
- Payment status tracking

### For Administrators
- Comprehensive dashboard with analytics
- Application and document review system
- User management capabilities
- Detailed reporting with export functionality
- System configuration and settings
- Activity logs for audit trails

## 🚀 Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/documenttrackingsystem.git
   cd documenttrackingsystem
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Initialize the database:
   ```
   python app.py
   ```

## ⚙️ Configuration

### Email Settings
Update the email configuration in `app.py` to enable notifications:

```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Replace with actual email
app.config['MAIL_PASSWORD'] = 'your-password'  # Replace with actual password
```

### File Upload Settings
The system currently supports:
- Maximum file size: 16MB
- Accepted formats: PDF, JPG, PNG

To modify these settings, update the following in `app.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
```

## 📝 Usage

### Student Workflow
1. Register for an account
2. Create a new application
3. Upload required documents
4. Monitor application status
5. Address feedback if documents are rejected
6. Receive notifications on status changes

### Administrator Workflow
1. Review submitted applications
2. Verify uploaded documents
3. Approve or reject applications
4. Provide feedback for rejected documents
5. Generate reports on system usage
6. Manage user accounts

## 👑 Admin Access

To access the administrator dashboard, use these credentials:

- **Username**: admin
- **Email**: admin@example.com
- **Password**: admin123

> **⚠️ IMPORTANT**: Change the default admin password immediately after first login for security purposes!

## 💻 System Requirements

- Python 3.8+
- SQLite3 (default) or PostgreSQL/MySQL for production
- Modern web browser (Chrome, Firefox, Safari, Edge)
- 512MB+ of RAM
- 1GB+ of free disk space

## 📁 Directory Structure

```
documenttrackingsystem/
├── static/                  # Static assets
│   ├── css/                 # CSS files
│   ├── js/                  # JavaScript files
│   ├── uploads/             # User uploaded files
│   └── img/                 # System images
├── templates/               # HTML templates
│   ├── admin/               # Admin interface templates
│   └── ...                  # Other templates
├── app.py                   # Main application file
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## 🛠️ Technologies Used

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite
- **Frontend**: Bootstrap 5, Tailwind CSS, Font Awesome
- **Authentication**: Flask-Login
- **Email**: Flask-Mail
- **Charts**: Chart.js

## 📸 Screenshots

### Student Dashboard
![Student Dashboard](static/img/student-dashboard.png)

### Admin Dashboard
![Admin Dashboard](static/img/admin-dashboard.png)

### Document Submission
![Document Submission](static/img/document-submission.png)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For questions, issues, or feature requests, please contact:

- Email: support@documenttracking.com
- GitHub Issues: [Create an issue](https://github.com/yourusername/documenttrackingsystem/issues)

---

&copy; 2023 Document Tracking System. All rights reserved.
