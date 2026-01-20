# Check Attendance IoT

An end-to-end RFID-based attendance system integrating embedded hardware, cloud infrastructure,
and a web-based management dashboard to automate attendance tracking and reporting.

## Features
- RFID-based attendance recording using ESP32
- Real-time data synchronization with cloud database
- Secure database connection using SSL certificates
- Web dashboard for attendance monitoring and reporting
- RESTful API for device-to-server communication

## System Overview
The system consists of an IoT device that reads RFID cards and sends attendance data
to a cloud-hosted backend server. The backend processes, stores, and exposes data
through REST APIs for web-based management.

---

## Tech Stack

### Hardware
- ESP32 – main microcontroller
- RFID RC522 – card reader
- RTC DS1302 – time synchronization
- I2C Display – local device display

### Frontend
- HTML5 – page structure
- CSS3 – layout and styling
- JavaScript (ES6) – client-side interactions

### Backend
- Django – core backend framework
- Django REST Framework – REST API development
- Python – business logic implementation

### Database
- PostgreSQL – cloud-hosted relational database (Aiven)

### Deployment
- AWS EC2 – application hosting
- Nginx – reverse proxy and static file serving
- Gunicorn – WSGI server

### Tools
- Git & GitHub – version control

---

## Architecture
- Django MVT architecture
- RESTful API design
- Secure device-to-server communication
- Separation of frontend and backend concerns

---

## Installation & Configuration

### Prerequisites
- Python 3.9+
- PostgreSQL (cloud-hosted)
- Aiven account (or any free cloud database provider)

### Database Setup
1. Create a PostgreSQL service on Aiven (or another provider).
2. Download the SSL certificate (`ca.pem`) provided by the service.
3. Place the certificate inside the `certs/` directory: certs/ca.pem


### Environment Variables
Create a `.env` file and configure the database connection:
```env
#debug mode for development
DEBUG=True

#SECRET KEY FIELD IN Settings.py
SECRET_KEY=django-insecure-2@keg%)x^2ix%tt1*%cr#iot!+q2==qu)fmv+cgn)0j5-e++k#

#Allowed hosts configuration
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.63

#Database configuration. Please add the database configuration from Aiven in order to use online database.
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=your_db_port
