from email_sender import send_reset_email_smtp

# Replace with your test email
recipient = "2406@tkmce.ac.in"

# A fake token for testing
token = "test-token-123456"

success = send_reset_email_smtp(recipient, token)
print("Email sent successfully!" if success else "Failed to send email.")
