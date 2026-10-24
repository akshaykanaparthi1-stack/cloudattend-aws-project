# CloudAttend — Cloud-Based Student Attendance Management System
**Enterprise Cloud Computing Solution | Production Edition**

![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue?logo=python)
![Framework](https://img.shields.io/badge/Framework-Flask%203.x-black?logo=flask)
![Database](https://img.shields.io/badge/Database-SQLite%203%20(RDS%20Ready)-003B57?logo=sqlite)
![Production](https://img.shields.io/badge/Server-Gunicorn%20%2B%20Nginx-009639?logo=nginx)
![Cloud](https://img.shields.io/badge/Deployment-AWS%20EC2%20(Ubuntu)-FF9900?logo=amazonec2)
![Tests](https://img.shields.io/badge/Tests-35%20Passed%20(100%25)-success?logo=pytest)

---

## Executive Summary & System Overview

**CloudAttend** is a production-grade, secure, cloud-based web application designed for academic institutions, universities, and training bootcamps to track, evaluate, and export student attendance data.

Built with an enterprise cloud-first approach, CloudAttend bridges modern web application engineering with scalable cloud infrastructure on Amazon Web Services (AWS EC2).

### Key Highlights
- **Executive Dashboard:** Live statistics for enrolled students, present, absent, and late counts, overall attendance percentages, and dynamic 7-day trend visualizations.
- **Robust Student Management:** Full CRUD operations (Add, View Dossier, Edit, Search, and Delete with cascade cleanup).
- **Interactive Attendance Marking:** Cohort-based attendance roster with rapid bulk toggles (*"Mark All Present"*), custom remarks, and strict duplicate-prevention constraints.
- **Reporting & CSV Export:** Comprehensive daily and monthly reports, filterable by date, class, section, student name, and status, with instant RFC 4180 CSV export.
- **Enterprise-Grade Security:**
  - Salted PBKDF2 cryptographic password hashing (zero plaintext storage).
  - Synchronizer Token CSRF protection for all state-changing requests.
  - Server-side parameter validation and sanitized parameterized SQL queries.
  - Hardened HTTP response headers (`X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`).
  - Session cookie security (`HttpOnly`, `SameSite=Lax`).
- **Cloud-Ready Architecture:** Designed for continuous deployment behind **Nginx** reverse proxy and **Gunicorn** WSGI workers on an **Ubuntu Linux AWS EC2** instance with systemd reboot survival.

---

## System Architecture

```text
               +--------------------------------------------------+
               |                  Client Browser                  |
               +--------------------------------------------------+
                                        |
                             HTTP / HTTPS (Port 80/443)
                                        |
                                        v
               +--------------------------------------------------+
               |            AWS EC2 Security Group                |
               |   - Port 22 (SSH): Restricted to My IP           |
               |   - Port 80 (HTTP): 0.0.0.0/0                    |
               |   - Port 443 (HTTPS): 0.0.0.0/0                  |
               +--------------------------------------------------+
                                        |
                                        v
               +--------------------------------------------------+
               |               Nginx Web Server                   |
               |  - Reverse Proxy (127.0.0.1:8000)                |
               |  - Direct High-Speed Static Asset Delivery       |
               |  - Gzip Compression & Buffer Handling            |
               +--------------------------------------------------+
                                        |
                                        v
               +--------------------------------------------------+
               |             Gunicorn WSGI Workers                |
               |    (Managed by systemd: cloudattend.service)     |
               +--------------------------------------------------+
                                        |
                                        v
               +--------------------------------------------------+
               |             Flask Application Core               |
               |  - Route Handlers & Input Validation             |
               |  - CSRF Verification & Auth Middleware           |
               |  - Jinja2 Responsive UI Rendering                |
               +--------------------------------------------------+
                                        |
                                        v
               +--------------------------------------------------+
               |           Persistent Storage Tier                |
               |  Current: SQLite 3 with Foreign Keys & WAL       |
               |  Target : Amazon RDS (PostgreSQL / MySQL)        |
               +--------------------------------------------------+
```

---

## Directory Structure

```text
cloudattend/
├── app.py                     # Main Flask application, routes, and security middleware
├── config.py                  # Environment-driven configuration classes
├── database.py                # Database connection, migrations, CLI & fictional seeding
├── schema.sql                 # Relational database schema with constraints and indices
├── wsgi.py                    # Production WSGI entry point for Gunicorn
├── requirements.txt           # Python application dependencies
├── .env.example               # Example environment variable template
├── .gitignore                 # Version control exclusions
├── README.md                  # Comprehensive technical documentation & deployment guide
├── deploy/
│   ├── cloudattend.service    # Systemd daemon service unit file
│   └── nginx.conf             # Nginx reverse proxy configuration
├── static/
│   ├── css/
│   │   └── style.css          # Premium Navy/Blue/Purple UI theme & responsive grid
│   └── js/
│       ├── main.js            # UI interactions, mobile sidebar drawer, auto-dismiss alerts
│       ├── attendance.js      # Bulk marking shortcuts and live counter updates
│       └── charts.js          # Zero-dependency High-DPI Canvas chart renderer
├── templates/
│   ├── base.html              # Core application layout and navigation
│   ├── login.html             # Secure administrator login screen
│   ├── dashboard.html         # Executive overview dashboard with KPI cards and charts
│   ├── system.html            # Cloud architecture and environment status page
│   ├── error.html             # Custom HTTP error pages (403, 404, 500)
│   ├── students/
│   │   ├── index.html         # Searchable, filterable student directory
│   │   ├── add.html           # Student enrollment form
│   │   ├── edit.html          # Student modification form
│   │   └── view.html          # Individual student dossier and attendance log
│   └── attendance/
│       ├── mark.html          # Cohort attendance recording sheet
│       └── history.html       # Daily and monthly reports with CSV export
└── tests/
    ├── __init__.py
    ├── conftest.py            # Pytest test fixtures (isolated DB, auth client, seed data)
    ├── test_auth.py           # Login, logout, session protection, unauthorized redirects
    ├── test_students.py       # Student CRUD, validation, unique ID checks, search
    ├── test_attendance.py     # Attendance marking, duplicate prevention, constraints
    ├── test_reports.py        # Daily/monthly filtering, percentage math, CSV format
    ├── test_security_and_edge_cases.py  # Password hashes, CSRF enforcement, empty datasets
    └── test_ui_smoke.py       # End-to-end template rendering verification
```

---

## Local Development Setup

Follow these step-by-step instructions to run CloudAttend locally on Windows, macOS, or Linux:

### Step 1: Clone the Repository & Enter Directory
```bash
git clone https://github.com/akshaykanaparthi1-stack/cloudattend-aws-project.git
cd cloudattend-aws-project
```

### Step 2: Create and Activate a Python Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```
*(The default settings in `.env.example` work out of the box for local development).*

### Step 5: Initialize and Seed the Database
CloudAttend includes an automated fictional dataset with 18 fictional students across 3 cohorts and a week of realistic attendance records.

```bash
flask init-db
flask seed-db
```

### Step 6: Launch the Development Server
```bash
python app.py
```
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

### Default Demo Credentials
- **Username:** `admin`
- **Password:** `Admin@Cloud2026`
*(Note: Change these credentials before deploying to a public server).*

---

## Running the Automated Test Suite

CloudAttend includes a comprehensive test suite of **35 automated test cases** covering authentication, authorization, CRUD logic, duplicate prevention, edge cases, reporting math, and security.

Run pytest with verbose output:
```bash
python -m pytest -v
```

### Actual Test Execution Results
```text
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.1.1
collected 35 items

tests/test_attendance.py::test_mark_attendance_page_loads PASSED         [  2%]
tests/test_attendance.py::test_mark_attendance_post_successful PASSED    [  5%]
tests/test_attendance.py::test_duplicate_attendance_prevention_and_update PASSED [  8%]
tests/test_attendance.py::test_database_unique_constraint_enforced PASSED [ 11%]
tests/test_attendance.py::test_invalid_date_rejected PASSED              [ 14%]
tests/test_auth.py::test_login_page_renders PASSED                       [ 17%]
tests/test_auth.py::test_login_successful PASSED                         [ 20%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 22%]
tests/test_auth.py::test_login_nonexistent_user PASSED                   [ 25%]
tests/test_auth.py::test_logout PASSED                                   [ 28%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/] PASSED [ 31%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/dashboard] PASSED [ 34%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/students] PASSED [ 37%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/students/add] PASSED [ 40%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/attendance/mark] PASSED [ 42%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/attendance/reports] PASSED [ 45%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/attendance/export-csv] PASSED [ 48%]
tests/test_auth.py::test_unauthorized_access_redirects_to_login[/system] PASSED [ 51%]
tests/test_reports.py::test_reports_daily_view PASSED                    [ 54%]
tests/test_reports.py::test_reports_monthly_view PASSED                  [ 57%]
tests/test_reports.py::test_reports_status_filtering PASSED              [ 60%]
tests/test_reports.py::test_zero_records_calculation_handling PASSED     [ 62%]
tests/test_reports.py::test_export_csv_headers_and_content PASSED        [ 65%]
tests/test_security_and_edge_cases.py::test_password_stored_as_secure_hash PASSED [ 68%]
tests/test_security_and_edge_cases.py::test_csrf_protection_blocks_forged_requests PASSED [ 71%]
tests/test_security_and_edge_cases.py::test_export_csv_empty_dataset PASSED [ 74%]
tests/test_students.py::test_list_students PASSED                        [ 77%]
tests/test_students.py::test_add_student_successful PASSED               [ 80%]
tests/test_students.py::test_add_student_duplicate_id_prevented PASSED   [ 82%]
tests/test_students.py::test_add_student_validation_errors PASSED        [ 85%]
tests/test_students.py::test_edit_student PASSED                         [ 88%]
tests/test_students.py::test_delete_student PASSED                       [ 91%]
tests/test_students.py::test_search_and_filter_students PASSED           [ 94%]
tests/test_students.py::test_view_student_dossier PASSED                 [ 97%]
tests/test_ui_smoke.py::test_smoke_all_pages_rendered_with_seeded_data PASSED [100%]

============================= 35 passed in 6.26s ==============================
```

---

## AWS EC2 Deployment Guide (Ubuntu Linux)

Follow these beginner-friendly, production-ready steps to deploy CloudAttend to Amazon EC2:

### 1. Launching an Ubuntu EC2 Instance
1. Log in to the [AWS Management Console](https://console.aws.amazon.com/ec2/).
2. In the top navigation bar, choose your nearest AWS Region (e.g., `us-east-1` or `ap-south-1`).
3. Navigate to **EC2 Dashboard** and click **Launch Instance**.
4. Configure instance parameters:
   - **Name:** `CloudAttend-Production-Server`
   - **OS Image (AMI):** `Ubuntu Server 24.04 LTS (HVM), SSD Volume Type` (or `Ubuntu 22.04 LTS`).
   - **Architecture:** `64-bit (x86)`
   - **Instance Type:** `t2.micro` (or `t3.micro`), eligible for AWS Free Tier.
   - **Key Pair:** Choose an existing key pair or click **Create new key pair** (Type: `RSA`, Format: `.pem`). Download and save `cloudattend-key.pem` securely on your computer.

### 2. Configuring the Security Group
Under **Network Settings**, click **Edit** and configure the inbound rules as follows:

| Type | Protocol | Port Range | Source | Description |
| :--- | :--- | :--- | :--- | :--- |
| **SSH** | TCP | `22` | **My IP** | **Critical Security Practice:** Restricts shell access strictly to your current public IP address. |
| **HTTP** | TCP | `80` | `0.0.0.0/0` (Anywhere) | Allows public web browser traffic to CloudAttend. |
| **HTTPS** | TCP | `443` | `0.0.0.0/0` (Anywhere) | Allows encrypted SSL/TLS traffic once certbot is enabled. |

Under **Configure Storage**, keep the default 8 GB or 20 GB **gp3 General Purpose SSD** volume. Click **Launch Instance**.

### 3. Connecting via SSH
On your local machine, open terminal / PowerShell:
```bash
# Set strict permissions on your downloaded private key (Linux / macOS)
chmod 400 cloudattend-key.pem

# Connect to your EC2 instance (replace with your instance's Public IPv4 DNS or IP)
ssh -i "cloudattend-key.pem" ubuntu@ec2-XX-XX-XX-XX.compute-1.amazonaws.com
```

### 4. Installing Python, Nginx, and System Packages
Once connected to the Ubuntu shell:
```bash
# 1. Update package lists and upgrade existing system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3, pip, venv, Git, and Nginx
sudo apt install -y python3 python3-pip python3-venv git nginx

# 3. Verify installations
python3 --version
nginx -v
```

### 5. Deploying the Application & Configuring Gunicorn
```bash
# 1. Clone repository into home directory
cd /home/ubuntu
git clone https://github.com/akshaykanaparthi1-stack/cloudattend-aws-project.git cloudattend
cd cloudattend

# 2. Create and activate a dedicated virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip and install all requirements
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create dedicated persistent database and log directories
sudo mkdir -p /var/log/cloudattend
sudo mkdir -p /var/lib/cloudattend
sudo chown -R ubuntu:www-data /var/log/cloudattend
sudo chown -R ubuntu:www-data /var/lib/cloudattend

# 5. Configure production environment file
cp .env.example .env
nano .env
```
Inside `.env`, configure:
```ini
FLASK_ENV=production
# Generate a strong 64-character secret key:
# Run: python3 -c 'import secrets; print(secrets.token_hex(32))'
SECRET_KEY=YOUR_GENERATED_RANDOM_SECRET_KEY

# Persistent database location outside the transient webroot
DATABASE_PATH=/var/lib/cloudattend/cloudattend.db

PORT=8000
SESSION_COOKIE_SECURE=False  # Set to True once HTTPS is configured
DEFAULT_ADMIN_USER=admin
DEFAULT_ADMIN_PASS=ChangeThisToStrongPassword2026!
```

Initialize and seed the production database:
```bash
flask init-db
flask seed-db
```

### 6. Configuring systemd Service (Survival Across Reboots)
A systemd service daemon ensures that Gunicorn starts automatically upon system boot, recovers from crashes, and runs seamlessly in the background.

```bash
# Copy the included unit file to systemd directory
sudo cp deploy/cloudattend.service /etc/systemd/system/cloudattend.service

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable cloudattend
sudo systemctl start cloudattend

# Verify that the service is active and running
sudo systemctl status cloudattend
```

### 7. Configuring Nginx Reverse Proxy
Nginx receives web requests on port 80/443, serves static files (`/static/`) directly from disk with browser caching, and forwards dynamic requests to Gunicorn on `127.0.0.1:8000`.

```bash
# 1. Copy the Nginx configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/cloudattend

# 2. Enable the site by creating a symlink
sudo ln -sf /etc/nginx/sites-available/cloudattend /etc/nginx/sites-enabled/

# 3. Remove default Nginx welcome page
sudo rm -f /etc/nginx/sites-enabled/default

# 4. Test Nginx syntax configuration
sudo nginx -t

# 5. Restart Nginx to apply changes
sudo systemctl restart nginx
```

Now, navigate to your **EC2 Public IPv4 Address** in your browser:
```text
http://<YOUR-EC2-PUBLIC-IP>
```
Log in with your administrator credentials!

---

### 8. Monitoring with Amazon CloudWatch
Amazon CloudWatch provides built-in metrics without installing any external agents:

1. **Viewing Basic Metrics:**
   - Go to the **EC2 Console** -> Select your instance -> Click the **Monitoring** tab.
   - Review graphs for:
     - `CPUUtilization`: Measures CPU load percentage.
     - `NetworkIn` / `NetworkOut`: Volume of inbound/outbound traffic.
     - `StatusCheckFailed_Instance` and `StatusCheckFailed_System`: Health checks indicating hardware or OS failure.
2. **Creating CloudWatch Alarms:**
   - In AWS Console, open **CloudWatch** -> **Alarms** -> **Create Alarm**.
   - Select metric `EC2 > Per-Instance Metrics > CPUUtilization`.
   - Threshold: Greater than `80%` for 2 consecutive periods of 5 minutes.
   - Configure SNS Notification: Enter your email to receive an instant alert if CPU spikes.
   - Action: Optionally configure auto-reboot or instance restart.

---

### 9. SQLite vs. Amazon RDS: Deep Dive & Migration Strategy

| Feature | SQLite (Current) | Amazon RDS (PostgreSQL / MySQL) |
| :--- | :--- | :--- |
| **Architecture** | Serverless, file-based embedded engine | Dedicated managed relational database instance |
| **Concurrency** | Single-writer lock (WAL mode handles moderate concurrent reads) | Multi-version concurrency control (MVCC), thousands of simultaneous write transactions |
| **Scaling** | Vertical only (single server storage) | Horizontal read replicas, Multi-AZ high availability |
| **Maintenance** | Manual file backups required | Automated daily snapshots, point-in-time recovery (PITR) |
| **Ideal For** | Development, prototypes, single-server departmental deployments | Multi-server clusters, Auto-Scaling groups, high concurrency enterprise SaaS |

#### Migration Roadmap to Amazon RDS:
When scaling CloudAttend across multiple EC2 instances behind an Application Load Balancer (ALB), SQLite's file-based nature cannot be shared across multiple servers.

1. **Provision RDS Instance:** Launch an Amazon RDS instance running PostgreSQL 16 (or MySQL 8.0) in the same VPC.
2. **Security Group Rule:** Authorize inbound port `5432` on the RDS security group exclusively from the EC2 instance's Security Group ID.
3. **Migrate Schema:** Execute `schema.sql` syntax adapted for PostgreSQL/MySQL (or use SQLAlchemy / Alembic migrations).
4. **Data Transfer:** Use tools like `pgloader` to migrate existing SQLite rows directly into Amazon RDS:
   ```bash
   pgloader sqlite:///var/lib/cloudattend/cloudattend.db postgresql://user:password@rds-endpoint.amazonaws.com/cloudattend
   ```
5. **Update Application Connection:** Change `DATABASE_PATH` or `DATABASE_URL` in `.env` to the RDS connection string.

---

### 10. Backup Strategies, Updates & Security Hardening

#### A. Database Durability (Never Lose Records)
- **Persistent Location:** In our deployment, SQLite is placed in `/var/lib/cloudattend/cloudattend.db` (never in `/tmp` or within a transient directory).
- **Automated S3 Backup via Cron:**
  Create an automated nightly backup script to push database snapshots to an encrypted Amazon S3 bucket:
  ```bash
  #!/bin/bash
  # /home/ubuntu/backup_db.sh
  DATE=$(date +%Y-%m-%d_%H%M%S)
  sqlite3 /var/lib/cloudattend/cloudattend.db ".backup '/tmp/cloudattend_$DATE.db'"
  aws s3 cp /tmp/cloudattend_$DATE.db s3://your-private-backup-bucket/attendance/
  rm /tmp/cloudattend_$DATE.db
  ```
  Add to crontab (`crontab -e`):
  ```cron
  0 2 * * * /home/ubuntu/backup_db.sh
  ```
- **Amazon EBS Snapshots:** Configure AWS Data Lifecycle Manager (DLM) to take automated daily EBS volume snapshots.

#### B. Free SSL / HTTPS with Let's Encrypt (Certbot)
If you associate a domain name or Elastic IP with your EC2 instance:
```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-attendance-domain.com
```
Certbot automatically configures TLS 1.3 certificates and sets up automatic renewal.

#### C. Firewall (UFW) & Intrusion Prevention (Fail2ban)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Protect against SSH brute-force attacks
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Production Deployment Checklist

- [x] Application functional and running locally.
- [x] Modern, responsive dashboard with navy/blue/purple accent theme.
- [x] Student CRUD operations working with full validation.
- [x] Attendance marking with duplicate entry prevention.
- [x] Daily & monthly reports with zero-division protection.
- [x] Instant CSV export functionality verified.
- [x] Secure password hashing and session handling implemented.
- [x] CSRF protection enabled on all state-changing endpoints.
- [x] 35 automated pytest tests passing (100% pass rate).
- [x] Deployment configurations for Gunicorn, systemd, and Nginx tested.
- [x] Complete AWS EC2 deployment documentation written.

---

## License & Credits
Developed as an enterprise cloud attendance management platform.  
All sample student data included is strictly fictional.
