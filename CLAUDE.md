# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository, with emphasis on using subagents and Model Context Protocol (MCP) tools for optimal development workflow.

## Project Overview: Bibbi Parfum Sales Data Analytics Platform

This is a **full-stack data processing and analytics platform** for Bibbi Parfum sales data management with multi-vendor data pipeline integration, AI-powered analytics, and comprehensive reporting capabilities.

## Subagent-Driven Workflow

Before starting any task, Claude should:
1. **Analyze the request** and determine which subagents would be most effective
2. **Create a specialized subagent** using the available agent templates when the task requires domain expertise
3. **Use MCPs** for technical operations and integrations
4. **Coordinate between subagents** for complex multi-domain tasks

### Available Subagents

#### Product Manager Agent (`product-manager`)
**Use for:**
- Feature planning and requirements gathering
- User story creation and acceptance criteria
- Product roadmap planning
- Problem analysis and solution validation

**Workflow:**
```
@product-manager "Analyze the request for [feature/improvement] and create comprehensive product documentation"
```

#### Technical Architect Agent (Create when needed)
**Use for:**
- System design decisions
- Architecture reviews
- Technical debt analysis
- Performance optimization planning

#### DevOps Agent (Create when needed)
**Use for:**
- Deployment strategies
- Infrastructure planning
- CI/CD pipeline improvements
- Environment configuration

## MCP Integration Strategy

### Supabase MCP
**Use for:**
- Database schema modifications
- RLS policy updates
- Query optimization
- Real-time subscription management

**Typical commands:**
```bash
# Schema updates
supabase db diff
supabase db push

# Local development
supabase start
supabase status
```

### Playwright MCP
**Use for:**
- End-to-end testing
- UI automation
- Integration testing
- User flow validation

**Integration points:**
- Frontend component testing
- API endpoint testing
- Full user journey testing

### REF MCP
**Use for:**
- Code refactoring
- Pattern extraction
- Code quality improvements
- Legacy code modernization

### Claude Task Master MCP
**Use for:**
- Complex project coordination
- Multi-step task management
- Progress tracking
- Resource allocation

## Architecture Overview

### Backend Architecture (`backend/`)
- **FastAPI application** with middleware stack for security, rate limiting, caching, and error handling
- **Supabase integration** for database operations and authentication
- **Multi-vendor data pipeline** with vendor detection and normalization
- **AI-powered chat system** using LangChain + OpenAI for natural language database queries
- **Email reporting system** with PDF/CSV/Excel generation
- **Real-time processing status** tracking and webhook support

Key backend modules:
- `app/api/` - REST API endpoints (auth, upload, status, email, dashboard, chat, webhook)
- `app/pipeline/` - Data processing (detector.py, normalizers.py, cleaners.py)
- `app/services/` - Business logic (auth, cleaning, database, email, file, report services)
- `app/middleware/` - Request processing (caching, rate limiting, error handling, security)

### Frontend Architecture (`frontend/src/`)
- **React SPA** with Vite build system
- **Component-based structure** with pages and reusable components
- **Supabase client integration** for authentication and real-time updates
- **Multi-tab interface** for Upload, Status, Email Reports, AI Chat, and Analytics

Key frontend components:
- `pages/Dashboard.jsx` - Main application dashboard with tabbed interface
- `components/Upload.jsx` - File upload with vendor detection
- `components/Chat.jsx` - AI-powered natural language database queries
- `components/EmailReporting.jsx` - Report generation and email delivery
- `components/AnalyticsDashboard.jsx` - External dashboard embedding

### Data Pipeline
The system processes Excel files from multiple vendors (Galilu, Boxnox, Skins SA, CDLC, Continuity, Ukraine, etc.) with:
1. **Vendor detection** via filename and content patterns (`detector.py`)
2. **Data normalization** to standard schema (`normalizers.py`)
3. **Data cleaning** with vendor-specific rules (`cleaners.py`)
4. **Database persistence** in `sellout_entries2` table with user isolation

### AI Chat System
- **LangChain-based SQL agent** with OpenAI GPT-4 integration
- **Conversation memory** with database persistence
- **Security-validated queries** - only SELECT operations allowed
- **User-specific data filtering** based on authentication
- **Supabase REST API fallback** when direct PostgreSQL connection unavailable

### Phase 1: Analysis & Planning
1. **Initial Assessment**
   - Analyze the request complexity and scope
   - Identify required expertise domains
   - Determine appropriate subagents and MCPs

2. **Subagent Coordination**
   - Create product manager documentation if feature-related
   - Generate technical architecture plans if system changes needed
   - Create specialized agents for domain-specific tasks

3. **MCP Preparation**
   - Initialize required MCP connections
   - Validate environment setup
   - Prepare testing infrastructure

4. **Comprehensive Planning**
   - Create detailed plan in `tasks/todo.md`
   - Include subagent responsibilities
   - Map MCP usage points
   - Define success criteria

### Phase 2: Validation & Approval
5. **Plan Review**
   - Present complete plan including subagent roles
   - Highlight MCP integration points
   - Request approval before execution

### Phase 3: Execution
6. **Coordinated Development**
   - Execute tasks using appropriate subagents
   - Leverage MCPs for technical operations
   - Maintain communication between agents
   - Provide high-level progress updates

7. **Quality Assurance**
   - Use Playwright MCP for testing
   - Apply REF MCP for code quality
   - Validate with Supabase MCP for database changes

### Phase 4: Documentation & Review
8. **Comprehensive Documentation**
   - Update all relevant documentation
   - Include subagent outputs
   - Document MCP integration points

9. **Final Review**
   - Add review section to todo.md
   - Include subagent coordination summary
   - Document lessons learned

## Subagent Decision Matrix

| Task Type | Primary Subagent | Supporting Agents | Key MCPs |
|-----------|------------------|-------------------|----------|
| New Feature | Product Manager | Technical Architect | Supabase, Playwright |
| Bug Fix | Technical Lead | QA Engineer | REF, Playwright |
| Refactoring | Technical Lead | Code Review Agent | REF, Supabase |
| UI/UX Changes | Frontend Specialist | Product Manager | Playwright |
| Database Changes | Data Engineer | Technical Architect | Supabase |
| API Development | Backend Engineer | Technical Architect | Supabase, Playwright |

## MCP Usage Patterns

### For Database Operations
```bash
# Always use Supabase MCP for:
- Schema migrations
- RLS policy updates
- Query performance analysis
- Real-time subscription management
```

### For Testing
```bash
# Use Playwright MCP for:
- Component testing
- Integration testing
- User flow validation
- Cross-browser compatibility
```

### For Code Quality
```bash
# Use REF MCP for:
- Refactoring legacy code
- Extracting common patterns
- Improving code maintainability
- Technical debt reduction
```

### For Complex Coordination
```bash
# Use Claude Task Master MCP for:
- Multi-phase projects
- Cross-team coordination
- Resource planning
- Progress tracking
```

## Development Commands (Enhanced)

### Backend (Python/FastAPI) with MCP Support
```bash
# Setup with Supabase MCP integration
cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
supabase start  # Using Supabase MCP

# Run development server with testing ready
cd backend && ./run.sh
# Parallel: Initialize Playwright for testing
playwright install

# Run tests with MCP support
cd backend && python run_tests.py
playwright test  # Using Playwright MCP
```

### Frontend (React/Vite) with MCP Support
```bash
# Setup with testing infrastructure
cd frontend && npm install
playwright install  # Prepare for E2E testing

# Development with hot reload
cd frontend && npm run dev

# Build and test
cd frontend && npm run build
playwright test --headed  # Visual testing
```

## Architecture-Aware Development

### When to Create Specialized Subagents

#### Database Schema Agent
**Create when:**
- Major schema changes required
- Complex migration planning needed
- Performance optimization required

#### Security Agent
**Create when:**
- Authentication changes needed
- RLS policy updates required
- Security vulnerability assessment needed

#### Integration Agent
**Create when:**
- Third-party API integration
- External service coordination
- Webhook implementation

#### Performance Agent
**Create when:**
- Performance bottlenecks identified
- Scaling considerations
- Optimization requirements

## Quality Gates with MCP Integration

### Pre-Development
- [ ] Supabase MCP: Validate database connectivity
- [ ] Playwright MCP: Ensure test environment ready
- [ ] REF MCP: Assess current code quality baseline

### During Development
- [ ] Use appropriate subagents for domain expertise
- [ ] Leverage MCPs for technical operations
- [ ] Maintain continuous testing with Playwright MCP
- [ ] Apply code quality checks with REF MCP

### Pre-Deployment
- [ ] Supabase MCP: Validate all migrations
- [ ] Playwright MCP: Full E2E test suite
- [ ] REF MCP: Final code quality assessment
- [ ] Task Master MCP: Coordinate deployment steps

## Best Practices

### Subagent Coordination
1. **Clear Handoffs**: Ensure clean transitions between agents
2. **Shared Context**: Maintain context across agent interactions
3. **Validation Points**: Verify outputs between agent handoffs
4. **Documentation**: Keep comprehensive records of agent decisions

### MCP Integration
1. **Connection Management**: Establish MCP connections early
2. **Error Handling**: Implement robust MCP error recovery
3. **Performance**: Monitor MCP operation performance
4. **Security**: Ensure MCP operations follow security protocols

### Code Quality with Simplicity
1. **Minimal Changes**: Every modification should impact minimal code
2. **Single Responsibility**: Each change should address one concern
3. **MCP Validation**: Use REF MCP to ensure changes maintain quality
4. **Testing First**: Use Playwright MCP for test-driven development

## Emergency Protocols

### When Subagents Conflict
1. Escalate to Claude Task Master MCP
2. Create arbitration agent if needed
3. Document resolution for future reference

### When MCPs Fail
1. Fall back to manual operations
2. Document MCP issues
3. Implement temporary workarounds
4. Report to appropriate MCP maintainers

## Success Metrics

Track the effectiveness of subagent and MCP usage:
- Time to completion
- Code quality improvements
- Test coverage increases
- Documentation completeness
- Stakeholder satisfaction

## Testing & Quality Assurance

- Backend tests located in `backend/tests/`
- Run backend tests: `cd backend && python run_tests.py`
- Main test coverage: AI chat system, data pipeline, authentication
- Archive of old tests in `backend/archive_old_tests/`
- Use Playwright MCP for comprehensive E2E testing
- Use REF MCP for code quality improvements

## File Structure Notes

- `uploads/` directory contains user-uploaded Excel files
- `logs/` directory for application logging
- `database/` contains SQL schemas and migrations
- `Instruction_templates/` contains AI prompts and reseller profiles
- `csv/` contains sample data files
- `tasks/` contains project management files (todo.md, etc.)

## Important Implementation Details

- **Asynchronous processing** with Celery background tasks
- **Real-time updates** via Supabase subscriptions
- **Conversation memory** for AI chat with database persistence
- **Vendor detection** uses both filename patterns and sheet content analysis
- **Data normalization** converts all vendor formats to unified schema
- **Email attachments** generated dynamically (PDF/CSV/Excel formats)
- **External dashboard embedding** with authentication handling
- **Comprehensive logging** with structured JSON format option
- **Error handling** with detailed error tracking and user-friendly messages

---

> **Remember**: You are orchestrating a team of specialized agents and powerful tools. Your value is in coordination, quality assurance, and maintaining the big picture while leveraging domain expertise and technical capabilities effectively.