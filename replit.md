# SocialMarket - Social Media Account Marketplace

## Overview

SocialMarket is a comprehensive web application built with Flask that serves as a marketplace for buying and selling social media accounts. The platform connects sellers who want to monetize their established social media presence with buyers looking to acquire accounts with existing followers and engagement.

## Recent Changes

### Currency Conversion and Support Form Fix (July 22, 2025)
- Converted entire application from USD to Nigerian Naira (NGN) currency
- Updated format_currency function in utils.py to use ₦ symbol
- Modified JavaScript formatCurrency function to use 'en-NG' locale and NGN currency
- Replaced all manual $ symbols with ₦ across all templates and forms
- Updated form labels, input placeholders, and validation messages to use Naira
- Fixed blinking support form by adding validation throttling and novalidate attribute
- Modified form validation JavaScript to skip support forms and add 500ms delay
- Replaced dollar-sign icons with money-bill icons for better Naira representation

### Database Migration to PostgreSQL (July 22, 2025)
- Migrated from SQLite to PostgreSQL for production compatibility
- Fixed Flask-Login UserMixin conflicts by renaming `is_active` field to `active`
- Resolved LSP diagnostics and type conflicts
- Updated database configuration to use environment-based DATABASE_URL
- Successfully tested admin user creation and application startup

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
The application follows a traditional Flask MVC architecture with the following key characteristics:
- **Flask Framework**: Core web framework providing routing, templating, and request handling
- **SQLAlchemy ORM**: Database abstraction layer for data modeling and queries
- **Flask-Login**: User authentication and session management
- **Blueprint Architecture**: Modular organization with separate blueprints for authentication, admin functions, and main application logic

### Frontend Architecture
- **Bootstrap 5**: CSS framework for responsive design and UI components
- **Jinja2 Templates**: Server-side templating with template inheritance
- **Font Awesome**: Icon library for consistent visual elements
- **Custom CSS/JS**: Additional styling and client-side functionality

### Database Architecture
- **SQLite**: Primary database stored in `instance/marketplace.db` for development and production
- **User-centric Design**: Core entities revolve around User model with relationships to accounts, purchases, and transactions
- **Referral System**: Built-in multi-level referral tracking for user acquisition

## Key Components

### Authentication System
- **User Registration/Login**: Email-based authentication with password hashing
- **Email Verification**: Token-based email verification system
- **Role-based Access**: User and admin role separation
- **Session Management**: Flask-Login handles user sessions and "remember me" functionality

### Account Management
- **Multi-platform Support**: Instagram, TikTok, YouTube, Twitter, Facebook, LinkedIn, Snapchat, Telegram
- **Verification Workflow**: Admin approval process for all account listings
- **Rich Metadata**: Followers count, engagement rates, category classification
- **Media Uploads**: Support for account screenshots and verification documents

### Payment System
- **Wallet-based**: Internal credit system for transactions
- **Bank Transfer Deposits**: Manual verification process for funding accounts
- **Commission Structure**: Platform fee system for completed transactions
- **Transaction History**: Comprehensive logging of all financial activities

### Admin Panel
- **User Management**: Admin can manage user accounts, KYC status, and permissions
- **Account Verification**: Review and approve/reject social media account listings
- **Payment Processing**: Verify deposits and manage financial transactions
- **Content Management**: Create and manage footer pages and site content
- **Support System**: Handle customer support tickets and inquiries

### Referral System
- **Unique Codes**: Each user gets a unique referral code
- **Commission Tracking**: 5% commission on referred user transactions
- **Multi-level Support**: Track referrer relationships
- **Earnings Dashboard**: Users can monitor referral performance

## Data Flow

### Account Listing Process
1. User creates account listing with platform details and media
2. System stores listing in "pending" status
3. Admin reviews listing through verification interface
4. Upon approval, account becomes visible in marketplace
5. Buyers can browse and purchase approved accounts

### Purchase Process
1. Buyer selects account and initiates purchase
2. System checks buyer's wallet balance
3. If sufficient funds, creates purchase record
4. Seller receives notification of sale
5. Admin can verify payment completion
6. Account ownership transfers to buyer

### Deposit Process
1. User initiates deposit request with amount and payment proof
2. System creates pending transaction record
3. Admin reviews deposit evidence
4. Upon approval, user's wallet balance is updated
5. Transaction status updated to "completed"

## External Dependencies

### Third-party Services
- **Email Service**: Configured through environment variables (SMTP settings)
- **File Storage**: Local file system for uploaded documents and images
- **Payment Processing**: Manual bank transfer verification (no automated payment processor)

### Python Packages
- **Flask**: Web framework
- **SQLAlchemy**: Database ORM
- **Flask-Login**: Authentication
- **Flask-WTF**: Form handling and CSRF protection
- **Pillow**: Image processing and compression
- **Werkzeug**: WSGI utilities and security helpers

### Frontend Dependencies
- **Bootstrap 5**: CSS framework (CDN)
- **Font Awesome 6**: Icons (CDN)
- **TinyMCE**: Rich text editor for admin content management (CDN)

## Deployment Strategy

### Configuration
- **Environment Variables**: Database URL, secret key, upload paths
- **Database**: SQLite for development, configurable for production
- **File Uploads**: Local file system with size and type restrictions
- **Session Management**: Secure session configuration with CSRF protection

### Development Setup
- **Database Initialization**: Automatic table creation through SQLAlchemy
- **Admin Account**: Manual creation required for initial admin access
- **File Permissions**: Upload directory must be writable by application

### Security Considerations
- **Password Hashing**: Werkzeug secure password hashing
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **File Upload Security**: Restricted file types and size limits
- **Admin Access**: Role-based access control for administrative functions
- **Input Validation**: WTForms validation on all user inputs

The application is designed to be a complete marketplace solution with built-in user management, payment processing, and administrative tools. The modular architecture allows for easy extension and maintenance, while the comprehensive admin panel provides full control over platform operations.

## Recent Changes

### File Upload Enhancement (July 22, 2025)
- Implemented automatic file compression for oversized uploads
- Enhanced compression algorithm with progressive quality reduction and resizing  
- Updated frontend to remove file size restrictions and provide user feedback
- Modified templates to reflect new auto-compression feature
- Successfully tested with images up to 18MB being compressed to 15KB target

### Database Migration to PostgreSQL (July 22, 2025)
- Migrated from SQLite to PostgreSQL for production compatibility
- Fixed Flask-Login UserMixin conflicts by renaming `is_active` field to `active`
- Resolved LSP diagnostics and type conflicts
- Updated database configuration to use environment-based DATABASE_URL
- Successfully tested admin user creation and application startup

### July 23, 2025 - Migration to Replit Environment and Alert System Enhancement
- Successfully migrated from Replit Agent to standard Replit environment
- Fixed database initialization to prevent recreating database on each startup
- Updated database configuration to use absolute path for SQLite reliability
- Configured application to use existing SQLite database instead of PostgreSQL
- Application running successfully on port 5000 with gunicorn
- Admin account creation logic updated to check for existing users
- Default footer pages creation improved with conflict checking

### Alert Auto-Dismiss Issue Fix (July 23, 2025)
- Fixed critical bug where important information alerts were disappearing after 5 seconds
- Implemented alert-permanent class system to prevent auto-dismissal of critical alerts
- Updated JavaScript in main.js to only auto-dismiss flash messages, not permanent alerts
- Applied alert-permanent class to over 25+ critical alert elements across all templates:
  - Bank transfer details and payment instructions
  - KYC verification status alerts
  - Security notices and warnings
  - Information boxes and guidelines
  - Admin verification checklists
  - Support form notices
  - Account purchase instructions
- Comprehensive scan and fix ensures users can properly read important information
- Bank details, KYC status, and other critical alerts now remain visible permanently

### Admin System Management Enhancement (July 23, 2025)
- Added comprehensive admin system settings management
- Implemented bank details configuration for user deposits  
- Created SMTP email configuration with test email functionality
- Added general system settings (commission rates, file limits, etc.)
- Fixed HTTP 500 errors in support system (nl2br filter issue)
- Enhanced footer page management with proper form validation
- Updated admin dashboard with system settings navigation
- All admin templates include alert-permanent classes for critical information