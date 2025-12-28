# Architecture Documentation Index

This directory contains comprehensive architecture documentation for the Terraform + Spacelift AI Reviewer platform.

## Documentation Structure

### Core Architecture Documents

1. **[Platform Architecture](./platform-architecture.md)**
   - Complete system architecture
   - Multi-account strategy
   - Network model
   - Security model
   - Identity integration
   - Compliance mapping
   - Trust boundaries

2. **[Architecture Diagrams](./architecture-diagrams.md)**
   - ASCII diagrams for all components
   - Network flow diagrams
   - Identity and access flows
   - Data flow diagrams
   - Security boundary diagrams
   - Compliance evidence collection

3. **[Trust Boundaries](./trust-boundaries.md)**
   - Trust level definitions
   - Security zones
   - Trust boundary transitions
   - Zero trust principles
   - Threat model
   - Compliance considerations

4. **[Architecture Summary](./architecture-summary.md)**
   - High-level overview
   - Key architectural decisions
   - Component summary
   - Quick reference

### Implementation Guides

5. **[Multi-Account Setup Guide](./multi-account-setup.md)**
   - Step-by-step setup instructions
   - AWS Organizations configuration
   - IAM Identity Center setup
   - Network connectivity
   - Cross-account access
   - Troubleshooting

### Reference Documents

6. **[Example Prompts](../docs/example-prompts.md)**
   - AI prompt templates
   - Example Terraform code
   - Expected responses

7. **[Example Payloads](../docs/example-payloads.md)**
   - API request/response examples
   - Webhook payloads
   - Error responses

8. **[Architecture Overview](../docs/architecture.md)**
   - System components
   - Data flow
   - Scalability
   - Cost optimization

## Quick Navigation

### For Architects
- Start with [Platform Architecture](./platform-architecture.md)
- Review [Architecture Diagrams](./architecture-diagrams.md)
- Understand [Trust Boundaries](./trust-boundaries.md)

### For Engineers
- Follow [Multi-Account Setup Guide](./multi-account-setup.md)
- Reference [Architecture Diagrams](./architecture-diagrams.md)
- Review [Example Payloads](../docs/example-payloads.md)

### For Security Teams
- Review [Trust Boundaries](./trust-boundaries.md)
- Check [Platform Architecture - Security Model](./platform-architecture.md#3-security-model)
- Understand [Compliance Mapping](./platform-architecture.md#5-compliance-mapping)

### For Compliance Teams
- Review [Compliance Mapping](./platform-architecture.md#5-compliance-mapping)
- Check [Evidence Generation Points](./platform-architecture.md#53-evidence-generation-points)
- Understand [Trust Boundaries](./trust-boundaries.md)

## Architecture Highlights

### Multi-Account Strategy
- Management Account (governance)
- Shared Services Account (networking)
- Application Accounts (workloads)

### Network Architecture
- VPC per account
- Private endpoints
- Transit Gateway
- Bedrock via PrivateLink

### Security Model
- IAM boundaries
- Service Control Policies
- Least privilege
- Encryption everywhere

### Identity Integration
- Azure Entra ID → AWS IAM Identity Center
- SAML 2.0 federation
- SCIM provisioning
- Permission sets

### Compliance
- SOC 2 controls
- ISO 27001 clauses
- Automated evidence
- Audit trails

## Diagram Legend

```
┌─────────────┐
│   Component │  = Service/Component
└─────────────┘

    │
    │  = Data Flow
    ▼

┌─────────────┐
│   Boundary  │  = Trust Boundary
└─────────────┘

    ────  = Network Connection
```

## Related Documentation

- [Main README](../README.md) - Project overview
- [Deployment Guide](../DEPLOYMENT.md) - Deployment instructions
- [Quick Start](../QUICKSTART.md) - Quick setup guide

## Updates and Maintenance

This architecture documentation is maintained as part of the project. When making changes:

1. Update relevant architecture documents
2. Update diagrams if components change
3. Update trust boundaries if security model changes
4. Update compliance mapping if controls change
5. Review and update all related documents

## Questions?

For questions about the architecture:
1. Review the relevant documentation
2. Check the troubleshooting sections
3. Consult the team
4. Update documentation with new findings

