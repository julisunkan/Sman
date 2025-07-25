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

### July 23, 2025 - Replit Agent to Replit Environment Migration - COMPLETED
- Successfully migrated Flask social media marketplace from Replit Agent to standard Replit environment
- Configured SQLite database at instance/marketplace.db per user request
- Fixed Flask-Login authentication system and template field name inconsistencies
- Resolved LSP diagnostics in authentication and routing modules
- Enhanced security with proper client/server separation and robust practices
- Application running successfully on port 5000 with gunicorn and SQLite database
- All core routes functional: authentication, accounts browsing, admin panel, user dashboard
- Migration completed successfully with all checklist items verified
- Fixed admin users page 500 error by correcting verification_token field reference

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

### Replit Agent to Environment Migration - Complete (July 23, 2025)
- Successfully migrated Flask social media marketplace from Replit Agent to standard Replit environment
- Implemented PostgreSQL database integration with proper environment configuration
- Fixed Flask-Login authentication system and template field name inconsistencies (confirm_password vs password2)
- Resolved all LSP diagnostics in authentication, routing, and forms modules
- Updated database models to be compatible with PostgreSQL
- Fixed template rendering errors and form field mismatches
- Enhanced security with proper client/server separation and robust practices
- Fixed missing form fields: KYCForm.document, PurchaseForm.account_id and payment_proof
- Resolved type safety issues with nullable form data handling
- Added proper type annotations and error handling for search filters
- Application running successfully on port 5000 with gunicorn and PostgreSQL
- All core routes functional: authentication, accounts browsing, admin panel, user dashboard
- Fixed currency display from USD ($) to Nigerian Naira (₦) in notifications

### Support System Redesign (July 23, 2025)
- Completely redesigned admin support system to remove popup forms per user request
- Replaced modal dialogs with inline expandable cards for better user experience
- Implemented collapsible ticket details with toggle functionality
- Added inline response forms directly within each ticket card
- Enhanced ticket display with comprehensive user information and message details
- Maintained all existing functionality (CSRF protection, form validation, email notifications)
- Fixed JavaScript validation issues and removed dependency on Bootstrap modals
- Support system now uses clean, accessible inline interface without popups

### Admin User Management Enhancement (July 23, 2025)
- Fixed admin quick actions functionality (verify email, deactivate user, reset password)
- Added manual email verification route allowing admins to verify user emails directly
- Implemented proper user status toggle with email notifications
- Modified password reset to force password change on next login instead of sending emails
- Enhanced user management template with proper form submissions and CSRF protection
- Replaced JavaScript AJAX calls with reliable server-side form processing
- Added force_password_change database field and change password workflow
- Created change password template and form for forced password changes
- All admin actions now provide user feedback and appropriate notifications

### Dynamic Bank Details Integration (July 23, 2025)
- Updated deposit page to dynamically display bank details from admin system settings
- Modified deposit route to fetch bank details from SystemSettings model
- Enhanced deposit template with conditional display of bank information
- Added fallback message when bank details are not configured
- Fixed footer page form template error with is_active field
- Bank details now automatically sync between admin settings and user deposit page

### Dynamic Footer Pages Auto-Addition (July 23, 2025)
- Implemented automatic footer link addition when admins create new footer pages
- Added Flask context processor to inject active footer pages into all templates
- Modified base.html footer template to dynamically display footer pages from database
- Footer now automatically updates when new pages are created or existing pages are activated/deactivated
- Enhanced form submission handling with improved validation and CKEditor content synchronization
- Fixed Create Footer Page button functionality with proper event listeners and debugging

### Admin Social Media Configuration (July 23, 2025)
- Added social media links configuration to admin system settings
- Implemented URLField and URL validators for social media form fields
- Added six social media platforms: Facebook, Twitter, Instagram, Telegram, LinkedIn, YouTube
- Enhanced SystemSettingsForm with social media URL fields and validation
- Updated admin system settings template with dedicated social media configuration section
- Modified Flask context processor to inject social media links into all templates
- Made footer social media links dynamic - only configured links appear with proper icons and titles
- Social media links open in new tabs with descriptive titles for better user experience

### Dynamic Site Branding System (July 23, 2025)
- Implemented dynamic site name and description throughout the entire website
- Enhanced Flask context processor to inject site configuration globally
- Updated base template to use dynamic site name in navigation, footer, and page titles
- Added META description tags with dynamic content for better SEO
- Modified index page to use dynamic site description in hero section
- Site name and description changes in admin settings now reflect instantly across all pages
- Updated copyright notice to use dynamic site name
- Comprehensive branding system allows complete site rebranding from admin panel

### Dynamic Financial Settings System (July 23, 2025)
- Implemented dynamic commission rates, referral rates, and minimum deposit amounts
- Enhanced Flask context processor to inject financial configuration globally
- Updated referral page to display dynamic commission rates instead of hardcoded 5%
- Modified deposit page to use dynamic minimum deposit amount and validation
- Enhanced utils.py calculate_referral_commission function to use dynamic rates
- Added backend validation for minimum deposit amounts using system settings
- All financial settings in admin panel now reflect instantly throughout website
- Commission rates, referral rates, and minimum deposits are now fully configurable

### Admin Settings Import/Export System (July 23, 2025)
- Added comprehensive settings import/export functionality to admin panel
- Implemented SettingsImportForm and SettingsExportForm for file handling
- Created import_settings and export_settings routes with full validation
- Added selective export options: all, bank, SMTP, general, and social media settings
- Import system supports overwrite protection and conflict resolution
- Export generates timestamped JSON files for easy backup and migration
- Added import/export buttons to system settings page toolbar
- Full error handling and user feedback for all operations

### Migration Fixes and Enhancements (July 23, 2025)
- Fixed LSP diagnostics issues in admin.py with proper SystemSettings constructor
- Enhanced form handling and JSON import validation
- Resolved CSRF token handling and authentication system compatibility
- Updated templates with import/export functionality integration
- Successfully completed migration from Replit Agent to standard Replit environment

### Static Database Configuration for Render Deployment (July 23, 2025)
- Successfully configured application to use SQLite instead of PostgreSQL for static deployment
- Updated database configuration to dynamically handle both SQLite and PostgreSQL connections
- Removed PostgreSQL dependency from pyproject.toml to reduce deployment complexity
- Created comprehensive deployment files for Render platform:
  - render.yaml: Service configuration with environment variables
  - build.sh: Build script for dependency installation and directory creation
  - start.sh: Production start script with proper environment setup
  - Procfile: Simple process configuration for web dyno
  - runtime.txt: Python version specification
- Fixed database schema mismatch by recreating SQLite database with current models
- Application now runs successfully with SQLite backend and is ready for Render deployment
- Maintained all existing functionality while switching to static database approach

### Replit Agent to Environment Migration - Complete (July 23, 2025)
- Successfully completed migration from Replit Agent to standard Replit environment
- Fixed authentication system issues and improved error handling in registration
- Enhanced registration route with proper validation and duplicate checking
- Added comprehensive error handling for database integrity constraints
- Fixed LSP diagnostics issues in admin panel and authentication modules
- Implemented admin settings import/export functionality with JSON file support
- Removed "Routing Number" field from bank details forms and templates per user request
- All core routes functional: authentication, accounts browsing, admin panel, user dashboard
- Application running stable on port 5000 with SQLite database
- Admin login available with credentials: admin@marketplace.com / admin123
- Migration completed successfully with comprehensive feature set

### Replit Environment Migration - Complete (July 23, 2025)
- Successfully completed migration from Replit Agent to standard Replit environment
- Fixed all route errors including missing admin root route and template function access
- Enhanced template context processor to globally provide format_currency function
- Resolved 500 errors in deposit page and other template rendering issues
- Application running successfully on port 5000 with PostgreSQL database
- All core functionalities verified: authentication, account browsing, admin panel, user dashboard
- Admin credentials: admin@marketplace.com / admin123
- Migration completed with comprehensive route and error fixing

### Bulk Account Creation and Market Simulation (July 23, 2025)
- Created 118 social media accounts across all 8 supported platforms
- Generated realistic Nigerian-themed usernames, follower counts, and engagement rates
- Added proper pricing structure based on platform and follower count
- Included login credentials and account URLs for each listing
- Platform distribution: Instagram (19), TikTok (15), YouTube (15), Facebook (16), LinkedIn (15), Twitter (10), Snapchat (13), Telegram (15)
- All accounts marked as "sold" to simulate active marketplace activity
- Accounts span 10 different categories: lifestyle, entertainment, technology, business, health, finance, education, travel, food, fashion
- Updated website display to show sold accounts with visual indicators
- Modified route filters to include sold accounts in homepage and browse pages
- Added "SOLD" badges and updated button styling for sold accounts
- Enhanced user experience with clear visual distinction between available and sold accounts
- Adjusted all account prices to realistic range of ₦2,000-₦10,000 based on platform and follower count
- Price distribution: Instagram/TikTok/YouTube premium pricing, LinkedIn professional rates, moderate pricing for other platforms
- Average account price: ₦7,027 with good spread across all price ranges
- Disabled "View Live Account" buttons for sold accounts to prevent access to unavailable accounts
- Added clear status indicators and disabled preview functionality for sold accounts
- Enhanced user experience with appropriate messaging for sold account limitations
- Fixed username formatting consistency - ensured all social media usernames use single @ symbol
- Standardized username format across all platforms with proper @ prefixes where appropriate
- Disabled "Login to Purchase" and purchase functionality for sold accounts
- Added disabled "Account Sold" button with clear messaging for sold accounts
- Updated account status display to show "SOLD" badge in account details
- Enhanced purchase route protection to prevent purchasing sold accounts
- Changed "View Details (SOLD)" button text to simply "SOLD" for cleaner display
- Fixed double @@ display issue by implementing conditional @ symbol logic
- Updated index, browse, and account detail templates to prevent @@ username display
- Fixed pagination error in browse page causing 500 internal server error
- Replaced problematic **request.args with explicit parameter passing

### Realistic Nigerian Seller Distribution (July 23, 2025)
- Created 15 authentic Nigerian seller accounts with realistic names and email addresses
- Distributed all 117 social media accounts among the Nigerian sellers instead of "demo_seller"
- Seller names include: ChidozieOkeke, AdesuwaIhama, EmmanuelAdebayo, FatimaAbubakar, etc.
- Removed demo_seller account completely from the system
- Each seller now owns 5-13 accounts distributed across different platforms
- Account distribution reflects realistic ownership patterns in Nigerian marketplace


### Transaction Login Details UI Enhancement (July 23, 2025)
- Converted Account Login Details from popup modal to inline dropdown in transactions page
- Replaced Bootstrap modal with collapsible row that expands below the transaction
- Enhanced user experience with inline display of account credentials
- Maintained all security features: password visibility toggle, copy-to-clipboard functionality
- Improved responsive layout with two-column grid for credentials display
- Added close button within dropdown for better user control

### Admin Listing Management & Account URL Preview (July 23, 2025)
- Added admin edit and delete functionality for social media account listings
- Enhanced AdminEditAccountForm with comprehensive editing capabilities including status updates
- Created admin edit account template with full account management interface
- Implemented account deletion with safety checks for pending purchases
- Added account_url field to SocialMediaAccount model for account previews
- Enhanced user listing creation form to include optional account URL field
- Updated account browse and detail templates with preview buttons
- Added live account preview functionality accessible to buyers and admins
- Account URLs display as external link buttons in admin dashboard and user browsing
- Email notifications sent to sellers when accounts are edited or deleted by admins
- CSRF token visibility issue fixed in KYC verification forms

### Instant Wallet-Based Purchase System (July 23, 2025)
- Completely redesigned purchase system to use wallet-based instant payments
- Removed payment proof upload requirement in favor of immediate wallet deduction
- Implemented instant account details release upon successful payment
- Added automatic account status change to 'sold' after purchase completion
- Enhanced platform commission calculation using dynamic system settings
- Integrated referral commission system for instant commission payments
- Created comprehensive purchase details page with account credentials display
- Updated purchase template to show wallet balance and payment flow
- Added transaction records for buyers, sellers, and referral commissions
- Removed sold accounts from browse listings and homepage featured accounts
- Email notifications sent to both buyer and seller upon successful purchase
- Purchase system now creates completed Purchase records instantly
- Enhanced security with password visibility toggle and copy-to-clipboard functionality

### Seller Withdrawal System Implementation (July 23, 2025)
- Added comprehensive withdrawal system for sellers to withdraw earnings
- Created Withdrawal model with bank details and admin processing workflow
- Implemented seller sales tracking dashboard with earnings breakdown
- Added WithdrawalForm with balance validation and bank account fields
- Created admin withdrawal management interface with approval/rejection workflow
- Added withdrawal processing routes with email notifications for status changes
- Enhanced navigation with withdrawal and sales tracking links
- Created seller sales dashboard showing gross earnings, commissions, and net earnings
- Implemented automatic fund deduction on withdrawal request (pending approval)
- Added refund mechanism for rejected withdrawals with transaction records
- Updated admin sidebar and dashboard statistics to include withdrawal management
- Enhanced wallet interface with withdrawal button and improved layout
- All withdrawal operations use manual bank transfer processing
- Sales tracking shows detailed transaction history and withdrawal status

### Admin User Creation System (July 23, 2025)
- Added admin functionality to create user accounts directly from admin panel
- Created AdminCreateUserForm with comprehensive user configuration options
- Implemented admin/users/create route with proper validation and error handling
- Added create_user.html template with professional form design and user guidance
- Enhanced admin dashboard and users page with "Create New User" buttons
- Includes options for username, email, password, role (user/admin), verification status
- Supports initial balance setting, KYC status configuration, and account activation
- Automatic welcome email sent to new users if email verification is enabled
- Proper validation prevents duplicate usernames and email addresses
- Admin can create both regular users and admin accounts with full privileges

### System Error Scan and Bank Details Update (July 23, 2025)
- Completed comprehensive error scan of the entire web application
- Updated bank account details in admin system settings to: SocialMarket Bank, Account: 1234567890, Routing: 123456789
- Verified all critical endpoints are working correctly (200 OK responses)
- Confirmed database integrity with proper table structure and data
- Tested static asset delivery (JavaScript, CSS) - all functioning properly
- Validated template rendering for key pages (homepage, login, accounts browse)
- No LSP diagnostics errors found in codebase
- All navigation links pointing to correct routes
- File upload system working with automatic compression
- Email notification system operational
- System settings properly configured and accessible
- Application running stable on port 5000 with SQLite database

### Dark Theme Implementation and White Background Fix (July 23, 2025)
- Fixed all white background issues throughout the web application
- Updated admin email template badges from bg-light to bg-secondary for better dark theme compatibility
- Changed admin sidebar from bg-light to bg-dark for consistent dark theme
- Modified homepage statistic cards from bg-white to bg-dark with opacity
- Enhanced CSS with comprehensive dark theme overrides for all Bootstrap components
- Added dark theme support for forms (form-control, form-select) with proper focus states
- Implemented dark theme for modals, dropdowns, list groups, and pagination
- Enhanced alert components with dark theme color schemes
- Updated card components and headers for consistent dark appearance
- Fixed image preview backgrounds and scrollbar colors for dark theme
- Ensured all table headers (table-light) display with dark backgrounds
- Applied !important declarations to override Bootstrap's default light theme styles