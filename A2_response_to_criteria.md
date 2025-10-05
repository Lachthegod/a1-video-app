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
- **Partner name (if applicable):** Mirelle Mimiague (n10810315)
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
- **Bucket/instance/table name:** n11715910-a2: in video code / mirelle-storage: in new code
- **Video timestamp:** 03.08
- **Relevant files:**
    - api/controllers.py
    - api/routes.py
    - client/templates/dashboard_user.html
    - client/templates/dashboard_admin.html
    - client/main.py

### Core - Second data persistence service

- **AWS service name:**  DynamoDB
- **What data is being stored?:** Video metadata (filename, user, status, format, progress, timestamps).
- **Why is this service suited to this data?:** DynamoDB provides fast, scalable access to structured metadata by video_id and user_id. It supports queries by user and flexible attributes.
- **Why is are the other services used not suitable for this data?:** S3 cannot efficiently query metadata fields.
- **Bucket/instance/table name:** n11715910-a2: in video code / mirelle-database: in new code
- **Video timestamp:** 03.26
- **Relevant files:**
    - api/models.py

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

- **S3 Bucket names:** n11715910-a2: in video code / mirelle-storage: in new code
- **Video timestamp:** 02.23
- **Relevant files:**
    - api/controllers.py
    - api/routes.py
    - client/main.py

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
    - api/controllers.py
    - client/main.py 

### Graceful handling of persistent connections

- **Type of persistent connection and use:** Server-Sent Events stream for live transcoding progress updates.
- **Method for handling lost connections:** The async generator handles asyncio.CancelledError when clients disconnect. Clients reconnect to resume updates.
- **Relevant files:**
    - api/routes.py
    - client/main.py
    - client/templates/dashboard_user.html
    - client/templates/dashboard_admin.html


### Core - Authentication with Cognito

- **User pool name:** n11715910-a2: in video code / mirelle-user-pool: in new code
- **How are authentication tokens handled by the client?:** Cognito issues JWTs (IdToken and AccessToken). The client stores them in HTTP-only cookies and sends them as Bearer tokens in Authorization headers for all API requests.
- **Video timestamp:** 00.16, 03.56
- **Relevant files:**
    - api/auth.py
    - api/routes_auth.py
    - client/main.py

### Cognito multi-factor authentication

- **What factors are used for authentication:** Password and Email OTP (configured as OPTIONAL in Cognito)
- **Video timestamp:** 00.55
- **Relevant files:**
    - client/main.py
    - client/templates/mfa.html
    - api/cognito.py
    - api/routes_auth.py

### Cognito federated identities

- **Identity providers used:** Google
- **Video timestamp:** 01.12
- **Relevant files:**
    - client/main.py (OAuth2 callback handling)
    - client/templates/login.html (Google login button)
    - terraform/cognito.tf (Google identity provider configuration)

### Cognito groups

- **How are groups used to set permissions?:** Admin users can view, edit, and delete all videos from all users. Regular users can only access their own videos. Groups are extracted from JWT claims (cognito:groups).
- **Video timestamp:** 01.21
- **Relevant files:**
    - api/auth.py (extracts role from JWT)
    - client/main.py (renders different dashboards based on role)
    - api/controllers.py (permission checks)
    - api/routes.py (authorization logic)
    - api/models.py (role-based data access)

### Core - DNS with Route53

- **Subdomain**:  n11715910-a2.cab432.com: in video code / mirelle.cab432.com: in new code
- **Video timestamp:** 00.04

### Parameter store

- **Parameter names:** 
  - /mirelle/COGNITO_USER_POOL_ID  
  - /mirelle/COGNITO_CLIENT_ID  
  - /mirelle/COGNITO_USER_POOL_DOMAIN  
  - /mirelle/DOMAIN
  - /mirelle/REDIRECT_URI
  - /mirelle/S3_BUCKET_NAME
  - /mirelle/DYNAMODB_TABLE
- **Video timestamp:** -
- **Relevant files:**
    - parameter_store.py (loads parameters with memoization)
    - terraform/parameters.tf (defines parameters)

### Secrets manager

- **Secrets names:** n11715910-cognito: in video code / mirelle/COGNITO_CLIENT_SECRET: in new code
- **Video timestamp:** 04.20
- **Relevant files:**
    - secrets_manager.py (retrieves secrets)
    - client/main.py (uses secret for OAuth token exchange)
    - api/cognito.py (uses secret for authentication)
    - terraform/secrets.tf (stores Cognito client secret)

### Infrastructure as code

- **Technology used:** Terraform
- **Services deployed:** EC2 (with IAM role), ECR (2 repositories), S3, Cognito (User Pool, Client, Domain, Google Identity Provider), API Gateway, Parameter Store, Secrets Manager
- **Video timestamp:** -
- **Relevant files:**
    - terraform/instances.tf (EC2, ECR)
    - terraform/s3.tf (S3 bucket)
    - terraform/cognito.tf (Cognito resources)
    - terraform/api_gateway.tf (API Gateway for OAuth callback)
    - terraform/parameters.tf (SSM parameters)
    - terraform/secrets.tf (Secrets Manager)
    - terraform/user_data.sh (EC2 initialization script)
    - terraform/variables.tf (configuration variables)
    - run-terraform.sh (deployment script)
    - run-docker.sh (container build and push script)

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
