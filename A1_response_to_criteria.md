Assignment 1 - REST API Project - Response to Criteria
================================================

Overview
------------------------------------------------

- **Name:** Lachlan Forbes
- **Student number:** n11715910
- **Application name:** Video Converter
- **Two line description:** This application allows users to upload a video file and convert it into a different video format. It handles uploading, transcoding, and downloading of videos through a web interface and API.


Core criteria
------------------------------------------------

### Containerise the app

- **ECR Repository name:** add
- **Video timestamp:** add
- **Relevant files:**
    - /Dockerfile 
    - /Dockerfile.client 
    - /docker-compose.yml

### Deploy the container

- **EC2 instance ID:** add
- **Video timestamp:** add

### User login

- **One line description:** Hard coded admin and user accounts. Using JWTs for sessions.
- **Video timestamp:** add
- **Relevant files:**
    - /videoapi/auth.py
    - /videoapi/routes.py
    - /videocli/templates/login.html

### REST API

- **One line description:** REST API with endpoints (as nouns) and HTTP methods (GET, POST, PUT, DELETE), and appropriate status codes
- **Video timestamp:** add
- **Relevant files:**
    - /videoapi/routes.py
    - /videoapi/controllers.py
    - /videoapi/models.py

### Data types

#### First kind

- **One line description:** Uploaded and transcoded video files stored locally.
- **Type:** Unstructured
- **Rationale:** These files are the primary user data, manipulated during upload, download, and transcoding. Stored as files because binary blobs in databases are inefficient for large media.
- **Video timestamp:** add
- **Relevant files:**
    - /videoapi/controllers.py
    - /uploads (local)

#### Second kind

- **One line description:** Video metadata stored in MariaDB, including ownership, file paths, format, and processing parameters.
- **Type:** Structured, ACID-compliant
- **Rationale:** Metadata must remain consistent and reliable for user and task information, so a relational database is used to enforce ACID properties.
- **Video timestamp:** add
- **Relevant files:**
  - /db/db.py
  - /videoapi/models.py

#### Third kind

- **One line description:** Transcoding task logs stored in a JSON file, tracking status, timestamps, errors, and allowing rerun on failure.
- **Type:** Structured, non-ACID
- **Rationale:** JSON file storage provides a lightweight mechanism for logging transcoding tasks outside of the main relational MariaDB. It is not ACID-compliant, but this is acceptable for task logs because occasional write conflicts or temporary inconsistencies do not affect core user or video data. This mechanism allows the application to easily read, update, and manage individual task records, including the ability to rerun failed transcoding tasks.
- **Video timestamp:** add
- **Relevant files:**
  - /videoapi/routes.py
  - /videoapi/task_logger.py
  - /videocli/client.py

### CPU intensive task

 **One line description:** The CPU intesive task uses ffmpeg to convert .mp4 files to .mov
- **Video timestamp:** add
- **Relevant files:**
    - /videoapi/controllers.py
    - /videoapi/routes.py
    - /videocli/client.py
    - /videocli/templates/dashboard_admin.html
    - /videocli/templates/dashboard_user.html

### CPU load testing

 **One line description:** CPU load testing is conducted through the web client 
- **Video timestamp:** add
- **Relevant files:**
    - 

Additional criteria
------------------------------------------------

### Extensive REST API features

- **One line description:** Implemented in the web client with role-based access, enabling pagination, filtering, and sorting across API endpoints.
- **Video timestamp:** add
- **Relevant files:**
    - /videoapi/routes.py
    - /videocli/client.py
    - /videocli/templates/dashboard_admin.html
    - /videocli/templates/dashboard_user.html

### External API(s)

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Additional types of data

- **One line description:** transcoding tasks are tracked in a JSON file, storing structured information such as status, timestamps, and errors. This data is not ACID-compliant but allows the application to interact with it, including rerunning a transcoding task in case of errors.
- **Video timestamp:** add
- **Relevant files:**
    - /videoapi/task_logger.py
    - /videocli/client.py
    - /videoapi/routes.py

### Custom processing

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 

### Infrastructure as code

- **One line description:** The application uses IaC to fully deploy on AWS, automatically launching an EC2 instance with all dependencies installed via a launch script. The script also calls the docker Compose file to deploy the 3 containers. This is all down from a single line of code.
- **Video timestamp:**add
- **Relevant files:**
    - /docker-compose.yml
    - /IaC/launch_a1_ec2.py 

### Web client

- **One line description:** The web client implements all REST API endpoints in a meaningful way and includes a login system with two separate HTML templates for users and admins.
- **Video timestamp:** add
- **Relevant files:**
    - /videocli/client.py
    - /videocli/templates/dashboard_admin.html
    - /videocli/templates/dashboard_user.html
    - /Dockerfile.client 

### Upon request

- **One line description:** Not attempted
- **Video timestamp:**
- **Relevant files:**
    - 