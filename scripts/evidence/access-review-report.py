#!/usr/bin/env python3
"""
Access Review Report Generator

Generates monthly access review reports for SOC2 CC6 and ISO 27001 A.9 compliance.
"""

import json
import boto3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import csv

# Configuration
REPORT_DIR = Path("evidence/access-reviews")
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# AWS Clients
iam = boto3.client('iam')
logs = boto3.client('logs')
cognito = boto3.client('cognito-idp')

# Date range for review
REVIEW_END = datetime.utcnow()
REVIEW_START = REVIEW_END - timedelta(days=30)


class AccessReviewGenerator:
    """Generate access review reports"""
    
    def __init__(self, log_group_prefix: str, user_pool_id: str = None):
        self.log_group_prefix = log_group_prefix
        self.user_pool_id = user_pool_id
        self.report = {
            "review_period": {
                "start": REVIEW_START.isoformat(),
                "end": REVIEW_END.isoformat()
            },
            "generated_at": datetime.utcnow().isoformat(),
            "reviewer": "Automated System"
        }
    
    def generate_report(self):
        """Generate complete access review report"""
        print("Generating access review report...")
        
        # IAM Roles Review
        self.review_iam_roles()
        
        # IAM Policies Review
        self.review_iam_policies()
        
        # User Access Review
        if self.user_pool_id:
            self.review_user_access()
        
        # API Access Review
        self.review_api_access()
        
        # Failed Access Attempts
        self.review_failed_access()
        
        # Save report
        self.save_report()
        
        print(f"Access review report saved to {REPORT_DIR}")
    
    def review_iam_roles(self):
        """Review IAM roles"""
        print("  Reviewing IAM roles...")
        
        roles_data = {
            "roles": [],
            "summary": {
                "total_roles": 0,
                "roles_with_policies": 0,
                "last_used": {}
            }
        }
        
        try:
            # List roles with prefix
            response = iam.list_roles(PathPrefix="/terraform-spacelift-ai-reviewer/")
            
            for role in response['Roles']:
                role_name = role['RoleName']
                
                # Get attached policies
                policies_response = iam.list_attached_role_policies(RoleName=role_name)
                inline_policies_response = iam.list_role_policies(RoleName=role_name)
                
                # Get last used (if available)
                try:
                    last_used_response = iam.get_role(RoleName=role_name)
                    last_used = last_used_response['Role'].get('RoleLastUsed', {})
                except:
                    last_used = {}
                
                roles_data["roles"].append({
                    "role_name": role_name,
                    "arn": role['Arn'],
                    "created_date": role['CreateDate'].isoformat(),
                    "attached_policies": [p['PolicyName'] for p in policies_response['AttachedPolicies']],
                    "inline_policies": inline_policies_response['PolicyNames'],
                    "last_used_date": last_used.get('LastUsedDate', 'Never').isoformat() if last_used.get('LastUsedDate') else 'Never',
                    "last_used_region": last_used.get('Region', 'N/A')
                })
                
                roles_data["summary"]["total_roles"] += 1
                if policies_response['AttachedPolicies'] or inline_policies_response['PolicyNames']:
                    roles_data["summary"]["roles_with_policies"] += 1
                
                if last_used.get('LastUsedDate'):
                    date_str = last_used['LastUsedDate'].isoformat()
                    roles_data["summary"]["last_used"][role_name] = date_str
            
            self.report["iam_roles"] = roles_data
            
        except Exception as e:
            self.report["iam_roles"] = {"error": str(e)}
    
    def review_iam_policies(self):
        """Review IAM policies"""
        print("  Reviewing IAM policies...")
        
        policies_data = {
            "policies": [],
            "summary": {
                "total_policies": 0,
                "high_privilege_policies": []
            }
        }
        
        try:
            # List policies
            response = iam.list_policies(Scope='Local', PathPrefix='/terraform-spacelift-ai-reviewer/')
            
            high_privilege_actions = [
                '*', 'iam:*', 'dynamodb:*', 'lambda:*', 'bedrock:*'
            ]
            
            for policy in response['Policies']:
                policy_name = policy['PolicyName']
                
                # Get policy version
                try:
                    policy_version = iam.get_policy_version(
                        PolicyArn=policy['Arn'],
                        VersionId=policy['DefaultVersionId']
                    )
                    
                    # Check for high privilege actions
                    document = policy_version['PolicyVersion']['Document']
                    has_high_privilege = False
                    
                    for statement in document.get('Statement', []):
                        actions = statement.get('Action', [])
                        if isinstance(actions, str):
                            actions = [actions]
                        
                        for action in actions:
                            if any(action.startswith(priv) or action == priv for priv in high_privilege_actions):
                                has_high_privilege = True
                                break
                    
                    policies_data["policies"].append({
                        "policy_name": policy_name,
                        "arn": policy['Arn'],
                        "created_date": policy['CreateDate'].isoformat(),
                        "high_privilege": has_high_privilege
                    })
                    
                    if has_high_privilege:
                        policies_data["summary"]["high_privilege_policies"].append(policy_name)
                    
                    policies_data["summary"]["total_policies"] += 1
                    
                except Exception as e:
                    policies_data["policies"].append({
                        "policy_name": policy_name,
                        "error": str(e)
                    })
            
            self.report["iam_policies"] = policies_data
            
        except Exception as e:
            self.report["iam_policies"] = {"error": str(e)}
    
    def review_user_access(self):
        """Review user access from Cognito"""
        print("  Reviewing user access...")
        
        users_data = {
            "users": [],
            "summary": {
                "total_users": 0,
                "active_users": 0,
                "inactive_users": 0
            }
        }
        
        try:
            # List users in Cognito
            response = cognito.list_users(UserPoolId=self.user_pool_id)
            
            for user in response['Users']:
                username = user['Username']
                status = user.get('UserStatus', 'UNKNOWN')
                enabled = user.get('Enabled', False)
                
                # Get user groups
                try:
                    groups_response = cognito.admin_list_groups_for_user(
                        UserPoolId=self.user_pool_id,
                        Username=username
                    )
                    groups = [g['GroupName'] for g in groups_response['Groups']]
                except:
                    groups = []
                
                users_data["users"].append({
                    "username": username,
                    "status": status,
                    "enabled": enabled,
                    "groups": groups,
                    "created_date": user.get('UserCreateDate', '').isoformat() if user.get('UserCreateDate') else 'Unknown',
                    "last_modified": user.get('UserLastModifiedDate', '').isoformat() if user.get('UserLastModifiedDate') else 'Unknown'
                })
                
                users_data["summary"]["total_users"] += 1
                if enabled and status == 'CONFIRMED':
                    users_data["summary"]["active_users"] += 1
                else:
                    users_data["summary"]["inactive_users"] += 1
            
            self.report["user_access"] = users_data
            
        except Exception as e:
            self.report["user_access"] = {"error": str(e)}
    
    def review_api_access(self):
        """Review API access from logs"""
        print("  Reviewing API access...")
        
        api_access_data = {
            "access_logs": [],
            "summary": {
                "total_requests": 0,
                "unique_users": set(),
                "requests_by_endpoint": {},
                "requests_by_status": {}
            }
        }
        
        try:
            # Get access logs from JWT authorizer
            response = logs.filter_log_events(
                logGroupName=f"{self.log_group_prefix}-jwt-authorizer-prod",
                filterPattern="authorization_granted",
                startTime=int(REVIEW_START.timestamp() * 1000),
                endTime=int(REVIEW_END.timestamp() * 1000),
                limit=1000
            )
            
            for event in response.get('events', []):
                message = event.get('message', '')
                # Parse log message (would need actual log format)
                # This is a simplified version
                api_access_data["summary"]["total_requests"] += 1
            
            # Convert set to list for JSON serialization
            api_access_data["summary"]["unique_users"] = list(api_access_data["summary"]["unique_users"])
            
            self.report["api_access"] = api_access_data
            
        except Exception as e:
            self.report["api_access"] = {"error": str(e)}
    
    def review_failed_access(self):
        """Review failed access attempts"""
        print("  Reviewing failed access attempts...")
        
        failed_access_data = {
            "failed_attempts": [],
            "summary": {
                "total_failures": 0,
                "failure_types": {},
                "security_events": []
            }
        }
        
        try:
            # Get failed authorization logs
            response = logs.filter_log_events(
                logGroupName=f"{self.log_group_prefix}-jwt-authorizer-prod",
                filterPattern="authorization_failed OR authorization_insufficient_permissions",
                startTime=int(REVIEW_START.timestamp() * 1000),
                endTime=int(REVIEW_END.timestamp() * 1000),
                limit=500
            )
            
            for event in response.get('events', []):
                message = event.get('message', '')
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000)
                
                failed_access_data["failed_attempts"].append({
                    "timestamp": timestamp.isoformat(),
                    "message": message
                })
                
                failed_access_data["summary"]["total_failures"] += 1
            
            self.report["failed_access"] = failed_access_data
            
        except Exception as e:
            self.report["failed_access"] = {"error": str(e)}
    
    def save_report(self):
        """Save access review report"""
        filename = f"access-review-{REVIEW_END.strftime('%Y-%m')}.json"
        filepath = REPORT_DIR / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.report, f, indent=2, default=str)
        
        # Also save CSV summary
        csv_filename = f"access-review-{REVIEW_END.strftime('%Y-%m')}-summary.csv"
        csv_filepath = REPORT_DIR / csv_filename
        
        with open(csv_filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Category', 'Metric', 'Value'])
            
            # IAM Roles Summary
            if 'iam_roles' in self.report and 'summary' in self.report['iam_roles']:
                writer.writerow(['IAM Roles', 'Total Roles', self.report['iam_roles']['summary']['total_roles']])
                writer.writerow(['IAM Roles', 'Roles with Policies', self.report['iam_roles']['summary']['roles_with_policies']])
            
            # User Access Summary
            if 'user_access' in self.report and 'summary' in self.report['user_access']:
                writer.writerow(['User Access', 'Total Users', self.report['user_access']['summary']['total_users']])
                writer.writerow(['User Access', 'Active Users', self.report['user_access']['summary']['active_users']])
                writer.writerow(['User Access', 'Inactive Users', self.report['user_access']['summary']['inactive_users']])
            
            # Failed Access Summary
            if 'failed_access' in self.report and 'summary' in self.report['failed_access']:
                writer.writerow(['Failed Access', 'Total Failures', self.report['failed_access']['summary']['total_failures']])
        
        print(f"  Saved: {filename}")
        print(f"  Saved: {csv_filename}")


def main():
    """Main function"""
    import sys
    
    log_group_prefix = sys.argv[1] if len(sys.argv) > 1 else "/aws/lambda/terraform-spacelift-ai-reviewer"
    user_pool_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    generator = AccessReviewGenerator(log_group_prefix, user_pool_id)
    generator.generate_report()


if __name__ == "__main__":
    main()

