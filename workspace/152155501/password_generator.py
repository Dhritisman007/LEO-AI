import password_generator

pwd = password_generator.generate_secure_password()
print(f"Generated Password: {pwd}")
print(f"Length: {len(pwd)}")