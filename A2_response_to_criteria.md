Assignment 2 - Cloud Services Exercises - Response to Criteria
================================================

Instructions
------------------------------------------------
- Keep this file named A2_response_to_criteria.md, do not change the name
- Upload this file along with your code in the root directory of your project
- Upload this file in the current Markdown format (.md extension)
- Do not delete or rearrange sections.  If you did not attempt a criterion, leave it blank
- Text inside [ ] like [eg. S3 ] are examples and should be removed


Overview
------------------------------------------------

- **Name:** Lachlan Forbes
- **Student number:** n11715910
- **Partner name (if applicable):** -
- **Application name:** Video Converter
- **Two line description:** This application allows users to upload a video file and convert it into a different video format. It handles uploading, transcoding, and downloading of videos through a web interface and API.
- **EC2 instance name or ID:**
i-068a76896623a5f46
------------------------------------------------

### Core - First data persistence service

- **AWS service name:**  S3
- **What data is being stored?:** Raw uploaded video files and transcoded video outputs.
- **Why is this service suited to this data?:** S3 is designed for scalable storage of large binary files like videos. It supports high durability and integrates well with pre-signed URLs for controlled access.
- **Why is are the other services used not suitable for this data?:** DynamoDB cannot handle large binary files efficiently.
- **Bucket/instance/table name:** n11715910-a2
- **Video timestamp:** 03.08
- **Relevant files:**
    - controllers.py
    - routes.py
    - dashboard_user.html/dashboard_admin.html
    - client.py

### Core - Second data persistence service

- **AWS service name:**  DynamoDB
- **What data is being stored?:** Video metadata (filename, user, status, format, progress, timestamps).
- **Why is this service suited to this data?:** DynamoDB provides fast, scalable access to structured metadata by video_id and user_id. It supports queries by user and flexible attributes.
- **Why is are the other services used not suitable for this data?:** S3 cannot efficiently query metadata fields.
- **Bucket/instance/table name:** n11715910-a2
- **Video timestamp:** 03.26
- **Relevant files:**
    - models.py

### Third data service

- **AWS service name:**  -
- **What data is being stored?:** -
- **Why is this service suited to this data?:** -
- **Why is are the other services used not suitable for this data?:** -
- **Bucket/instance/table name:** -
- **Video timestamp:** -
- **Relevant files:**
    -

### S3 Pre-signed URLs

- **S3 Bucket names:** n11715910-a2
- **Video timestamp:** 02.23
- **Relevant files:**
    - controllers.py
    - routes.py
    - client.py

### In-memory cache

- **ElastiCache instance name:** -
- **What data is being cached?:** -
- **Why is this data likely to be accessed frequently?:** -
- **Video timestamp:** -
- **Relevant files:**
    -

### Core - Statelessness

- **What data is stored within your application that is not stored in cloud data services?:** Temporary files created during transcoding. 
- **Why is this data not considered persistent state?:** These files are deleted after processing. If the server crashes, the video can be re-downloaded from S3 and transcoded again.
- **How does your application ensure data consistency if the app suddenly stops?:** Status updates and progress are written to DynamoDB during transcoding, so client-side state remains consistent. Temporary files are recreated when needed.
- **Relevant files:**
    - controllers.py
    - client.py 

### Graceful handling of persistent connections

- **Type of persistent connection and use:** Server-Sent Events stream for live transcoding progress updates.
- **Method for handling lost connections:** The async generator handles asyncio.CancelledError when clients disconnect. Clients reconnect to resume updates.
- **Relevant files:**
    - routes.py
    - client.py
    - dashboard_user.html/dashboard_admin.html


### Core - Authentication with Cognito

- **User pool name:** n11715910-a2
- **How are authentication tokens handled by the client?:** Cognito issues JWTs. The client sends them in the headers for all API requests.
- **Video timestamp:** 00.16, 03.56
- **Relevant files:**
    - auth.py
    - routes_auth.py

### Cognito multi-factor authentication

- **What factors are used for authentication:** Password and email
- **Video timestamp:** 00.55
- **Relevant files:**
    - client.py
    - cognito.py
    - routes_auth.py

### Cognito federated identities

- **Identity providers used:** Google
- **Video timestamp:** 01.12
- **Relevant files:**
    - client.py

### Cognito groups

- **How are groups used to set permissions?:** Admin users can delete and see transcoding logs of other users 
- **Video timestamp:** 01.21
- **Relevant files:**
    - auth.py
    - client.py
    - controllers.py
    - routes.py
    - models.py

### Core - DNS with Route53

- **Subdomain**:  n11715910-a2.cab432.com
- **Video timestamp:** 00.04

### Parameter store

- **Parameter names:** 
  - /n11715910/cognitouserpoolid  
  - /n11715910/cognitouserpoolclientid  
  - /n11715910/cognitodomain  
  - /n11715910/redirecturl  
  - /n11715910/s3bucket   
- **Video timestamp:** 04.45
- **Relevant files:**
    - pstore.py
    - pstore_client.py

### Secrets manager

- **Secrets names:** n11715910-cognito
- **Video timestamp:** 04.20
- **Relevant files:**
    - client.py
    - cognito.py

### Infrastructure as code

- **Technology used:** CloudFormation 
- **Services deployed:** S3, DynamoDB, Cognito 
- **Video timestamp:** -
- **Relevant files:**
    - launch_a2_AWS.yaml

### Other (with prior approval only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -

### Other (with prior permission only)

- **Description:**
- **Video timestamp:**
- **Relevant files:**
    -
