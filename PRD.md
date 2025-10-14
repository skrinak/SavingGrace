# Product Requirements Document: SavingGrace

## Project Overview

SavingGrace is a production-ready web application designed to help non-profit organizations track food donations and manage distribution to recipients. The system provides real-time visibility into inventory, donor management, recipient tracking, and distribution logistics.

## Technical Architecture

### Frontend
- **Framework**: React 18+
- **Build Tool**: Vite or Create React App
- **State Management**: React Context API or Redux Toolkit
- **UI Library**: Material-UI, Ant Design, or Tailwind CSS
- **HTTP Client**: Axios or Fetch API
- **Authentication**: AWS Cognito SDK
- **Hosting**: AWS S3 + CloudFront



### Backend
- **API Gateway**: AWS API Gateway (REST API)
- **Compute**: AWS Lambda (Node.js or Python runtime)
- **Database**: Amazon DynamoDB (primary) with optional RDS for complex queries
- **Authentication**: AWS Cognito User Pools
- **Authorization**: AWS IAM roles and Cognito groups
- **Storage**: Amazon S3 (for documents, images, receipts)
- **Monitoring**: AWS CloudWatch
- **Secrets Management**: AWS Secrets Manager

### Architecture Constraints
- API Gateway is the SOLE entry point for all backend requests
- NO proxies (no Express, no HTTP proxies)
- NO FastAPI or similar frameworks
- Direct Lambda integration with API Gateway
- All infrastructure must be production-grade from day one

### Infrastructure as Code
- AWS CloudFormation or AWS CDK
- Separate stacks for dev, staging, and production environments

## Core Features

### 1. User Management & Authentication

#### User Roles
- **Admin**: Full system access, user management, configuration
- **Donor Coordinator**: Manage donors, record donations
- **Distribution Manager**: Manage distributions, recipients
- **Volunteer**: View-only access, mark distributions complete
- **Read-Only**: Dashboard and reporting access

#### Authentication Requirements
- Email/password authentication via Cognito
- Multi-factor authentication (MFA) for admins
- Password reset flow
- Session management with JWT tokens
- Role-based access control (RBAC)

### 2. Donor Management

#### Donor Profiles
- Organization/individual name
- Contact information (phone, email, address)
- Donation history
- Preferred donation types
- Pickup requirements
- Tax ID for receipt generation
- Status (active, inactive, suspended)

#### Features
- Create, read, update, delete donors
- Search and filter donors
- Track donation frequency
- Generate donor reports
- Export donor lists

### 3. Donation Tracking

#### Donation Records
- Donor information
- Date and time received
- Food items (name, category, quantity, unit)
- Expiration dates
- Condition/quality rating
- Storage location
- Estimated value
- Receipt/proof of donation (image upload)
- Receiving staff member
- Status (pending, received, distributed, expired, discarded)

#### Food Categories
- Perishable (refrigerated, frozen)
- Non-perishable (canned, dry goods)
- Prepared meals
- Produce
- Dairy
- Protein
- Baked goods

#### Features
- Record new donations
- Bulk donation entry
- Upload donation receipts to S3
- Track inventory levels by category
- Expiration date alerts
- Generate donation receipts for donors
- Track chain of custody

### 4. Recipient Management

#### Recipient Profiles
- Name and household information
- Contact information
- Number of household members
- Dietary restrictions/allergies
- Preferred pickup location
- Eligibility verification status
- Enrollment date
- Status (active, inactive, graduated)

#### Features
- Create, read, update, delete recipients
- Verify eligibility
- Track distribution history
- Privacy controls (GDPR/CCPA compliant)
- Search and filter recipients

### 5. Distribution Management

#### Distribution Records
- Distribution date and time
- Recipients served
- Items distributed (from inventory)
- Quantity per item
- Distributing staff member
- Location
- Status (planned, in-progress, completed, cancelled)

#### Features
- Create distribution events
- Assign inventory to distributions
- Record real-time distributions
- Generate distribution manifests
- Track what each recipient received
- Prevent over-distribution (inventory checks)
- Distribution history reports

### 6. Inventory Management

#### Real-Time Inventory
- Current stock levels by category
- Items approaching expiration
- Storage location tracking
- FIFO (First In, First Out) recommendations
- Low stock alerts
- Automatic updates on donation/distribution

#### Features
- Dashboard view of current inventory
- Expiration date warnings (7 days, 3 days, expired)
- Inventory adjustments (spoilage, damage)
- Audit trail for all inventory changes
- Inventory forecasting

### 7. Reporting & Analytics

#### Dashboard Metrics
- Total donations (current month, YTD)
- Total distributions
- Number of recipients served
- Current inventory levels
- Top donors
- Most needed items
- Waste/spoilage rates

#### Reports
- Donation summary (by donor, date range, category)
- Distribution summary (by recipient, date range)
- Inventory turnover rates
- Donor tax receipts (annual)
- Impact reports for grants/funders
- Waste reduction metrics

#### Features
- Interactive dashboards
- Date range filters
- Export to CSV/PDF
- Scheduled email reports
- Custom report builder

### 8. Notifications & Alerts

#### Alert Types
- Items expiring within 7 days
- Items expiring within 3 days
- Items expired
- Low inventory warnings
- Distribution scheduled reminders
- New donation confirmations
- System maintenance notifications

#### Delivery Methods
- In-app notifications
- Email (AWS SES)
- SMS (AWS SNS) - optional

## Data Models

### DynamoDB Table Design

#### Users Table
```
PK: USER#<userId>
SK: PROFILE
- userId (UUID)
- email
- firstName
- lastName
- role
- phoneNumber
- status
- createdAt
- updatedAt
- cognitoId
```

#### Donors Table
```
PK: DONOR#<donorId>
SK: PROFILE
- donorId (UUID)
- name
- type (individual/organization)
- email
- phoneNumber
- address
- taxId
- preferredDonationTypes[]
- status
- createdAt
- updatedAt

GSI: DonorsByName (name-index)
```

#### Donations Table
```
PK: DONATION#<donationId>
SK: METADATA
- donationId (UUID)
- donorId
- receivedDate
- receivedBy (userId)
- totalValue
- status
- storageLocation
- receiptUrl (S3)
- notes
- createdAt
- updatedAt

PK: DONATION#<donationId>
SK: ITEM#<itemId>
- itemId (UUID)
- name
- category
- quantity
- unit
- expirationDate
- condition
- estimatedValue

GSI: DonationsByDonor (donorId-receivedDate-index)
GSI: DonationsByDate (receivedDate-index)
GSI: ItemsByExpiration (expirationDate-index)
```

#### Recipients Table
```
PK: RECIPIENT#<recipientId>
SK: PROFILE
- recipientId (UUID)
- firstName
- lastName
- email
- phoneNumber
- householdSize
- dietaryRestrictions[]
- address
- eligibilityStatus
- enrollmentDate
- status
- createdAt
- updatedAt

GSI: RecipientsByName (lastName-firstName-index)
```

#### Distributions Table
```
PK: DISTRIBUTION#<distributionId>
SK: METADATA
- distributionId (UUID)
- distributionDate
- location
- distributedBy (userId)
- status
- recipientCount
- totalItemsDistributed
- notes
- createdAt
- updatedAt

PK: DISTRIBUTION#<distributionId>
SK: RECIPIENT#<recipientId>
- recipientId
- items[] (itemId, quantity)
- timestamp

GSI: DistributionsByDate (distributionDate-index)
GSI: DistributionsByRecipient (recipientId-distributionDate-index)
```

#### Inventory Table (Materialized View)
```
PK: INVENTORY#<category>
SK: ITEM#<itemId>
- itemId (from donation)
- name
- category
- quantityAvailable
- unit
- expirationDate
- storageLocation
- donationId
- status (available, reserved, distributed, expired)
- updatedAt

GSI: InventoryByExpiration (expirationDate-index)
```

## API Specifications

### REST API Structure

Base URL: `https://us-west-2.console.aws.amazon.com/s3/buckets/saving-grace/{stage}`

#### Authentication
All endpoints require AWS Cognito JWT token in `Authorization` header:
```
Authorization: Bearer <JWT_TOKEN>
```

#### Donors API

```
GET    /donors                    - List all donors (paginated)
GET    /donors/{donorId}          - Get donor by ID
POST   /donors                    - Create new donor
PUT    /donors/{donorId}          - Update donor
DELETE /donors/{donorId}          - Delete donor (soft delete)
GET    /donors/{donorId}/donations - Get donation history
```

#### Donations API

```
GET    /donations                 - List donations (paginated, filterable)
GET    /donations/{donationId}    - Get donation by ID
POST   /donations                 - Create new donation
PUT    /donations/{donationId}    - Update donation
DELETE /donations/{donationId}    - Delete donation
POST   /donations/{donationId}/receipt - Upload receipt to S3
GET    /donations/expiring        - Get items expiring soon
```

#### Recipients API

```
GET    /recipients                - List recipients (paginated)
GET    /recipients/{recipientId}  - Get recipient by ID
POST   /recipients                - Create new recipient
PUT    /recipients/{recipientId}  - Update recipient
DELETE /recipients/{recipientId}  - Delete recipient (soft delete)
GET    /recipients/{recipientId}/history - Get distribution history
```

#### Distributions API

```
GET    /distributions             - List distributions (paginated)
GET    /distributions/{distributionId} - Get distribution by ID
POST   /distributions             - Create new distribution
PUT    /distributions/{distributionId} - Update distribution
DELETE /distributions/{distributionId} - Cancel distribution
POST   /distributions/{distributionId}/complete - Mark distribution complete
```

#### Inventory API

```
GET    /inventory                 - Get current inventory (all categories)
GET    /inventory/{category}      - Get inventory by category
GET    /inventory/alerts          - Get low stock and expiration alerts
POST   /inventory/adjust          - Manual inventory adjustment
```

#### Reports API

```
GET    /reports/dashboard         - Get dashboard metrics
GET    /reports/donations         - Donation reports (with filters)
GET    /reports/distributions     - Distribution reports (with filters)
GET    /reports/impact            - Impact summary report
POST   /reports/export            - Generate CSV/PDF export
```

#### Users API

```
GET    /users                     - List users (admin only)
GET    /users/{userId}            - Get user by ID
POST   /users                     - Create user (admin only)
PUT    /users/{userId}            - Update user
DELETE /users/{userId}            - Delete user (admin only)
PUT    /users/{userId}/role       - Update user role (admin only)
```

### API Gateway Configuration

- **Type**: REST API (not HTTP API)
- **Authentication**: Cognito User Pool Authorizer
- **Request Validation**: Enable on all endpoints
- **CORS**: Configured for frontend domain
- **Throttling**:
  - Steady-state: 1000 requests/second
  - Burst: 2000 requests
- **API Keys**: Not used (Cognito handles auth)
- **Request/Response Models**: JSON Schema validation
- **Logging**: Full request/response logging to CloudWatch
- **Caching**: Enable for GET requests (5-minute TTL)

### Lambda Function Organization

Each Lambda should handle a single resource or logical grouping:

```
/functions
  /donors
    - listDonors/
    - getDonor/
    - createDonor/
    - updateDonor/
    - deleteDonor/
  /donations
    - listDonations/
    - getDonation/
    - createDonation/
    - updateDonation/
    - uploadReceipt/
  /recipients
    - listRecipients/
    - getRecipient/
    - createRecipient/
    - updateRecipient/
  /distributions
    - listDistributions/
    - getDistribution/
    - createDistribution/
    - completeDistribution/
  /inventory
    - getInventory/
    - adjustInventory/
    - getAlerts/
  /reports
    - getDashboard/
    - generateReport/
    - exportReport/
  /users
    - listUsers/
    - getUser/
    - createUser/
    - updateUser/
```

### Lambda Best Practices for Production

- Use Lambda Layers for shared dependencies
- Environment variables for configuration (via Systems Manager)
- X-Ray tracing enabled for all functions
- Reserved concurrency for critical functions
- Dead letter queues for failed invocations
- Separate IAM roles per function (least privilege)
- Input validation in every function
- Structured logging (JSON format)
- Error handling with proper HTTP status codes
- Timeout: 30 seconds max
- Memory: 512MB-1024MB (test for optimal)

## Security Requirements

### Authentication & Authorization
- Must enforce SOC2 requirements
- AWS Cognito User Pools for authentication
- JWT tokens with 1-hour expiration
- Refresh tokens with 30-day expiration
- MFA required for admin accounts
- Role-based access control (RBAC)
- API Gateway Cognito Authorizer on all endpoints

### Data Security
- All data encrypted at rest (DynamoDB encryption, S3 encryption)
- All data encrypted in transit (TLS 1.2+)
- No sensitive data in logs
- PII data handling (recipient information)
- S3 bucket policies (no public access)
- Signed URLs for S3 access (time-limited)

### Network Security
- API Gateway in regional mode
- CloudFront with WAF for frontend
- No direct database access from internet
- Lambda functions in VPC (if accessing RDS)
- Security groups restricting Lambda egress
- CloudFront OAI for S3 access

### Compliance
- GDPR compliance (data portability, right to deletion)
- CCPA compliance (California privacy law)
- Audit logging for all data modifications
- Data retention policies
- Privacy policy and terms of service

### Monitoring & Incident Response
- CloudWatch alarms for errors and throttling
- AWS GuardDuty for threat detection
- CloudTrail for API auditing
- SNS alerts for security events
- Incident response runbook

## Performance Requirements

### Frontend
- Initial load time: < 3 seconds
- Time to interactive: < 5 seconds
- Lighthouse score: > 90
- Responsive design (mobile, tablet, desktop)
- Offline capability for critical features (optional PWA)

### Backend
- API response time (p95): < 500ms
- API response time (p99): < 1000ms
- Database query time: < 100ms
- S3 upload/download: Signed URLs (no proxy)
- Pagination: 50 items per page default

### Scalability
- Support 100 concurrent users initially
- Support 10,000 donations per month
- Support 5,000 recipients
- Auto-scaling Lambda
- DynamoDB on-demand or provisioned (monitor costs)

## Deployment & Operations

### Environment Strategy
- **Dev**: Development and testing
- **Staging**: Pre-production, identical to prod
- **Production**: Live system

### CI/CD Pipeline
- GitHub Actions or AWS CodePipeline
- Automated testing (unit, integration, e2e)
- Infrastructure deployment (CloudFormation/CDK)
- Frontend build and deployment to S3
- CloudFront cache invalidation
- Automated rollback on failure

### Deployment Steps
1. Run test suite
2. Build frontend (React build)
3. Deploy backend infrastructure (Lambda, API Gateway, DynamoDB)
4. Run smoke tests against staging
5. Deploy frontend to S3
6. Invalidate CloudFront cache
7. Run post-deployment verification
8. Monitor for errors (15-minute bake time)

### Monitoring
- CloudWatch dashboards for key metrics
- Lambda error rates and duration
- API Gateway 4xx/5xx errors
- DynamoDB throttling and capacity
- S3 request metrics
- Application-level metrics (custom metrics)
- User activity monitoring

### Backup & Disaster Recovery
- DynamoDB point-in-time recovery enabled
- S3 versioning enabled
- Daily automated backups
- Cross-region replication (optional for prod)
- RTO: 4 hours
- RPO: 1 hour
- Disaster recovery runbook

### Cost Management
- AWS Cost Explorer monitoring
- Budget alerts
- DynamoDB on-demand for variable workload
- Lambda memory optimization
- S3 lifecycle policies (move old receipts to Glacier)
- CloudFront caching to reduce origin requests
- Estimated monthly cost: $50-200 (low-moderate usage)

## Testing Strategy

### Unit Tests
- All Lambda functions
- React components
- Utility functions
- Target: > 80% code coverage

### Integration Tests
- API Gateway + Lambda integration
- DynamoDB operations
- Cognito authentication flows
- S3 upload/download

### End-to-End Tests
- Critical user flows
- Donation workflow (create donor -> record donation -> distribute)
- User authentication and authorization
- Report generation

### Load Testing
- Apache JMeter or Artillery
- Simulate 100 concurrent users
- Test API throttling
- Test Lambda cold starts

## Future Enhancements (Out of Scope for V1)

- Mobile app (React Native)
- SMS notifications for recipients
- Barcode scanning for donations
- Route optimization for pickup/delivery
- Integration with food banks network
- Volunteer scheduling and management
- Grant management module
- Multi-language support
- Advanced analytics and ML predictions
- Blockchain for donation transparency

## Success Metrics

- Successfully track 95%+ of all donations
- Reduce food waste by 20%
- Serve 500+ recipients in first 6 months
- 99.9% uptime
- Zero data breaches
- User satisfaction: 4.5/5 stars
- Donation-to-distribution time: < 48 hours average

## Constraints & Assumptions

### Constraints
- API Gateway is ONLY interface (no proxies, no FastAPI)
- Must be production-ready from day one
- AWS services only (no third-party hosting)
- Budget-conscious (non-profit)

### Assumptions
- Users have modern web browsers (Chrome, Firefox, Safari, Edge)
- Internet connectivity required (no true offline mode in V1)
- Single organization (no multi-tenancy in V1)
- US-based operation (timezone, currency, regulations)
- English language only (V1)
- Non-profit has AWS account and basic technical support

## Documentation Requirements

- Architecture diagrams (system, data flow, deployment)
- API documentation (OpenAPI/Swagger spec)
- User guides for each role
- Admin setup guide
- Developer onboarding guide
- Deployment runbook
- Incident response procedures
- Data retention and privacy policies
