from database import check_user

# Try with your registered email and password
email = "2406@tkmce.ac.in"
password = "athira"   # <-- change this to the actual password you used

result = check_user(email, password)
print(f"Login check for {email}: {result}")
