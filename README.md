# IGCSE Learning Management System
## Functional Requirements

### 1. User Functional Requirements (Common)

- **[FR-1]** Register and log in using email and password authentication.
- **[FR-2]** Log out securely from the system.
- **[FR-3]** View and update personal profile information.
- **[FR-4]** Change account password.
- **[FR-5]** Receive system notifications related to learning activities.
- **[FR-6]** Access the system based on assigned role permissions.

### 2. Student Functional Requirements

- **[FR-7]** View enrolled courses and learning materials.
- **[FR-8]** Participate in quizzes and assessments.
- **[FR-9]** Submit assignments online.
- **[FR-10]** View quiz results and assignment scores.
- **[FR-11]** Track personal learning progress.
- **[FR-12]** View announcements and notifications from teachers.
- **[FR-13]** Access personal academic history.

### 3. Teacher Functional Requirements

- **[FR-14]** Log in and manage assigned courses.
- **[FR-15]** Create, update, and delete quizzes and assignments.
- **[FR-16]** Grade student submissions.
- **[FR-17]** View student performance and progress.
- **[FR-18]** Send announcements and notifications to students.
- **[FR-19]** Communicate with students through the system.

### 4. Parent Functional Requirements

- **[FR-20]** Log in to the parent portal.
- **[FR-21]** View assigned student academic performance.
- **[FR-22]** Monitor quiz results and assignment scores.
- **[FR-23]** Receive notifications about student progress and activities.

### 5. Manager Functional Requirements

- **[FR-24]** Manage courses and academic programs.
- **[FR-25]** Assign teachers to courses.
- **[FR-26]** View overall academic statistics and reports.
- **[FR-27]** Monitor system usage and learning outcomes.

### 6. Admin Functional Requirements

- **[FR-28]** Manage user accounts (create, update, delete).
- **[FR-29]** Assign roles (admin, manager, teacher, student, parent).
- **[FR-30]** Manage system-wide settings.
- **[FR-31]** Monitor system activity and access logs.

## System Architecture

- **Backend Framework:** FastAPI  
- **Database ORM:** SQLAlchemy  
- **Template Engine:** Jinja2  
- **Authentication:** Role-based access control using dependencies  
- **Architecture Style:** Router-based modular architecture  

## Project Structure

