# Knowledge Base: Enterprise Identity and Password Reset Policy

**Category:** Access  
**Tags:** password, reset, access, account lockout, mfa, sso, credentials, identity  
**Applicability:** All employee directory accounts (Active Directory / Okta / Azure AD)

---

## STRICT SECURITY POLICY NOTICE
> **MANDATORY POLICY FOR ALL SUPPORT STAFF AND AUTOMATED AGENTS:**  
> Support representatives and automated triage systems **MUST NEVER** ask the employee to share, speak, email, or enter their password or MFA token in a ticket, chat, or phone conversation.  
> Never send temporary passwords or secrets via unencrypted email or ticket comments. All password resets must proceed through the verified Self-Service Identity Portal.

## Overview
Accounts automatically lock after 5 consecutive failed authentication attempts to protect against brute-force attacks. Lockouts automatically release after 30 minutes, or can be reset immediately by the user.

## Self-Service Password Reset (SSPR)
Employees should be directed to the self-service portal:
1. Navigate to: `https://identity.internal.corp/sspr`
2. Enter your employee email address (`username@example.com`).
3. Complete the secondary authentication challenge using one of your enrolled MFA methods:
   - Push notification on registered Authenticator app (Recommended)
   - FIDO2 / YubiKey hardware key tap
   - SMS backup code (restricted to mobile numbers previously registered with HR)
4. Set a new password meeting the complexity standard:
   - Minimum 14 characters
   - At least 1 uppercase letter, 1 lowercase letter, 1 numeric digit, and 1 approved symbol (`!@#$%^&*`)
   - Cannot match any of your previous 6 passwords

## Account Unlock Without Password Change
If the employee knows their current password and merely triggered an accidental lockout:
1. Go to `https://identity.internal.corp/unlock`
2. Verify identity via MFA challenge.
3. The account will be unlocked instantly without changing the existing password.

## When to Escalate to Identity Operations
If the employee has lost their MFA device, has a broken phone, or has no secondary verification methods configured:
- Route ticket directly to Tier 2 Identity Operations for a live video identity verification call.
- Mark priority as **High** if the user is a designated critical production on-call engineer.
